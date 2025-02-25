import asyncio
from web3.contract import Contract

from evm.base_activity import BaseActivity
from evm.client import EVMClient
from evm.models.token import TokenAmount
from evm.models.registry.tokens import MonadTokens
from evm.models.registry.protocols import MonadProtocols
from utils.tasks.base import Base


class aPriori(BaseActivity, Base):
    def __init__(self, client: EVMClient):
        super().__init__(client)
        self.protocol = MonadProtocols.APRIORI
        self.mon = MonadTokens.MON
        self.contract = self.protocol.get_contract(self.client.web3)


    async def stake_mon(self, amount: int | float = None) -> None:
        if amount is None:
            amount = Base.get_mon_amount_for_stake()
        
        amount_wei = amount.Wei if isinstance(amount, TokenAmount) else self.mon.amount_to_wei(amount)
        tx = await self.client.build_transaction(
            to=self.protocol.address,
            data=self.contract.encodeABI(
                fn_name="deposit",
                args=[amount_wei, self.client.account.address]
            ),
            value=amount_wei
        )
        
        tx_hash = await self.client.send_transaction(tx)
        return tx_hash
    
    
    async def unstake_mon(self, amount: int | float) -> None:
        amount_wei = amount.Wei if isinstance(amount, TokenAmount) else self.mon.amount_to_wei(amount)
        shares = await self.contract.functions.convertToShares(amount_wei).call()
        
        tx_req = await self.client.build_transaction(
            to=self.protocol.address,
            data=self.contract.encodeABI(
                fn_name="requestRedeem",
                args=[shares, self.client.account.address, self.client.account.address]
            )
        )
        await self.client.send_transaction(tx_req)
        
        next_request = await self.contract.functions.nextRequestId().call()
        request_id = next_request - 1
        
        wait_time = await self.contract.functions.withdrawalWaitTime().call()
        await asyncio.sleep(wait_time + 60)
        
        tx_redeem = await self.client.build_transaction(
            to=self.protocol.address,
            data=self.contract.encodeABI(
                fn_name="redeem",
                args=[request_id, self.client.account.address]
            )
        )
        await self.client.send_transaction(tx_redeem)
    
    
    async def get_aprmon_balance(self) -> int:
        balance = await self.contract.functions.balanceOf(self.client.account.address).call()
        return balance


    async def get_exchange_rates(self) -> dict:
        one_ether = 10**18
        assets = await self.contract.functions.convertToAssets(one_ether).call()
        shares = await self.contract.functions.convertToShares(one_ether).call()
        return {"assets": assets, "shares": shares}
