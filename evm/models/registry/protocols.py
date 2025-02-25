from typing import Dict
from ..protocol import Protocol

class MonadProtocols:
    APRIORI = Protocol(
        address="0xb2f82D0f38dc453D596Ad40A37799446Cc89274A",
        name="aPriori",
        abi_filename="aPriori.json"
    )

    UNISWAP_ROUTER = Protocol(
        address="0x3aE6D8A282D67893e17AA70ebFFb33EE5aa65893",
        name="UniswapRouter",
        abi_filename="uniswap_router.json"
    )
    
    BEAN_EXCHANGE = Protocol(
        address="0xCa810D095e90Daae6e867c19DF6D9A8C56db2c89",
        name="BeanExchange",
        abi_filename=None
    )
    
    AMBIENT = Protocol(
        address="0x88B96aF200c8a9c35442C8AC6cd3D22695AaE4F0",
        name="Ambient",
        abi_filename="ambient.json"
    )
    
    MULTPLI_CLAIM = Protocol(
        address="0x181579497d5c4EfEC2424A21095907ED7d91ac9A",
        name="MultPliClaim",
        abi_filename=None
    )
    
    MULTPLI_STAKE = Protocol(
        address="0xBCF1415BD456eDb3a94c9d416F9298ECF9a2cDd0",
        name="MultPliStake",
        abi_filename=None
    )
     
    
    _by_address: Dict[str, Protocol] = {}

    @classmethod
    def get_by_address(cls, address: str) -> Protocol:
        """Получает протокол по его адресу"""
        if not cls._by_address:
            for attr_name in dir(cls):
                if attr_name.startswith('_'):
                    continue
                protocol = getattr(cls, attr_name)
                if isinstance(protocol, Protocol):
                    cls._by_address[protocol.address.lower()] = protocol
        
        address = address.lower()
        if address not in cls._by_address:
            raise ValueError(f"Неизвестный протокол с адресом {address}")
        
        return cls._by_address[address]