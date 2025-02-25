import random
import asyncio
from evm.base_activity import BaseActivity
from evm.client import EVMClient
from evm.models.registry.tokens import MonadTokens
from evm.models.token import TokenAmount
from evm.utils.token_utils import approve_token_if_needed
from utils.tasks.base import Base
from loguru import logger


class MultPli(BaseActivity, Base):
    def __init__(self, client: EVMClient):
        super().__init__(client)
        self.claim_contract = "0x181579497d5c4EfEC2424A21095907ED7d91ac9A"
        self.staking_contract = "0xBCF1415BD456eDb3a94c9d416F9298ECF9a2cDd0"
        
        self.usdc = MonadTokens.USDC
        self.multpli_usdc = self.client.web3.to_checksum_address("0x924F1Bf31b19a7f9695F3FC6c69C2BA668Ea4a0a")

    async def claim_usdc(self) -> str:
        data = (
            "0x32f289cf"
            "000000000000000000000000924f1bf31b19a7f9695f3fc6c69c2ba668ea4a0a"
        )

        tx = await self.client.build_transaction(
            to=self.claim_contract,
            data=bytes.fromhex(data[2:] if data.startswith('0x') else data),
            value=0
        )
        return await self.client.send_transaction(tx)

    async def stake_usdc(self, amount: float) -> str:
        try:
            amount_wei = amount.Wei if isinstance(amount, TokenAmount) else self.usdc.amount_to_wei(amount)
            
            balance = await self.client.web3.eth.contract(
                address=self.multpli_usdc,
                abi=[{
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                }]
            ).functions.balanceOf(self.client.account.address).call()
            
            await approve_token_if_needed(
                client=self.client,
                token_address=self.multpli_usdc,
                spender=self.staking_contract,
                amount_wei=amount_wei
            )
            
            allowance = await self.client.web3.eth.contract(
                address=self.multpli_usdc,
                abi=[{
                    "constant": True,
                    "inputs": [
                        {"name": "_owner", "type": "address"},
                        {"name": "_spender", "type": "address"}
                    ],
                    "name": "allowance",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "type": "function"
                }]
            ).functions.allowance(
                self.client.account.address,
                self.staking_contract
            ).call()

            data = (
                "0x47e7ef24"
                "000000000000000000000000924f1bf31b19a7f9695f3fc6c69c2ba668ea4a0a"
                f"{amount_wei:064x}"
            )

            tx = await self.client.build_transaction(
                to=self.staking_contract,
                data=bytes.fromhex(data[2:] if data.startswith('0x') else data),
                value=0
            )
            
            return await self.client.send_transaction(tx)
            
        except Exception as e:
            logger.error(f"Ошибка при стейкинге: {str(e)}")
            raise


    async def claim_and_stake(self) -> tuple[str, str]:
        claim_hash = await self.claim_usdc()
        
        await asyncio.sleep(10)
        
        stake_amount = random.uniform(20, 45)
        stake_hash = await self.stake_usdc(stake_amount)
        
        return claim_hash, stake_hash