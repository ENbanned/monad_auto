import random
import asyncio
from datetime import datetime, timedelta

from loguru import logger

from evm import EVMClient, Networks


from data.models import Settings
from utils.db_api.wallet_api import db
from utils.db_api.models import Wallet
from utils.tasks.controller import Controller
from functions.select_random_action import select_random_action
from utils.update_expired import update_expired


async def activity():
    settings = Settings()
    delay = 10

    update_expired(initial=False)
    await asyncio.sleep(5)

    while True:
        try:
            now = datetime.now()

            wallet: Wallet = db.one(
                Wallet, Wallet.initial_completed.is_(True) & (Wallet.next_activity_action_time <= now)
            )

            if not wallet:
                await asyncio.sleep(delay)
                continue

            client = EVMClient(private_key=wallet.private_key, network=Networks.MONAD, proxy=wallet.proxy)
            controller = Controller(client=client)

            now = datetime.now()
            action = await select_random_action(controller=controller, wallet=wallet, initial=False)

            if not action:
                logger.warning(f'{wallet.address} | select_random_action | can not choose the action')
                continue

            if action == 'Insufficient balance':
                logger.error(f'{wallet.address}: Insufficient balance')
                continue

            status = await action()
            if 'Failed' not in status:
                now = datetime.now()
                wallet.next_activity_action_time = now + timedelta(
                    seconds=random.randint(settings.activity_actions_delay.from_, settings.activity_actions_delay.to_)
                )

                db.commit()

                logger.success(f'{wallet.address}: {status}')

                next_action_time = min((wallet.next_activity_action_time for wallet in db.all(
                    Wallet, Wallet.initial_completed.is_(True)
                )))
                logger.info(f'The next closest activity action will be performed at {next_action_time}')

                await asyncio.sleep(delay)

            else:
                wallet.next_activity_action_time = now + timedelta(seconds=random.randint(10 * 60, 20 * 60))
                db.commit()
                logger.error(f'{wallet.address}: {status}')

        except BaseException as e:
            logger.exception(f'Something went wrong: {e}')

        finally:
            await asyncio.sleep(delay)
