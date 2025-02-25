import json
from pathlib import Path
from typing import Optional
from web3 import Web3
from web3.contract import Contract

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