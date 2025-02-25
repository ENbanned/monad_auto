from typing import Dict
from ..token import Token

class MonadTokens:

    MON = Token(
        address="0x0000000000000000000000000000000000000000",
        name="Monad",
        symbol="MON",
        decimals=18,
        is_native=True
    )

    WMON = Token(
        address="0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701",
        name="Wrapped Monad",
        symbol="WMON",
        decimals=18,
        abi_filename="monad_wrap_eth.json"
    )

    USDT = Token(
        address="0xfbc2d240a5ed44231aca3a9e9066bc4b33f01149",
        name="Tether USD",
        symbol="USDT",
        decimals=6
    )
    
    BEAN = Token(
        address="0x268E4E24E0051EC27b3D27A95977E71cE6875a05",
        name="Bean Exchange",
        symbol="BEAN",
        decimals=18
    )
    
    JAI = Token(
        address="0xCc5B42F9d6144DFDFb6fb3987a2A916af902F5f8",
        name="AI Jarvis",
        symbol="JAI",
        decimals=6
    )
    
    USDC = Token(
        address="0xf817257fed379853cDe0fa4F97AB987181B1E5Ea",
        name="USD Coin",
        symbol="USDC",
        decimals=6
    )
    
    WBTC = Token(
        address="0xcf5a6076cfa32686c0Df13aBaDa2b40dec133F1d",
        name="Wrapped Bitcoin",
        symbol="WBTC", 
        decimals=8,
        abi_filename="wbtc.json"
    )

    _by_address: Dict[str, Token] = {}


    @classmethod
    def get_by_address(cls, address: str) -> Token:
        if not cls._by_address:
            for attr_name in dir(cls):
                if attr_name.startswith('_'):
                    continue
                token = getattr(cls, attr_name)
                if isinstance(token, Token):
                    cls._by_address[token.address.lower()] = token
        
        address = address.lower()
        if address not in cls._by_address:
            raise ValueError(f"Неизвестный токен с адресом {address}")
        
        return cls._by_address[address]