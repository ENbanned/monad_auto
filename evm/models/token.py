import json
from pathlib import Path
from typing import Optional, Union
from web3 import Web3
from decimal import Decimal
from web3.contract import Contract

class TokenAmount:
    def __init__(self, amount: Union[int, float, str, Decimal], decimals: int = 18, wei: bool = False) -> None:
        if wei:
            self.Wei: int = int(amount)
            self.Ether: Decimal = Decimal(str(amount)) / 10 ** decimals
        else:
            self.Wei: int = int(Decimal(str(amount)) * 10 ** decimals)
            self.Ether: Decimal = Decimal(str(amount))

        self.decimals = decimals


    @classmethod
    def from_wei(cls, wei_amount: int, decimals: int = 18) -> 'TokenAmount':
        return cls(amount=wei_amount, decimals=decimals, wei=True)
    
    
    @classmethod 
    def from_ether(cls, ether_amount: Union[int, float, str, Decimal], decimals: int = 18) -> 'TokenAmount':
        return cls(amount=ether_amount, decimals=decimals, wei=False)


    def __str__(self):
        return f'{self.Ether}'


class Token:
    def __init__(
        self,
        address: str,
        name: str,
        symbol: str,
        decimals: int,
        is_native: bool = False,
        abi_filename: Optional[str] = None
    ):
        self.address = Web3.to_checksum_address(address)
        self.name = name
        self.symbol = symbol
        self.decimals = decimals
        self.is_native = is_native
        self.abi_filename = abi_filename
        self._abi = None
        self._contract: Optional[Contract] = None


    @property
    def abi(self):
        if self._abi is None and self.abi_filename:
            path = Path("evm/abis") / self.abi_filename
            try:
                with path.open("r", encoding="utf-8") as file:
                    self._abi = json.load(file)
                for item in self._abi:
                    if item.get("inputs") is None:
                        item["inputs"] = []
                        
            except FileNotFoundError:
                raise FileNotFoundError(f"ABI файл не найден: {path}")
            except json.JSONDecodeError:
                raise ValueError(f"Ошибка парсинга ABI файла: {path}")
        return self._abi


    @property
    def multiplier(self) -> int:
        return 10 ** self.decimals


    def amount_to_wei(self, amount: float) -> int:
        return int(amount * self.multiplier)


    def wei_to_amount(self, wei_amount: int) -> float:
        return wei_amount / self.multiplier


    def get_contract(self, web3) -> Optional[Contract]:
        if not self.is_native and self._contract is None and self.abi:
            self._contract = web3.eth.contract(
                address=self.address,
                abi=self.abi
            )
        return self._contract
    