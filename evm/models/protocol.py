import json
from pathlib import Path
from typing import Optional
from web3 import Web3
from web3.contract import Contract


class Protocol:
    def __init__(
        self,
        address: str,
        name: str,
        abi_filename: str
    ):
        self.address = Web3.to_checksum_address(address)
        self.name = name
        self.abi_filename = abi_filename
        self._abi = None
        self._contract: Optional[Contract] = None
        
        
    @property
    def abi(self):
        if self._abi is None:
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


    def get_contract(self, web3) -> Contract:
        if self._contract is None:
            self._contract = web3.eth.contract(
                address=self.address,
                abi=self.abi
            )
        return self._contract