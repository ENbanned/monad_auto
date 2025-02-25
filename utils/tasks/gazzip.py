import asyncio
import aiohttp
from evm.base_activity import BaseActivity
from evm.client import EVMClient
from evm.models.token import TokenAmount
from utils.tasks.base import Base
from loguru import logger


class GazZip(BaseActivity, Base):
    def __init__(self, client: EVMClient):
        super().__init__(client)
        self.contract_address = "0x391E7C679d29bD940d63be94AD22A25d25b5A604"
        
        self.input_data = "0x0101b1"
        
        self.USD_AMOUNT = 2.0
        
        
    async def _get_eth_amount_for_usd(self, usd_amount: float = 2.0) -> TokenAmount:
        try:
            eth_price = await self._get_eth_price()
        except Exception as e:
            return e
        
        eth_amount = usd_amount / eth_price
        
        return TokenAmount.from_ether(eth_amount)
    
    
    async def _get_eth_price(self) -> float:        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT') as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data['price'])
                    else:
                        return 2666.0
        except Exception as e:
            logger.error(f"Ошибка при получении цены ETH: {e}")
            return 2666.0
        
        
    async def buy_monad(self, usd_amount: float = 2.0, max_retries: int = 3) -> str:
        retry_count = 0
        while retry_count < max_retries:
            try:
                eth_amount = await self._get_eth_amount_for_usd(usd_amount)
                break
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    return f"Не удалось получить цену ETH после {max_retries} попыток: {str(e)}"
                await asyncio.sleep(1)
        
        balance = await self.client.web3.eth.get_balance(self.client.account.address)
        balance_token_amount = TokenAmount.from_wei(balance)
        
        eth_amount_float = float(eth_amount.Ether)
        balance_float = float(balance_token_amount.Ether)
        
        if balance_token_amount.Ether < eth_amount.Ether:
            return f"Недостаточно ETH на балансе. Требуется: {eth_amount_float:.8f} ETH (${usd_amount}), доступно: {balance_float:.8f} ETH"
            
        eth_amount_float = float(eth_amount.Ether)
        logger.info(f"Покупка MONAD на {usd_amount} USD ({eth_amount_float:.8f} ETH) по курсу {usd_amount/eth_amount_float:.2f} USD/ETH")
        
        tx_params = await self.client.build_transaction(
            to=self.contract_address,
            value=eth_amount.Wei,
            data=self.input_data,
        )
        
        tx_hash = await self.client.send_transaction(tx_params)
        
        return f"Транзакция отправлена. Хеш: {tx_hash}"
    
    async def buy_monad_with_exact_eth(self, eth_amount: float) -> str:
        amount = TokenAmount.from_ether(eth_amount)
        
        balance = await self.client.web3.eth.get_balance(self.client.account.address)
        balance_token_amount = TokenAmount.from_wei(balance)
        
        if balance_token_amount.Ether < amount.Ether:
            return f"Недостаточно ETH на балансе. Требуется: {amount.Ether}, доступно: {balance_token_amount.Ether}"
        
        tx_params = await self.client.build_transaction(
            to=self.contract_address,
            value=amount.Wei,
            data=self.input_data,
        )
        
        tx_hash = await self.client.send_transaction(tx_params)
        
        return f"Транзакция отправлена. Хеш: {tx_hash}"