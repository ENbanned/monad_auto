import csv
import random

from loguru import logger

from evm import EVMClient, Networks

from data import config
from data.models import WalletCSV, Settings
from utils.db_api.wallet_api import get_wallet, db
from utils.db_api.models import Wallet



class Import:
    @staticmethod
    def get_wallets_from_csv(csv_path: str, skip_first_line: bool = True) -> list[WalletCSV]:
        wallets = []

        with open(csv_path) as f:
            reader = csv.reader(f)
            for row in reader:
                if skip_first_line:
                    skip_first_line = False
                    continue
                wallets.append(WalletCSV(
                    private_key=row[0].strip(),
                    proxy=row[1].strip(),
                    name=row[2].strip(),
                ))
        return wallets

    @staticmethod
    async def wallets():
        settings = Settings()
        wallets = Import.get_wallets_from_csv(csv_path=config.IMPORT_FILE)

        imported = []
        edited = []
        total = len(wallets)

        for wallet in wallets:
            wallet_instance = get_wallet(private_key=wallet.private_key)
            if wallet_instance and (
                    wallet_instance.proxy != wallet.proxy or
                    wallet_instance.name != wallet.name
            ):
                wallet_instance.proxy = wallet.proxy
                wallet_instance.name = wallet.name
                db.commit()
                edited.append(wallet_instance)

            if not wallet_instance:
                client = EVMClient(private_key=wallet.private_key, network=Networks.MONAD)
                wallet_instance = Wallet(
                    private_key=wallet.private_key,
                    address=client.account.address,
                    proxy=wallet.proxy,
                    name=wallet.name,
                    number_of_swaps=random.randint(
                        settings.number_of_swaps.from_, settings.number_of_swaps.to_),
                )
                
                db.insert(wallet_instance)
                imported.append(wallet_instance)

        logger.success(f'Done! imported wallets: {len(imported)}/{total}; '
                       f'edited wallets: {len(edited)}/{total}; total: {total}')
