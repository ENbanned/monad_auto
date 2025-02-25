from datetime import datetime, timedelta

from fake_useragent import UserAgent

from utils.web_requests import async_get, aiohttp_params

class Module:
    """
    Class with functions related to some API module.

    Attributes:
        key (str): an API key.
        url (str): an API entrypoint URL.
        headers (Dict[str, Any]): a headers for requests.
        module (str): a module name.

    """
    key: str
    url: str
    headers: dict[str]
    module: str

    def __init__(self, key: str, url: str, headers: dict[str]) -> None:
        """
        Initialize the class.

        Args:
            key (str): an API key.
            url (str): an API entrypoint URL.
            headers (Dict[str, Any]): a headers for requests.

        """
        self.key = key
        self.url = url
        self.headers = headers


class Account(Module):
    module: str = 'address'

    async def txlist(
            self,
            address: str,
            page: int = 1,
            limit: int = 50,
            chain: str | None = 'zksync'
    ) -> list[dict]:
        """
        Query address transaction list information

        https://www.oklink.com/docs/en/#blockchain-general-api-address-query-address-transaction-list-information
        """

        action = 'transaction-list'

        params = {
            'chainShortName': chain,
            'address': address,
            'limit': limit,
            'page': page
        }

        res = await async_get(
            url=self.url + f'/api/v5/explorer/{self.module}/{action}',
            params=aiohttp_params(params),
            headers=self.headers
        )

        return res['data'][0]['transactionLists']

    async def txlist_all(
            self,
            address: str,
            chain: str | None = 'zksync',
    ) -> list[dict]:
        page = 1
        limit = 50
        txs_lst = []
        txs = await self.txlist(
            address=address,
            page=page,
            limit=limit,
            chain=chain,
        )
        txs_lst += txs
        while len(txs) == limit:
            page += 1
            txs = await self.txlist(
                address=address,
                page=page,
                limit=limit,
                chain=chain,
            )
            txs_lst += txs
        return txs_lst

    async def find_tx_by_method_id(
            self,
            address: str,
            to: str,
            method_id: str,
            tx_list: list[dict] | None = None
    ):
        if not tx_list:
            tx_list = await self.txlist_all(address=address)
        txs = {}
        for tx in tx_list:
            if tx.get('state') == 'success' and tx.get('to') == to.lower() and method_id in tx.get('methodId'):
                txs[tx.get('txId')] = tx
        return txs

class APIFunctions:
    """
    Class with functions related to Blockscan API.

    Attributes:
        key (str): an API key.
        url (str): an API entrypoint URL.
        headers (Dict[str, Any]): a headers for requests.
        account (Account): functions related to 'account' API module.

    """

    def __init__(self, key: str, url: str) -> None:
        """
        Initialize the class.

        Args:
            key (str): an API key.
            url (str): an API entrypoint URL.

        """
        self.key = key
        self.url = url
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'user-agent': UserAgent().chrome,
            'Ok-Access-Key': self.key,
        }
        self.account = Account(self.key, self.url, self.headers)
