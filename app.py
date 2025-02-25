from functions.create_files import create_files
from functions.Import import Import
from functions.initial import initial
from functions.activity import activity

from loguru import logger
from data.models import Settings

# Новые импорты
from functions.wallets_loader import load_wallets
from utils.tasks.mandatory_actions import MandatoryActions
from utils.tasks.faucet import FaucetClaim
from functions.check_mon_balance import check_balance
from functions.mexc_withdraw import process_mexc_withdraw
from functions.gazzip_buy import process_gazzip_buy  # Новый импорт

import asyncio

async def start_script():
    settings = Settings()
    if not settings.blockvision_api_key:
        logger.error('Specify the API key for blockvision!')
        return

    await asyncio.wait([
        asyncio.create_task(initial()),
        asyncio.create_task(activity())
    ])

async def run_mandatory_actions():
    wallets = load_wallets()
    actions = MandatoryActions()
    tasks = [asyncio.create_task(actions.run(wallet)) for wallet in wallets]
    await asyncio.gather(*tasks)

async def run_faucet_claim():
    settings = Settings()
    
    if not settings.capsolver_api_key:
        logger.error('Specify the Capsolver API key!')
        return
    
    wallets = load_wallets()
    faucet = FaucetClaim()
    tasks = [asyncio.create_task(faucet.claim(wallet)) for wallet in wallets]
    await asyncio.gather(*tasks)

async def run_check_mon_balance():
    wallets = load_wallets()
    tasks = [asyncio.create_task(check_balance(wallet)) for wallet in wallets]
    await asyncio.gather(*tasks)
    
async def run_mexc_withdraw():
    settings = Settings()
    
    if not settings.mexc_api_key or not settings.mexc_secret_key:
        logger.error('Specify the Mexc API key and secret key!')
        return
    
    await process_mexc_withdraw()

async def run_gazzip_buy():
    await process_gazzip_buy()

if __name__ == '__main__':
    create_files()
    print("""Выберите один из вариантов:
1) Импортировать кошельки из таблицы в базу данных.
2) Запустить скрипт (свапы).
3) Выполнить обязательные действия.
4) Собрать MON с оффициального крана.
5) Проверить баланс в токенах MON.
6) Пополнить кошельки с MEXC через ETH(Arb).
7) Купить MON используя ETH(Arb).
8) Выйти.
""")
    
    try:
        action = int(input('> '))
        if action == 1:
            asyncio.run(Import.wallets())
        elif action == 2:
            asyncio.run(start_script())
        elif action == 3:
            asyncio.run(run_mandatory_actions())
        elif action == 4:
            asyncio.run(run_faucet_claim())
        elif action == 5:
            asyncio.run(run_check_mon_balance())
        elif action == 6:
            asyncio.run(run_mexc_withdraw())
        elif action == 7:
            asyncio.run(run_gazzip_buy())
        elif action == 8:
            pass
    except KeyboardInterrupt:
        print()
    except ValueError as err:
        logger.error(f'ValueError: {err}')
    except BaseException as err:
        logger.error(f'BaseException: {err}')