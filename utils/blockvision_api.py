from fake_useragent import UserAgent
from curl_cffi.requests import AsyncSession


class BlockvisionAPI:
    def __init__(self, key: str):
        self.key = key
        self.url = 'https://api.blockvision.org/v2/monad'
        self.headers = {
            'accept': 'application/json',
            'x-api-key': self.key,
            'user-agent': UserAgent().chrome
        }

    async def get_account_transactions(
            self,
            address: str,
            page: int = 1,
            limit: int = 50
        ) -> list[dict]:

        cursor = (page - 1) * limit if page > 1 else 0 
        
        params = {
            'address': address.lower(),
            'limit': limit
        }
        
        if cursor > 0:
            params['cursor'] = cursor
            
        async with AsyncSession(verify=False) as session:
            response = await session.get(
                url=f"{self.url}/account/transactions",
                params=params,
                headers=self.headers
            )
            data = response.json()
            
            if data.get('code') != 0:
                raise Exception(f"API Error: {data.get('message')} - {data.get('reason')}")
                
            return data['result']['data']

    async def get_all_transactions(
            self,
            address: str,
    ) -> list[dict]:
        page = 1
        limit = 50
        txs_lst = []
        
        while True:
            txs = await self.get_account_transactions(
                address=address,
                page=page,
                limit=limit
            )
            txs_lst.extend(txs)
            
            if len(txs) < limit:
                break
                
            page += 1
            
        return txs_lst


    async def find_transactions_by_method_id(
            self,
            address: str,
            to: str,
            method_id: str,
            tx_list: list[dict] | None = None
    ) -> dict[str, dict]:
        if not tx_list:
            tx_list = await self.get_all_transactions(address=address)
            
        txs = {}
        for tx in tx_list:
            if (tx.get('status') == 1 and 
                tx.get('to', '').lower() == to.lower() and 
                tx.get('methodID') == method_id):
                txs[tx.get('hash')] = tx
                
        return txs
    