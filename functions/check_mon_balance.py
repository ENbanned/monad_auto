import asyncio
import random
from loguru import logger

from evm import EVMClient, Networks


async def check_balance(wallet):
    try:
        delay = random.uniform(0.5, 1.5)
        await asyncio.sleep(delay)
        
        client = EVMClient(
            private_key=wallet['private_key'],
            network=Networks.MONAD,
            proxy=wallet.get('proxy')
        )
        
        mon_balance = await client.get_native_balance()
        
        if mon_balance:
            logger.info(f"Кошелёк {wallet['name']}: Баланс MON: {mon_balance.Ether:.6f}")
        else:
            logger.error(f"Кошелёк {wallet['name']}: Не удалось получить баланс MON")
            
    except Exception as e:
        logger.error(f"Кошелёк {wallet['name']}: Ошибка при проверке баланса: {str(e)}")
        