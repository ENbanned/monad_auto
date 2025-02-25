from evm.base_activity import BaseActivity
from evm.client import EVMClient
from evm.models.registry.tokens import MonadTokens
from evm.models.token import TokenAmount
from utils.tasks.base import Base


class Shmonad(BaseActivity, Base):
    def __init__(self, client: EVMClient):
        super().__init__(client)
        
        self.mon = MonadTokens.MON
        self.contract = self.client.web3.to_checksum_address("0x3a98250F98Dd388C211206983453837C8365BDc1")
        
        """
        function_signature 0x6e553f65
        00000000000000000000000000000000000000000000000000038d7ea4c68000
        000000000000000000000000e72ff0f0776453bb8adfd439655c01424ec3680a
        """
        
    async def stake_mon(self, amount: int | float = None):
        
        if amount is None:
            amount = Base.get_mon_amount_for_stake()
            
        amount_in_wei = amount.Wei if isinstance(amount, TokenAmount) else self.mon.amount_to_wei(amount)
                
        data = (
            f'0x6e553f65'
            f'{hex(amount_in_wei)[2:].zfill(64)}'
            f'{str(self.client.account.address).lower()[2:].zfill(64)}'
        )

        tx_params = await self.client.build_transaction(
            to=self.contract,
            value=amount_in_wei,
            data=data,
        )
        tx_hash = await self.client.send_transaction(tx_params)
        
        return tx_hash
    
    async def unstake_mon(self, amount: int | float):
        
        amount_in_wei = amount.Wei if isinstance(amount, TokenAmount) else self.mon.amount_to_wei(amount)

        
        data = (
            f'0xba087652'
            f'{hex(amount_in_wei)[2:].zfill(64)}'
            f'{str(self.client.account.address).lower()[2:].zfill(64)}'
            f'{str(self.client.account.address).lower()[2:].zfill(64)}'
        )
        
        print(data)

        tx_params = await self.client.build_transaction(
            to=self.contract,
            value=0,
            data=data,
        )
        tx_hash = await self.client.send_transaction(tx_params)
        
        return tx_hash