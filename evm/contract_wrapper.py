import json
from pathlib import Path
from web3 import Web3
from .base_activity import BaseActivity


class ContractWrapper(BaseActivity):
    def __init__(self, client, abi_filename: str, contract_address: str):
        super().__init__(client)
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.abi = self._load_abi(abi_filename)
        self.contract = self.client.web3.eth.contract(address=self.contract_address, abi=self.abi)


    def _load_abi(self, abi_filename: str):
        path = Path("evm/abis") / abi_filename
        with path.open("r", encoding="utf-8") as file:
            abi = json.load(file)
            
        for item in abi:
            if item.get("inputs") is None:
                item["inputs"] = []
        return abi
