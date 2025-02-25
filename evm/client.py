import asyncio
from web3 import AsyncWeb3, AsyncHTTPProvider
from eth_account import Account
from .networks import Network
from fake_useragent import UserAgent
from evm.models.token import TokenAmount
from loguru import logger

class EVMClient:
    def __init__(self, private_key: str, network: Network, proxy: str = None):
        self.private_key = private_key
        self.network = network
        
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'user-agent': UserAgent().chrome
        }
        
        if proxy:
            if 'http' not in proxy:
                proxy = f'http://{proxy}'
            self.proxy = proxy
        else:
            self.proxy = None
            
        provider = AsyncHTTPProvider(
            endpoint_uri=network.rpc_url,
            request_kwargs={
                'proxy': self.proxy,
                'headers': self.headers
            }
        )
        
        self.web3 = AsyncWeb3(provider)
        self.account = Account.from_key(private_key)
        self.chain_id = network.chain_id

    async def get_nonce(self):
        try:
            nonce = await self.web3.eth.get_transaction_count(
                self.account.address, 
                "pending" 
            )
            return nonce
        except Exception as e:
            logger.error(f"Ошибка при получении nonce: {e}")
            
            return await self.web3.eth.get_transaction_count(self.account.address)

    async def estimate_gas(self, tx: dict) -> int:
        try:
            estimated_gas = await self.web3.eth.estimate_gas(tx)
            return int(estimated_gas * 1.1)
        except Exception as e:
            logger.error(f"Ошибка при оценке газа: {e}")
            return tx.get('gas', 21000)


    async def build_transaction(
        self, 
        to: str, 
        value: int = 0, 
        data: bytes = b'', 
        gas: int = None
    ):
        try:
            await asyncio.sleep(1)
            
            tx_params = {
                'from': self.account.address,
                'to': to,
                'value': value,
                'data': data,
                'nonce': await self.get_nonce(),
                'chainId': self.chain_id,
                'type': '0x2'
            }

            estimated_gas = await self.web3.eth.estimate_gas(tx_params)
            
            latest_block = await self.web3.eth.get_block('latest')
            base_fee = latest_block['baseFeePerGas']

            max_priority_fee = await self.web3.eth.max_priority_fee

            tx = {
                **tx_params,
                'gas': estimated_gas,  
                'maxFeePerGas': base_fee + max_priority_fee,
                'maxPriorityFeePerGas': max_priority_fee
            }

            return tx
            
        except Exception as e:
            print(f"Ошибка при построении транзакции: {e}")
            raise

    async def send_transaction(self, tx: dict) -> str:
        signed_tx = self.web3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = await self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        return tx_hash.hex()
    
    
    async def get_native_balance(self) -> TokenAmount:
        try:
            # Получаем баланс адреса в wei
            balance_wei = await self.web3.eth.get_balance(self.account.address)
            return TokenAmount(amount=balance_wei, decimals=18, wei=True)
        except Exception as e:
            logger.error(f"Ошибка при получении баланса: {e}")
            return None
    
    async def get_balance(self, token_address: str, decimals: int = None) -> TokenAmount:
        try:
            token_address = self.web3.to_checksum_address(token_address)
            
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function",
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function",
                }
            ]
            
            token_contract = self.web3.eth.contract(address=token_address, abi=erc20_abi)
            
            balance = await token_contract.functions.balanceOf(self.account.address).call()
            
            if decimals is None:
                decimals = await token_contract.functions.decimals().call()
            
            return TokenAmount(amount=balance, decimals=decimals, wei=True)
        
        except Exception as e:
            logger.error(f"Ошибка при получении баланса токена: {e}")
            return None

    
