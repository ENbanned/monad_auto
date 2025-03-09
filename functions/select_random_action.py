import random

from loguru import logger

from utils.blockvision_api import BlockvisionAPI
from utils.tasks.controller import Controller
from data.models import Settings
from evm.models.registry.tokens import MonadTokens
from utils.db_api.models import Wallet


async def select_random_action(controller: Controller, wallet: Wallet, initial: bool = False):
    settings = Settings()

    possible_actions = []
    weights = []

    swaps = 0

    eth_balance = await controller.client.get_native_balance()

    if float(eth_balance.Ether) < settings.minimal_balance:
        return 'Insufficient balance'

    if initial:
        api_blockvision = BlockvisionAPI(key=settings.blockvision_api_key)
        tx_list = await api_blockvision.get_all_transactions(
            address=controller.client.account.address
        )
        swaps = await controller.count_swaps(tx_list=tx_list)
        logger.debug(
            f'{wallet.address} | amount swaps: {swaps}/{wallet.number_of_swaps};'
        )

        if swaps >= wallet.number_of_swaps:
            return 'Processed'

    sufficient_balance = float(eth_balance.Ether) > settings.minimal_balance + settings.mod_amount_for_swap.to_

    wbtc_balance = await controller.client.get_balance(MonadTokens.WBTC.address, MonadTokens.WBTC.decimals) 
    bean_balance = await controller.client.get_balance(MonadTokens.BEAN.address, MonadTokens.BEAN.decimals)
    jai_balance = await controller.client.get_balance(MonadTokens.JAI.address, MonadTokens.JAI.decimals)
    usdc_balance = await controller.client.get_balance(MonadTokens.USDC.address, MonadTokens.USDC.decimals)

    if swaps < wallet.number_of_swaps:
        if usdc_balance.Wei:
            possible_actions += [
                controller.bean.swap_usdc_to_mon,
                controller.bean.swap_usdc_to_bean,
                controller.bean.swap_usdc_to_jai,
                controller.ambient.swap_usdc_to_mon,
            ]
            weights += [
                1,
                1,
                1,
                1,
            ]

        if jai_balance.Wei:
            possible_actions += [
                controller.bean.swap_jai_to_mon,
                controller.bean.swap_jai_to_usdc,
                controller.bean.swap_jai_to_bean,
            ]
            weights += [
                1,
                1,
                1,
            ]

        if bean_balance.Wei:
            possible_actions += [
                controller.bean.swap_bean_to_jai,
                controller.bean.swap_bean_to_mon,
            ]
            weights += [
                1,
                1,
            ]

        if wbtc_balance.Wei:
            possible_actions += [
                controller.ambient.swap_wbtc_to_mon
            ]
            weights += [
                1,
            ]

        if sufficient_balance:
            possible_actions += [
                controller.ambient.swap_mon_to_wbtc,
                controller.ambient.swap_mon_to_usdc,
                controller.bean.swap_mon_to_bean,
                controller.uniswap.swap_mon_to_usdt,
            ]
            weights += [
                1,
                1,
                1,
                1,
            ]

    if possible_actions:
        action = None
        while not action:
            action = random.choices(possible_actions, weights=weights)[0]

        else:
            return action

    return None
