from typing import Optional

from evm.base_activity import BaseActivity
from evm.client import EVMClient
from evm.models.registry.tokens import MonadTokens
from evm.models.registry.protocols import MonadProtocols
from evm.models.token import TokenAmount
from evm.utils.token_utils import approve_token_if_needed
from utils.tasks.base import Base

class BeanExchange(BaseActivity, Base):
    def __init__(self, client: EVMClient):
        super().__init__(client)
        
        self.mon = MonadTokens.MON
        self.bean = MonadTokens.BEAN
        self.wmon = MonadTokens.WMON
        self.jai = MonadTokens.JAI
        self.usdc = MonadTokens.USDC

        self.protocol = MonadProtocols.BEAN_EXCHANGE
        self.router_address = self.protocol.address

        self.abi_swap_exact_eth_for_tokens = [
            {
                "name": "swapExactETHForTokens",
                "type": "function",
                "inputs": [
                    {"name": "amountOutMin", "type": "uint256"},
                    {"name": "path", "type": "address[]"},
                    {"name": "to", "type": "address"},
                    {"name": "deadline", "type": "uint256"}
                ],
                "outputs": [],
                "stateMutability": "payable"
            }
        ]
        self.abi_swap_exact_tokens_for_eth = [
            {
                "name": "swapExactTokensForETH",
                "type": "function",
                "inputs": [
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMin", "type": "uint256"},
                    {"name": "path", "type": "address[]"},
                    {"name": "to", "type": "address"},
                    {"name": "deadline", "type": "uint256"}
                ],
                "outputs": [],
                "stateMutability": "nonpayable"
            }
        ]
        self.abi_swap_exact_tokens_for_tokens = [
            {
                "name": "swapExactTokensForTokens",
                "type": "function",
                "inputs": [
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMin", "type": "uint256"},
                    {"name": "path", "type": "address[]"},
                    {"name": "to", "type": "address"},
                    {"name": "deadline", "type": "uint256"}
                ],
                "outputs": [],
                "stateMutability": "nonpayable"
            }
        ]
        self.abi_get_amounts_out = [{
            "name": "getAmountsOut",
            "type": "function",
            "inputs": [
                {"name": "amountIn", "type": "uint256"},
                {"name": "path", "type": "address[]"}
            ],
            "outputs": [
                {"name": "amounts", "type": "uint256[]"}
            ],
            "stateMutability": "view"
        }]


    async def _get_deadline(self, plus_seconds: int = 1200) -> int:
        latest_block = await self.client.web3.eth.get_block("latest")
        return latest_block["timestamp"] + plus_seconds


    async def swap_mon_to_bean(
        self,
        amount: Optional[float] = None,
        all_balance: bool = False,
        slippage: float = 0.01
    ) -> str:
        
        if amount is None:
           amount = Base.get_eth_amount_for_swap('bean')
        
        if isinstance(amount, (float, int)):
            amount = TokenAmount.from_ether(amount)
            
        if all_balance:
            balance = await self.client.web3.eth.get_balance(self.client.account.address)
            amount = TokenAmount.from_wei(int(balance * (1 - slippage)))
        
        amount_in_wei = amount.Wei
        if amount.Ether < Base.MIN_SWAP_AMOUNTS['bean']:
            return f"Failed: Amount too small (min: {Base.MIN_SWAP_AMOUNTS['bean']} MON)"
            
        min_amount_out = int(amount_in_wei * (1 - slippage))    
                
        deadline = await self._get_deadline()
        contract = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_swap_exact_eth_for_tokens
        )
        
        data = contract.encodeABI(
            fn_name="swapExactETHForTokens",
            args=[
                min_amount_out,
                [self.wmon.address, self.bean.address],
                self.client.account.address,
                deadline
            ]
        )
        
        tx_params = await self.client.build_transaction(
            to=self.router_address,
            value=amount_in_wei,
            data=data,
        )
        
        tx_hash = await self.client.send_transaction(tx_params)
        return tx_hash


    async def swap_bean_to_mon(
        self,
        amount: Optional[float] = None,
        all_balance: bool = False,
        slippage: float = 0.01
    ) -> str:
        
        if amount is None:
            amount = await self.client.get_balance(self.bean.address, self.bean.decimals)
        elif isinstance(amount, (float, int)):
            amount = TokenAmount.from_ether(amount, decimals=self.bean.decimals)
            
        if all_balance:
            amount = await self.client.get_balance(self.bean.address, self.bean.decimals)
            
        amount_in_wei = amount.Wei
            
        await approve_token_if_needed(
            client=self.client,
            token_address=self.bean.address,
            spender=self.router_address,
            amount_wei=amount_in_wei
        )
        
        router = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_get_amounts_out
        )
        
        amounts = await router.functions.getAmountsOut(
            amount_in_wei, [self.bean.address, self.wmon.address]
        ).call()
        
        expected_out = amounts[-1]
        min_amount_out = int(expected_out * (1 - slippage))
        deadline = await self._get_deadline()
        
        contract = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_swap_exact_tokens_for_eth
        )
        
        data = contract.encodeABI(
            fn_name="swapExactTokensForETH",
            args=[
                amount_in_wei,
                min_amount_out,
                [self.bean.address, self.wmon.address],
                self.client.account.address,
                deadline
            ]
        )
        
        tx_params = await self.client.build_transaction(
            to=self.router_address,
            value=0,
            data=data,
        )
        
        tx_hash = await self.client.send_transaction(tx_params)
        return tx_hash


    async def swap_jai_to_mon(
        self,
        amount: Optional[float] = None,
        all_balance: bool = False,
        slippage: float = 0.01
    ) -> str:
        if amount is None:
            amount = await self.client.get_balance(self.jai.address, self.jai.decimals)
        elif isinstance(amount, (float, int)):
            amount = TokenAmount.from_ether(amount, decimals=self.jai.decimals)
            
        if all_balance:
            amount = await self.client.get_balance(self.jai.address, self.jai.decimals)
            
        amount_in_wei = amount.Wei
            
        await approve_token_if_needed(
            client=self.client,
            token_address=self.jai.address,
            spender=self.router_address,
            amount_wei=amount_in_wei
        )
        
        router = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_get_amounts_out
        )
        
        amounts = await router.functions.getAmountsOut(
            amount_in_wei, [self.jai.address, self.wmon.address]
        ).call()
        
        expected_out = amounts[-1]
        min_amount_out = int(expected_out * (1 - slippage))
        deadline = await self._get_deadline()
        
        contract = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_swap_exact_tokens_for_eth
        )
        
        data = contract.encodeABI(
            fn_name="swapExactTokensForETH",
            args=[
                amount_in_wei,
                min_amount_out,
                [self.jai.address, self.wmon.address],
                self.client.account.address,
                deadline
            ]
        )
        
        tx_params = await self.client.build_transaction(
            to=self.router_address,
            value=0,
            data=data,
        )
        
        tx_hash = await self.client.send_transaction(tx_params)
        return tx_hash
    
    
    async def swap_usdc_to_mon(
        self,
        amount: Optional[float] = None,
        all_balance: bool = False,
        slippage: float = 0.01
    ) -> str:
        if amount is None:
            amount = await self.client.get_balance(self.usdc.address, self.usdc.decimals)
        elif isinstance(amount, (float, int)):
            amount = TokenAmount.from_ether(amount, decimals=self.usdc.decimals)
            
        if all_balance:
            amount = await self.client.get_balance(self.usdc.address, self.usdc.decimals)
            
        amount_in_wei = amount.Wei
            
        await approve_token_if_needed(
            client=self.client,
            token_address=self.usdc.address,
            spender=self.router_address,
            amount_wei=amount_in_wei
        )
        
        router = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_get_amounts_out
        )
        
        amounts = await router.functions.getAmountsOut(
            amount_in_wei, [self.usdc.address, self.wmon.address]
        ).call()
        
        expected_out = amounts[-1]
        min_amount_out = int(expected_out * (1 - slippage))
        deadline = await self._get_deadline()
        
        contract = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_swap_exact_tokens_for_eth
        )
        
        data = contract.encodeABI(
            fn_name="swapExactTokensForETH",
            args=[
                amount_in_wei,
                min_amount_out,
                [self.usdc.address, self.wmon.address],
                self.client.account.address,
                deadline
            ]
        )
        
        tx_params = await self.client.build_transaction(
            to=self.router_address,
            value=0,
            data=data,
        )
        
        tx_hash = await self.client.send_transaction(tx_params)
        return tx_hash
    
    
    async def swap_bean_to_jai(
        self,
        amount: Optional[float] = None,
        all_balance: bool = False,
        slippage: float = 0.01
    ) -> str:
        if amount is None:
            amount = await self.client.get_balance(self.bean.address, self.bean.decimals)
        elif isinstance(amount, (float, int)):
            amount = TokenAmount.from_ether(amount, decimals=self.bean.decimals)
            
        if all_balance:
            amount = await self.client.get_balance(self.bean.address, self.bean.decimals)
            
        amount_in_wei = amount.Wei
            
        await approve_token_if_needed(
            client=self.client,
            token_address=self.bean.address,
            spender=self.router_address,
            amount_wei=amount_in_wei
        )
        
        router = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_get_amounts_out
        )
        
        amounts = await router.functions.getAmountsOut(
            amount_in_wei, [self.bean.address, self.jai.address]
        ).call()
        
        expected_out = amounts[-1]
        min_amount_out = int(expected_out * (1 - slippage))
        deadline = await self._get_deadline()
        
        contract = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_swap_exact_tokens_for_tokens
        )
        
        data = contract.encodeABI(
            fn_name="swapExactTokensForTokens",
            args=[
                amount_in_wei,
                min_amount_out,
                [self.bean.address, self.jai.address],
                self.client.account.address,
                deadline
            ]
        )
        
        tx_params = await self.client.build_transaction(
            to=self.router_address,
            value=0,
            data=data,
        )
        
        tx_hash = await self.client.send_transaction(tx_params)
        return tx_hash


    async def swap_jai_to_bean(
        self,
        amount: Optional[float] = None,
        all_balance: bool = False,
        slippage: float = 0.01
    ) -> str:
        if amount is None:
            amount = await self.client.get_balance(self.jai.address, self.jai.decimals)
        elif isinstance(amount, (float, int)):
            amount = TokenAmount.from_ether(amount, decimals=self.jai.decimals)
            
        if all_balance:
            amount = await self.client.get_balance(self.jai.address, self.jai.decimals)
            
        amount_in_wei = amount.Wei
            
        await approve_token_if_needed(
            client=self.client,
            token_address=self.jai.address,
            spender=self.router_address,
            amount_wei=amount_in_wei
        )
        
        router = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_get_amounts_out
        )
        
        amounts = await router.functions.getAmountsOut(
            amount_in_wei, [self.jai.address, self.bean.address]
        ).call()
        
        expected_out = amounts[-1]
        min_amount_out = int(expected_out * (1 - slippage))
        deadline = await self._get_deadline()
        contract = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_swap_exact_tokens_for_tokens
        )
        
        data = contract.encodeABI(
            fn_name="swapExactTokensForTokens",
            args=[
                amount_in_wei,
                min_amount_out,
                [self.jai.address, self.bean.address],
                self.client.account.address,
                deadline
            ]
        )
        
        tx_params = await self.client.build_transaction(
            to=self.router_address,
            value=0,
            data=data,
        )
        
        tx_hash = await self.client.send_transaction(tx_params)
        return tx_hash


    async def swap_usdc_to_bean(
        self,
        amount: Optional[float] = None,
        all_balance: bool = False,
        slippage: float = 0.01
    ) -> str:
        if amount is None:
            amount = await self.client.get_balance(self.usdc.address, self.usdc.decimals)
        elif isinstance(amount, (float, int)):
            amount = TokenAmount.from_ether(amount, decimals=self.usdc.decimals)
            
        if all_balance:
            amount = await self.client.get_balance(self.usdc.address, self.usdc.decimals)
            
        amount_in_wei = amount.Wei
            
        await approve_token_if_needed(
            client=self.client,
            token_address=self.usdc.address,
            spender=self.router_address,
            amount_wei=amount_in_wei
        )
        router = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_get_amounts_out
        )
        amounts = await router.functions.getAmountsOut(
            amount_in_wei, [self.usdc.address, self.bean.address]
        ).call()
        expected_out = amounts[-1]
        min_amount_out = int(expected_out * (1 - slippage))
        deadline = await self._get_deadline()
        contract = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_swap_exact_tokens_for_tokens
        )
        data = contract.encodeABI(
            fn_name="swapExactTokensForTokens",
            args=[
                amount_in_wei,
                min_amount_out,
                [self.usdc.address, self.bean.address],
                self.client.account.address,
                deadline
            ]
        )
        tx_params = await self.client.build_transaction(
            to=self.router_address,
            value=0,
            data=data,
        )
        
        tx_hash = await self.client.send_transaction(tx_params)
        return tx_hash


    async def swap_jai_to_usdc(
        self,
        amount: Optional[float] = None,
        all_balance: bool = False,
        slippage: float = 0.01
    ) -> str:
        if amount is None:
            amount = await self.client.get_balance(self.jai.address, self.jai.decimals)
        elif isinstance(amount, (float, int)):
            amount = TokenAmount.from_ether(amount, decimals=self.jai.decimals)
            
        if all_balance:
            amount = await self.client.get_balance(self.jai.address, self.jai.decimals)
            
        amount_in_wei = amount.Wei
            
        await approve_token_if_needed(
            client=self.client,
            token_address=self.jai.address,
            spender=self.router_address,
            amount_wei=amount_in_wei
        )
        router = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_get_amounts_out
        )
        amounts = await router.functions.getAmountsOut(
            amount_in_wei, [self.jai.address, self.usdc.address]
        ).call()
        expected_out = amounts[-1]
        min_amount_out = int(expected_out * (1 - slippage))
        deadline = await self._get_deadline()
        contract = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_swap_exact_tokens_for_tokens
        )
        data = contract.encodeABI(
            fn_name="swapExactTokensForTokens",
            args=[
                amount_in_wei,
                min_amount_out,
                [self.jai.address, self.usdc.address],
                self.client.account.address,
                deadline
            ]
        )
        tx_params = await self.client.build_transaction(
            to=self.router_address,
            value=0,
            data=data,
        )
        
        tx_hash = await self.client.send_transaction(tx_params)
        return tx_hash


    async def swap_usdc_to_jai(
        self,
        amount: Optional[float] = None,
        all_balance: bool = False,
        slippage: float = 0.01
    ) -> str:
        if amount is None:
            amount = await self.client.get_balance(self.usdc.address, self.usdc.decimals)
        elif isinstance(amount, (float, int)):
            amount = TokenAmount.from_ether(amount, decimals=self.usdc.decimals)
            
        if all_balance:
            amount = await self.client.get_balance(self.usdc.address, self.usdc.decimals)
            
        amount_in_wei = amount.Wei
            
        await approve_token_if_needed(
            client=self.client,
            token_address=self.usdc.address,
            spender=self.router_address,
            amount_wei=amount_in_wei
        )
        router = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_get_amounts_out
        )
        amounts = await router.functions.getAmountsOut(
            amount_in_wei, [self.usdc.address, self.jai.address]
        ).call()
        expected_out = amounts[-1]
        min_amount_out = int(expected_out * (1 - slippage))
        deadline = await self._get_deadline()
        contract = self.client.web3.eth.contract(
            address=self.router_address,
            abi=self.abi_swap_exact_tokens_for_tokens
        )
        data = contract.encodeABI(
            fn_name="swapExactTokensForTokens",
            args=[
                amount_in_wei,
                min_amount_out,
                [self.usdc.address, self.jai.address],
                self.client.account.address,
                deadline
            ]
        )
        tx_params = await self.client.build_transaction(
            to=self.router_address,
            value=0,
            data=data,
        )
        
        tx_hash = await self.client.send_transaction(tx_params)
        return tx_hash
