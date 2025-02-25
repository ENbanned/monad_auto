from dataclasses import dataclass
from typing import Optional

@dataclass
class Network:
    name: str
    rpc_url: str
    chain_id: int

class Networks:
    ARBITRUM = Network(
        name='Arbitrum',
        rpc_url='https://endpoints.omniatech.io/v1/arbitrum/one/public',
        chain_id=42161
    )
    
    MONAD = Network(
        name='Monad Testnet',
        rpc_url='https://testnet-rpc.monad.xyz',
        chain_id=10143
    )
    
    @classmethod
    def get_network(cls, network_name: str) -> Optional[Network]:
        return getattr(cls, network_name.upper(), None)
    