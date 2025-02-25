from evm.base_activity import BaseActivity
from evm.client import EVMClient
from evm.models.registry.tokens import MonadTokens
from utils.tasks.base import Base


class Curvance(BaseActivity, Base):
    def __init__(self, client: EVMClient):
        super().__init__(client)

        self.mon = MonadTokens.MON
        self.claim_ca = "0x2f930b339DE82F34FDbe54e872Eb4A2855B76EA2"
        
        
    async def claim_all_tokens(self):
        balance = await self.client.get_native_balance()
        
        if float(balance.Ether) < 0.03:
            return 'Недостаточный баланс для выполнения активностей в Curvance.'
        
        data = (
            f'0x7214c206'
            f'{str(self.client.account.address).lower()[2:].zfill(64)}'
            '0000000000000000000000000000000000000000000000000000000000000060'
            '0000000000000000000000000000000000000000000000000000000000000160'
            '0000000000000000000000000000000000000000000000000000000000000007'
            '0000000000000000000000005d876d73f4441d5f2438b1a3e2a51771b337f27a' # usdc
            '0000000000000000000000006bb379a2056d1304e73012b99338f8f581ee2e18' # wbtc
            '0000000000000000000000000e1c9362cdea1d556e5ff89140107126baaf6b09' # arpMON
            '0000000000000000000000005b54153100e40000f6821a7ea8101dc8f5186c2d' # SWETH
            '0000000000000000000000007fdf92a43c54171f9c278c67088ca43f2079d09b' # LUSD
            '000000000000000000000000dfcf14d3e2a6eb731e27a810cb1400eea42a7fdc' # aUSD
            '000000000000000000000000b5481b57ff4e23ea7d2fda70f3137b16d0d99118' # CVE
            '0000000000000000000000000000000000000000000000000000000000000007'
            '00000000000000000000000000000000000000000000000000000002540be400' # 10000000000
            '00000000000000000000000000000000000000000000000000000000004c4b40' # 5000000
            '00000000000000000000000000000000000000000000003635c9adc5dea00000' # 1.0E+21
            '0000000000000000000000000000000000000000000000000de0b6b3a7640000' # 1000000000000000000
            '00000000000000000000000000000000000000000000003635c9adc5dea00000' # 1.0E+21
            '00000000000000000000000000000000000000000000003635c9adc5dea00000' # 1.0E+21
            '0000000000000000000000000000000000000000000000008ac7230489e80000' # 1.0E+19
        )

        tx_params = await self.client.build_transaction(
            to=self.claim_ca,
            value=0,
            data=data,
        )
        
        tx_hash = await self.client.send_transaction(tx_params)
        
        return tx_hash
    