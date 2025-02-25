import asyncio
import random
from loguru import logger
from typing import Dict, Any

from evm import EVMClient, Networks
from evm.models.token import TokenAmount
from functions.wallets_loader import load_wallets
from utils.tasks.gazzip import GazZip 

async def check_wallet_balance(wallet: Dict[str, Any]) -> Dict[str, Any]:
    try:
        client = EVMClient(
            private_key=wallet['private_key'],
            network=Networks.ARBITRUM,
            proxy=wallet.get('proxy')
        )
        
        eth_balance = await client.get_native_balance()
        
        wallet_info = wallet.copy()
        wallet_info['balance'] = eth_balance
        wallet_info['client'] = client 
        
        return wallet_info
    
    except Exception as e:
        logger.error(f"Ошибка при проверке баланса кошелька {wallet.get('name', 'Неизвестный')}: {str(e)}")
        wallet_info = wallet.copy()
        wallet_info['balance'] = TokenAmount.from_ether(0)
        return wallet_info

async def process_gazzip_buy():
    all_wallets = load_wallets()
    
    if not all_wallets:
        logger.error("Кошельки не найдены. Убедитесь, что они импортированы.")
        return
    
    logger.info(f"Проверка балансов {len(all_wallets)} кошельков в сети Arbitrum...")
    
    wallet_tasks = [check_wallet_balance(wallet) for wallet in all_wallets]
    wallet_results = await asyncio.gather(*wallet_tasks)
    
    min_usd_amount = 2.0
    
    try:
        temp_client = EVMClient(
            private_key=all_wallets[0]['private_key'],
            network=Networks.ARBITRUM,
            proxy=all_wallets[0].get('proxy')
        )
        
        gazzip = GazZip(temp_client)
        eth_price = await gazzip._get_eth_price()
        min_eth_amount = min_usd_amount / eth_price
        
    except Exception as e:
        logger.error(f"Ошибка при получении цены ETH: {str(e)}")
        return e
    
    eligible_wallets = []
    for wallet_info in wallet_results:
        balance_eth = float(wallet_info['balance'].Ether) if wallet_info['balance'] else 0
        balance_usd = balance_eth * eth_price
        
        if balance_eth >= min_eth_amount:
            eligible_wallets.append({
                'name': wallet_info['name'],
                'address': wallet_info.get('address', ''),
                'balance_eth': balance_eth,
                'balance_usd': balance_usd,
                'client': wallet_info.get('client')
            })
    
    if not eligible_wallets:
        logger.error(f"Не найдено кошельков с балансом больше ${min_usd_amount} в сети Arbitrum. Пополните кошельки через MEXC или другой сервис.")
        return
    
    logger.info(f"Найдено {len(eligible_wallets)} кошельков с достаточным балансом:")
    for i, wallet in enumerate(eligible_wallets, 1):
        logger.info(f"{i}. {wallet['name']}: {wallet['balance_eth']:.8f} ETH (${wallet['balance_usd']:.2f})")
    
    wallet_names_input = input("Введите имена кошельков через пробел (например: acc1 acc2 acc3) или 'all' для выбора всех подходящих кошельков: ")
    
    selected_wallets = []
    if wallet_names_input.strip().lower() == 'all':
        selected_wallets = eligible_wallets
        logger.info(f"Выбраны все {len(eligible_wallets)} кошельков с достаточным балансом.")
    else:
        wallet_names = [name.strip() for name in wallet_names_input.split() if name.strip()]
        
        if not wallet_names:
            logger.error("Не указаны имена кошельков.")
            return
        
        eligible_names = [wallet['name'] for wallet in eligible_wallets]
        non_existent_wallets = [name for name in wallet_names if name not in eligible_names]
        
        if non_existent_wallets:
            logger.error(f"Следующие кошельки не найдены или не имеют достаточного баланса: {', '.join(non_existent_wallets)}")
            return
        
        for wallet in eligible_wallets:
            if wallet['name'] in wallet_names:
                selected_wallets.append(wallet)
    
    confirmation = input(f"Будет выполнена покупка MON на ${min_usd_amount} для {len(selected_wallets)} кошельков. Продолжить? (y/n): ")
    if confirmation.lower() != 'y':
        logger.info("Операция отменена пользователем.")
        return
    
    for wallet in selected_wallets:
        try:
            logger.info(f"Покупка MON для кошелька {wallet['name']}...")
            
            client = wallet.get('client')
            if not client:
                found_wallet = next((w for w in all_wallets if w['name'] == wallet['name']), None)
                if not found_wallet:
                    logger.error(f"Ошибка: не удалось найти данные для кошелька {wallet['name']}")
                    continue
                
                client = EVMClient(
                    private_key=found_wallet['private_key'],
                    network=Networks.ARBITRUM,
                    proxy=found_wallet.get('proxy')
                )
            
            gazzip = GazZip(client)
            result = await gazzip.buy_monad(usd_amount=min_usd_amount)
            
            logger.success(f"Результат для {wallet['name']}: {result}")
            
            delay = random.uniform(5, 10)
            logger.info(f"Ожидание {delay:.2f} секунд перед следующей операцией...")
            await asyncio.sleep(delay)
            
        except Exception as e:
            logger.error(f"Ошибка при покупке MON для кошелька {wallet['name']}: {str(e)}")
            await asyncio.sleep(5)
            