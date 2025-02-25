from typing import Optional
from web3.contract import Contract
import logging

from evm.base_activity import BaseActivity
from evm.client import EVMClient
from evm.models.registry.tokens import MonadTokens
from evm.models.registry.protocols import MonadProtocols
from evm.models.token import TokenAmount
from evm.utils.token_utils import approve_token_if_needed
from utils.tasks.base import Base
from loguru import logger


class AmbientMonad(BaseActivity):
    def __init__(self, client: EVMClient):
        super().__init__(client)
        self.protocol = MonadProtocols.AMBIENT
        self.mon = MonadTokens.MON
        self.wbtc = MonadTokens.WBTC
        self.usdc = MonadTokens.USDC
        self.contract = self.protocol.get_contract(self.client.web3)


    async def swap_mon_to_wbtc(
        self,
        amount: float = None,
    ) -> str:
        if not amount:
             amount = Base.get_eth_amount_for_swap('ambient')
             
        if isinstance(amount, (float, int)):
             amount = TokenAmount.from_ether(amount)
             
        amount_in_wei = amount.Wei

        min_amount_out = "000000000000000000000000000000000ffff5433e2b3d8211706e6102aa9471"

        cmd = (
            "0" * 64 +                                    # [3] zeros 
            self.wbtc.address[2:].lower().zfill(64) +    # [4] WBTC token address
            "8ca0".zfill(64) +                           # [5] pool index
            "1".zfill(64) +                              # [6] is_buy
            "1".zfill(64) +                              # [7] in_base_qty
            hex(amount_in_wei)[2:].zfill(64) +           # [8] qty
            "0".zfill(64) +                              # [9] tip
            min_amount_out +                             # [10] min_out
            "3".zfill(64) +                              # [11] reserve_flags
            "0".zfill(64)                                # [12] trailing zero
        )

        data = self.contract.encodeABI(
            fn_name="userCmd",
            args=[
                1,
                bytes.fromhex(cmd)
            ]
        )

        tx = await self.client.build_transaction(
            to=self.protocol.address,
            value=amount_in_wei,
            data=data
        )
        return await self.client.send_transaction(tx)

        
    async def swap_wbtc_to_mon(self) -> str:
        try:
            balance = await self.client.get_balance(self.wbtc.address, self.wbtc.decimals)
            
            logger.info(f"Попытка свапа всего баланса WBTC: {balance.Wei}")
            
            await approve_token_if_needed(
                client=self.client,
                token_address=self.wbtc.address,
                spender=self.protocol.address,
                amount_wei=balance.Wei
            )
            
            cmd = (
                "0" * 64 +                                    # [3] zeros 
                self.wbtc.address[2:].lower().zfill(64) +    # [4] WBTC token address
                "8ca0".zfill(64) +                           # [5] pool index
                "0".zfill(64) +                              # [6] is_buy = 0
                "0".zfill(64) +                              # [7] in_base_qty = 0
                hex(balance.Wei)[2:].zfill(64) +             # [8] qty = весь баланс
                "0".zfill(64) +                              # [9] tip
                "10001".zfill(64) +                          # [10] min_out
                "0020c9a34d999e88".zfill(64) +               # [11] reserve_flags
                "0".zfill(64)                                # [12] trailing zero
            )

            data = self.contract.encodeABI(
                fn_name="userCmd",
                args=[
                    1,
                    bytes.fromhex(cmd)
                ]
            )

            tx = await self.client.build_transaction(
                to=self.protocol.address,
                value=0,
                data=data
            )
            
            logger.info("Отправка транзакции WBTC -> MON (весь баланс)...")
            tx_hash = await self.client.send_transaction(tx)
            logger.info(f"Транзакция отправлена: {tx_hash}")
            
            return tx_hash
                
        except Exception as e:
            logger.error(f"Ошибка при выполнении swap_wbtc_to_mon_full_balance: {str(e)}")
            raise e
        
        
    async def swap_mon_to_usdc(
        self,
        amount: float = None,
    ) -> str:
        try:
            if not amount:
                amount = Base.get_eth_amount_for_swap('ambient')
                
            if isinstance(amount, (float, int)):
                amount = TokenAmount.from_ether(amount)
                
            amount_in_wei = amount.Wei
            
            logger.info(f"Свап MON -> USDC, сумма: {amount}, Wei: {amount_in_wei}")

            min_amount_out = "000000000000000000000000000000000ffff5433e2b3d8211706e6102aa9471"
            
            cmd = (
                "0" * 64 +                                    # [3] zeros 
                self.usdc.address[2:].lower().zfill(64) +    # [4] USDC token address
                "8ca0".zfill(64) +                           # [5] pool index
                "1".zfill(64) +                              # [6] is_buy
                "1".zfill(64) +                              # [7] in_base_qty
                hex(amount_in_wei)[2:].zfill(64) +           # [8] qty
                "0".zfill(64) +                              # [9] tip
                min_amount_out +                             # [10] min_out
                "c644".zfill(64) +                           # [11] reserve_flags
                "0".zfill(64)                                # [12] trailing zero
            )

            data = self.contract.encodeABI(
                fn_name="userCmd",
                args=[
                    1, 
                    bytes.fromhex(cmd)  
                ]
            )

            tx = await self.client.build_transaction(
                to=self.protocol.address,
                value=amount_in_wei,
                data=data
            )
            
            logger.info("Отправка транзакции MON -> USDC...")
            tx_hash = await self.client.send_transaction(tx)
            logger.info(f"Транзакция отправлена: {tx_hash}")
            
            return tx_hash
        
        except Exception as e:
            logger.error(f"Ошибка при выполнении swap_mon_to_usdc: {str(e)}")
            raise e
            
    async def swap_usdc_to_mon(self) -> str:
        try:
            balance = await self.client.get_balance(self.usdc.address, self.usdc.decimals)
            
            
            logger.info(f"Свап USDC -> MON, количество: {balance.Wei})")
            
            await approve_token_if_needed(
                client=self.client,
                token_address=self.usdc.address,
                spender=self.protocol.address,
                amount_wei=balance.Wei
            )

            cmd = (
                "0" * 64 +                                    # [3] zeros 
                self.usdc.address[2:].lower().zfill(64) +    # [4] USDC token address
                "8ca0".zfill(64) +                           # [5] pool index
                "0".zfill(64) +                              # [6] is_buy = 0
                "0".zfill(64) +                              # [7] in_base_qty = 0
                hex(balance.Wei)[2:].zfill(64) +               # [8] qty = 0xc845
                "0".zfill(64) +                              # [9] tip
                "10001".zfill(64) +                          # [10] min_out
                "00230f19f1dbdcd3".zfill(64) +               # [11] reserve_flags
                "0".zfill(64)                                # [12] trailing zero
            )

            data = self.contract.encodeABI(
                fn_name="userCmd",
                args=[
                    1,
                    bytes.fromhex(cmd)  
                ]
            )

            tx = await self.client.build_transaction(
                to=self.protocol.address,
                value=0,
                data=data
            )
            
            logger.info("Отправка транзакции USDC -> MON...")
            tx_hash = await self.client.send_transaction(tx)
            logger.info(f"Транзакция отправлена: {tx_hash}")
            
            return tx_hash
                
        except Exception as e:
            logger.error(f"Ошибка при выполнении swap_usdc_to_mon: {str(e)}")
            raise e
        