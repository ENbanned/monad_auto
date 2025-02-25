import asyncio
import random
import json
import os
from loguru import logger

from evm.client import EVMClient
from evm.networks import Networks

from utils.tasks.owlto import OwlTo
from utils.tasks.multpli import MultPli
from utils.tasks.aPriori import aPriori
from utils.tasks.curvance import Curvance
from utils.tasks.shmonad import Shmonad

from data.config import COMPLETED_ACTIONS


def load_completed_actions() -> dict:
    if not os.path.exists(COMPLETED_ACTIONS):
        return {}
    try:
        with open(COMPLETED_ACTIONS, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки файла {COMPLETED_ACTIONS}: {e}")
        data = {}
    return data


def save_completed_actions(data: dict):
    try:
        with open(COMPLETED_ACTIONS, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения файла {COMPLETED_ACTIONS}: {e}")


class MandatoryActions:
    def __init__(self, delay_range=(60, 120)):
        self.delay_range = delay_range
        self.protocol_tasks = [
            ("OwlTo", OwlTo, ["deploy"]),
            ("MultPli", MultPli, ["claim_and_stake"]),
            ("aPriori", aPriori, ["stake_mon"]),
            ("Curvance", Curvance, ["claim_all_tokens"]),
            ("Shmonad", Shmonad, ["stake_mon"])
        ]
    
    
    async def run(self, wallet: dict):
        """
        Выполняет обязательные действия для заданного кошелька.
        Осуществляется проверка по файлу COMPLETED_ACTIONS – если для данного кошелька и протокола действия уже выполнены, они пропускаются.
        :param wallet: Словарь с данными кошелька (например, 'private_key', 'proxy', 'name')
        """
        wallet_name = wallet.get('name', 'Unknown')
        logger.info(f"[MandatoryActions] Начало обязательных действий для кошелька {wallet_name}.")
        
        try:
            client = EVMClient(
                private_key=wallet['private_key'],
                network=Networks.MONAD,
                proxy=wallet.get('proxy')
            )
        except Exception as e:
            logger.error(f"[MandatoryActions] Ошибка создания клиента для {wallet_name}: {e}")
            return

        wallet_id = client.account.address.lower()
        completed = load_completed_actions()
        if wallet_id not in completed:
            completed[wallet_id] = {}

        tasks = self.protocol_tasks.copy()
        random.shuffle(tasks)
        
        for protocol_name, protocol_class, methods in tasks:
            if completed[wallet_id].get(protocol_name):
                logger.info(f"[MandatoryActions] Действия для протокола {protocol_name} уже выполнены для кошелька {wallet_name}. Пропускаем.")
                continue

            logger.info(f"[MandatoryActions] Запуск задач для протокола {protocol_name} для кошелька {wallet_name}.")
            try:
                protocol_instance = protocol_class(client)
                success = True
                for method_name in methods:
                    if hasattr(protocol_instance, method_name):
                        method = getattr(protocol_instance, method_name)
                        try:
                            result = await method()
                            delay = random.uniform(*self.delay_range)
                            logger.info(
                                f"[MandatoryActions] {protocol_name}.{method_name} для {wallet_name} успешно выполнено. "
                                f"Следующее действие начнется через {delay:.2f} секунд. Результат: {result}"
                            )
                        except Exception as method_error:
                            logger.error(
                                f"[MandatoryActions] Ошибка при выполнении метода {protocol_name}.{method_name} для кошелька {wallet_name}: {method_error}"
                            )
                            success = False
                        await asyncio.sleep(delay)
                    else:
                        logger.warning(f"[MandatoryActions] Протокол {protocol_name} не реализует метод {method_name}.")
                        delay = random.uniform(*self.delay_range)
                        await asyncio.sleep(delay)
                if success:
                    completed[wallet_id][protocol_name] = True
                    save_completed_actions(completed)
                    logger.info(f"[MandatoryActions] Все обязательные действия для протокола {protocol_name} выполнены для кошелька {wallet_name}.")
                else:
                    logger.error(f"[MandatoryActions] Для протокола {protocol_name} для кошелька {wallet_name} возникли ошибки – отметка не сохраняется.")
            except Exception as e:
                logger.error(f"[MandatoryActions] Ошибка выполнения задачи {protocol_name} для кошелька {wallet_name}: {e}")
        
        logger.info(f"[MandatoryActions] Завершение обязательных действий для кошелька {wallet_name}.")
