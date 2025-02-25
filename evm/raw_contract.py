import json
from pathlib import Path
from web3 import Web3

class RawContract:
    def __init__(self, name: str, address: str, abi_filename: str = None):
        self.name = name
        self.address = Web3.to_checksum_address(address)
        self.abi_filename = abi_filename or f"{name}.json"
        self._abi = None

    @property
    def abi(self):
        if self._abi is None:
            self._abi = self._load_abi()
        return self._abi

    def _load_abi(self):
        path = Path("evm/abis") / self.abi_filename
        try:
            with path.open("r", encoding="utf-8") as file:
                abi = json.load(file)
            for item in abi:
                if item.get("inputs") is None:
                    item["inputs"] = []
            return abi
        except FileNotFoundError:
            raise FileNotFoundError(f"ABI файл не найден: {path}")
        except json.JSONDecodeError:
            raise ValueError(f"Ошибка парсинга ABI файла: {path}")
        