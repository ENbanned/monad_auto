from typing import Dict
from .client import EVMClient
from .raw_contract import RawContract
from web3.contract import Contract


class BaseActivity:
    def __init__(self, client: EVMClient):
        self.client = client
        self._contracts: Dict[str, Contract] = {}

    async def get_balance(self, address: str, in_wei: bool = False):
        balance = await self.client.web3.eth.get_balance(address)
        if in_wei:
            return balance
        else:
            return self.client.web3.fromWei(balance, 'ether')

    def get_contract(self, raw_contract: RawContract) -> Contract:
        if raw_contract.address not in self._contracts:
            self._contracts[raw_contract.address] = self.client.web3.eth.contract(
                address=raw_contract.address,
                abi=raw_contract.abi
            )
        return self._contracts[raw_contract.address]
    