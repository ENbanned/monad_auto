import asyncio

import aiohttp

from evm import EVMClient
from evm.models.token import TokenAmount
from utils.utils import randfloat

from data.models import Settings

class Base:
    
    MIN_SWAP_AMOUNTS = {
        'ambient': 0.0015,
        'bean': 0.0001,
        'uniswap': 0.004
    }
    
    def __init__(self, client: EVMClient):
        self.client = client
        
        
    @staticmethod
    def get_eth_amount_for_swap(protocol_name: str = 'ambient'):
        settings = Settings()
        min_amount = Base.MIN_SWAP_AMOUNTS.get(protocol_name, 0.0015)
        
        amount = max(
            min_amount,
            randfloat(
                from_=settings.mod_amount_for_swap.from_,
                to_=settings.mod_amount_for_swap.to_,
                step=0.0000001
            )
        )
        
        return TokenAmount.from_ether(amount)


    def get_mon_amount_for_stake():
        settings = Settings()
        return TokenAmount(
            amount=randfloat(
                from_=settings.mod_amount_for_stake.from_,
                to_=settings.mod_amount_for_stake.to_,
                step=0.0000001
            )
        )
    
    

