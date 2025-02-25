from evm.base_activity import BaseActivity
from evm.client import EVMClient
from utils.tasks.base import Base
from loguru import logger


class OwlTo(BaseActivity, Base):
    def __init__(self, client: EVMClient):
        super().__init__(client)
        self.bytecode = (
            "0x60806040"
            "527389a512a24e9d63e98e41f681bf77f27a7ef89eb76000806101000a815481"
            "73ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffff"
            "ffffffffffffffffffffffffffffff1602179055506000806000905490610100"
            "0a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffff"
            "ffffffffffffffffffffffffffff163460405161009f90610185565b60006040"
            "518083038185875af1925050503d80600081146100dc576040519150601f1960"
            "3f3d011682016040523d82523d6000602084013e6100e1565b606091505b5050"
            "905080610125576040517f08c379a00000000000000000000000000000000000"
            "0000000000000000000000815260040161011c9061019a565b60405180910390"
            "fd5b506101d6565b60006101386007836101c5565b91507f4661696c75726500"
            "0000000000000000000000000000000000000000000000006000830152602082"
            "019050919050565b60006101786000836101ba565b9150600082019050919050"
            "565b60006101908261016b565b9150819050919050565b600060208201905081"
            "810360008301526101b38161012b565b9050919050565b600081905092915050"
            "565b600082825260208201905092915050565b603f806101e46000396000f3fe"
            "6080604052600080fdfea264697066735822122095fed2c557b62b9f55f8b382"
            "2b0bdc6d15fd93abb95f37503d3f788da6cbb30064736f6c63430008000033"
        )

    async def deploy(self) -> str:
        try:
            tx = await self.client.build_transaction(
                to="",
                data=self.bytecode,
                value=0,
            )
            
            tx_hash = await self.client.send_transaction(tx)
            return tx_hash
            
        except Exception as e:
            logger.error(f"Ошибка при деплое контракта: {e}")
            raise