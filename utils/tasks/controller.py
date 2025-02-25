from evm import EVMClient, Networks
from utils.explorer_api import APIFunctions
from utils.blockvision_api import BlockvisionAPI
from data.models import Settings
from evm.models.registry.protocols import MonadProtocols

from utils.tasks.base import Base

from utils.tasks.ambient import AmbientMonad
from utils.tasks.aPriori import aPriori
from utils.tasks.bean import BeanExchange
from utils.tasks.multpli import MultPli
from utils.tasks.owlto import OwlTo
from utils.tasks.shmonad import Shmonad
from utils.tasks.uniswap import UniswapMonad


class Controller(Base):
    def __init__(self, client: EVMClient):
        super().__init__(client)

        self.base = Base(client=client)
        
        self.ambient = AmbientMonad(client)
        self.aPriori = aPriori(client)
        self.bean = BeanExchange(client)
        self.multpli = MultPli(client)
        self.owlto = OwlTo(client)
        self.shmonad = Shmonad(client)
        self.uniswap = UniswapMonad(client)
        

    async def count_swaps(self, tx_list: list[dict] | None = None):
        settings = Settings()
        result_count = 0

        api_blockvision = BlockvisionAPI(key=settings.blockvision_api_key)

        if not tx_list:
            tx_list = await api_blockvision.get_all_transactions(
                address=self.client.account.address
            )

        # ambient (mon-wbtc, wbtc-mon)
        result_count += len(await api_blockvision.find_transactions_by_method_id(
            address=self.client.account.address,
            to=MonadProtocols.AMBIENT.address,
            method_id='userCmd',
            tx_list=tx_list
        ))

        # bean (swapExactETHForTokens)
        result_count += len(await api_blockvision.find_transactions_by_method_id(
            address=self.client.account.address,
            to=MonadProtocols.BEAN_EXCHANGE.address,
            method_id='swapExactETHForTokens',
            tx_list=tx_list
        ))
        
        # bean (swapExactTokensForETH)
        result_count += len(await api_blockvision.find_transactions_by_method_id(
            address=self.client.account.address,
            to=MonadProtocols.BEAN_EXCHANGE.address,
            method_id='swapExactTokensForETH',
            tx_list=tx_list
        ))
        
        # bean (swapExactTokensForTokens)        
        result_count += len(await api_blockvision.find_transactions_by_method_id(
            address=self.client.account.address,
            to=MonadProtocols.BEAN_EXCHANGE.address,
            method_id='swapExactTokensForTokens',
            tx_list=tx_list
        ))

        # uniswap (mon - usdt, usdt - mon)
        result_count += len(await api_blockvision.find_transactions_by_method_id(
            address=self.client.account.address,
            to=MonadProtocols.UNISWAP_ROUTER.address,
            method_id='execute',
            tx_list=tx_list
        ))

        return result_count

