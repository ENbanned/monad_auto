import asyncio
from typing import Optional
from web3.contract import Contract

from evm.base_activity import BaseActivity
from evm.models.token import TokenAmount
from evm.client import EVMClient
from evm.utils.token_utils import approve_token_if_needed, get_token_balance
from evm.models.registry.tokens import MonadTokens
from utils.tasks.base import Base



class UniswapMonad(BaseActivity, Base):
    def __init__(self, client: EVMClient):
        super().__init__(client)
        self.router_address = self.client.web3.to_checksum_address(
            "0x3aE6D8A282D67893e17AA70ebFFb33EE5aa65893"
        )
        
        # Используем предопределенные токены
        self.mon = MonadTokens.MON
        self.wmon = MonadTokens.WMON
        self.usdt = MonadTokens.USDT
        
        # Инициализируем контракт WMON
        self._wmon_contract = self.client.web3.eth.contract(
            address=self.wmon.address,
            abi=self.wmon.abi
        )

    async def wrap(self, amount: float = None) -> str:
        """
        Wrap MON -> WMON
        :param amount: количество MON для wrap
        """
        if amount is None:
            amount = Base.get_mon_amount_for_stake()
            
        amount_wei = amount.Wei if isinstance(amount, TokenAmount) else self.mon.amount_to_wei(amount)
        
        tx = await self.client.build_transaction(
            to=self.wmon.address,
            value=amount_wei,
            data=self._wmon_contract.encodeABI(fn_name="deposit")
        )
        return await self.client.send_transaction(tx)

    async def unwrap(self, amount: float) -> str:
        """
        Unwrap WMON -> MON
        :param amount: количество WMON для unwrap
        """
        amount_wei = self.wmon.amount_to_wei(amount)
        
        tx = await self.client.build_transaction(
            to=self.wmon.address,
            value=0,
            data=self._wmon_contract.encodeABI(fn_name="withdraw", args=[amount_wei])
        )
        return await self.client.send_transaction(tx)

    async def _get_deadline(self, plus_seconds: int = 1200) -> int:
        """Возвращает текущий time + plus_seconds (по умолчанию +20 минут)."""
        latest_block = await self.client.web3.eth.get_block("latest")
        return latest_block["timestamp"] + plus_seconds

    def _prepare_swap_data_mon_to_usdt(
        self, amount_in: int, deadline: int, to_address: str
    ) -> bytes:
        addr_hex = to_address.lower().replace("0x", "")
        wmon_addr = self.wmon.address.lower().replace("0x", "")
        usdt_addr = self.usdt.address.lower().replace("0x", "")
        
        params = []
        prefix = "3593564c"

        params.append("0000000000000000000000000000000000000000000000000000000000000060")
        params.append("00000000000000000000000000000000000000000000000000000000000000a0")
        params.append(f"{deadline:064x}")  # deadline
        params.append("0000000000000000000000000000000000000000000000000000000000000002")
        params.append("0b08000000000000000000000000000000000000000000000000000000000000")
        params.append("0000000000000000000000000000000000000000000000000000000000000002")
        params.append("0000000000000000000000000000000000000000000000000000000000000040")
        params.append("00000000000000000000000000000000000000000000000000000000000000a0")
        params.append("0000000000000000000000000000000000000000000000000000000000000040")
        params.append("0000000000000000000000000000000000000000000000000000000000000002")
        params.append(f"{amount_in:064x}")  # amount_in
        params.append("0000000000000000000000000000000000000000000000000000000000000100")
        params.append(addr_hex.zfill(64))  # адрес
        params.append(f"{amount_in:064x}")  # amount_in повторно
        params.append("0000000000000000000000000000000000000000000000000000000000000002")
        params.append("00000000000000000000000000000000000000000000000000000000000000a0")
        params.append("0000000000000000000000000000000000000000000000000000000000000000")
        params.append("0000000000000000000000000000000000000000000000000000000000000002")
        params.append(wmon_addr.zfill(64))  # адрес токена WMON
        params.append(usdt_addr.zfill(64))  # адрес токена USDT
        params.append("0000000000000000000000000000000000000000000000000000000000000040")
        params.append(addr_hex.zfill(64))
        params.append("0c")

        data_hex = prefix + "".join(params)
        return bytes.fromhex(data_hex)

    def _prepare_swap_data_usdt_to_mon(
        self,
        amount_in: int,
        min_amount_out: int,
        deadline: int,
    ) -> bytes:
        prefix = "3593564c"

        words = [
            "0000000000000000000000000000000000000000000000000000000000000060",
            "00000000000000000000000000000000000000000000000000000000000000a0",
            f"{deadline:064x}",
            "0000000000000000000000000000000000000000000000000000000000000002",
            "080c000000000000000000000000000000000000000000000000000000000000",
            "0000000000000000000000000000000000000000000000000000000000000002",
            "0000000000000000000000000000000000000000000000000000000000000040",
            "0000000000000000000000000000000000000000000000000000000000000160",
            "0000000000000000000000000000000000000000000000000000000000000100",
            "0000000000000000000000000000000000000000000000000000000000000002",
            f"{amount_in:064x}",
            "0000000000000000000000000000000000000000000000000000000000000000",
            "00000000000000000000000000000000000000000000000000000000000000a0",
            "0000000000000000000000000000000000000000000000000000000000000001",
            "0000000000000000000000000000000000000000000000000000000000000002",
            self.usdt.address.lower().replace("0x", "").zfill(64),
            self.wmon.address.lower().replace("0x", "").zfill(64),
            "0000000000000000000000000000000000000000000000000000000000000040",
            self.client.account.address.lower().replace("0x", "").zfill(64),
            f"{min_amount_out:064x}",
        ]

        data_hex = prefix + "".join(words) + "0c"

        return bytes.fromhex(data_hex)


    async def swap_mon_to_usdt(
        self,
        amount: Optional[float] = None,
        all_balance: bool = False,
        slippage: float = 0.01
    ) -> str:
        if not amount:
            amount = Base.get_eth_amount_for_swap('uniswap')
            
        if isinstance(amount, (float, int)):
            amount = TokenAmount.from_ether(amount)
            
        if all_balance:
            balance = await self.client.web3.eth.get_balance(self.client.account.address)
            amount = TokenAmount.from_wei(int(balance * (1 - slippage)))
            
        amount_in_wei = amount.Wei
        
        if amount.Ether < Base.MIN_SWAP_AMOUNTS['uniswap']:
            return f"Failed: Amount too small (min: {Base.MIN_SWAP_AMOUNTS['uniswap']} MON)"
            
        min_amount_out = int(amount_in_wei * (1 - slippage))

        deadline = await self._get_deadline(plus_seconds=1200)
        
        data = self._prepare_swap_data_mon_to_usdt(
            amount_in=amount_in_wei,
            deadline=deadline,
            to_address=self.client.account.address,
        )

        tx_params = await self.client.build_transaction(
            to=self.router_address,
            value=amount_in_wei,
            data=data,
        )
        tx_hash = await self.client.send_transaction(tx_params)
        
        return tx_hash


    async def swap_usdt_to_mon(
        self,
        amount: Optional[float] = None,
        all_balance: bool = False,
        slippage: float = 0.01
    ) -> str:
        if amount is None:
            amount = await self.client.get_balance(self.usdt.address, self.usdt.decimals)
        elif isinstance(amount, (float, int)):
            amount = TokenAmount.from_ether(amount, decimals=self.usdt.decimals)
            
        if all_balance:
            amount = await self.client.get_balance(self.usdt.address, self.usdt.decimals)
            
        amount_in_wei = amount.Wei

        min_amount_out = int(amount_in_wei * (1 - slippage))

        await approve_token_if_needed(
            client=self.client,
            token_address=self.usdt.address,
            spender=self.router_address,
            amount_wei=amount_in_wei
        )

        deadline = await self._get_deadline(plus_seconds=1200)
        data = self._prepare_swap_data_usdt_to_mon(
            amount_in=amount_in_wei,
            min_amount_out=min_amount_out,
            deadline=deadline,
            to_address=self.client.account.address
        )

        try:
            tx_params = await self.client.build_transaction(
                to=self.router_address,
                value=0,
                data=data
            )
            tx_hash = await self.client.send_transaction(tx_params)
            return tx_hash
        
        except Exception as exc:
            raise exc