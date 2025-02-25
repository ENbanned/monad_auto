import asyncio
import random
from typing import List, Tuple
from loguru import logger

from data.models import Settings
from functions.wallets_loader import load_wallets
from utils.mexc_helper import MexcAssistant, WithdrawError, NetworkError


async def run_mexc_withdraw(wallet_names: List[str], amount_range: Tuple[float, float]) -> None:
    settings = Settings()
    
    if not settings.mexc_api_key or not settings.mexc_secret_key:
        logger.error('Не указаны API ключ и секретный ключ MEXC!')
        return
    
    all_wallets = load_wallets()
    
    selected_wallets = []
    for wallet in all_wallets:
        if wallet.get('name', '') in wallet_names:
            selected_wallets.append(wallet)
            
    if not selected_wallets:
        logger.error(f"Кошельки с указанными именами не найдены: {', '.join(wallet_names)}")
        return
        
    logger.info(f"Найдено {len(selected_wallets)} кошельков для вывода")
    
    wallets_without_address = []
    for wallet in selected_wallets:
        wallet_name = wallet.get('name', 'Неизвестный')
        wallet_address = wallet.get('address', '')
        
        if not wallet_address and 'private_key' in wallet:
            from evm import EVMClient, Networks
            try:
                client = EVMClient(
                    private_key=wallet['private_key'],
                    network=Networks.ARBITRUM
                )
                wallet['address'] = client.account.address
            except Exception as e:
                logger.error(f"Не удалось получить адрес для кошелька {wallet_name}: {e}")
                wallets_without_address.append(wallet_name)
        elif not wallet_address:
            wallets_without_address.append(wallet_name)
            
    if wallets_without_address:
        logger.error(f"Следующие кошельки не имеют адреса: {', '.join(wallets_without_address)}")
        return
    
    helper = MexcAssistant(
        base_url='https://api.mexc.com',
        api_key=settings.mexc_api_key,
        secret_key=settings.mexc_secret_key
    )
    
    for wallet in selected_wallets:
        try:
            min_amount, max_amount = amount_range
            amount = round(random.uniform(min_amount, max_amount), 8)
            
            wallet_name = wallet.get('name', 'Неизвестный')
            wallet_address = wallet.get('address', '')
            
            if not wallet_address and 'private_key' in wallet:
                from evm import EVMClient, Networks
                try:
                    client = EVMClient(
                        private_key=wallet['private_key'],
                        network=Networks.ARBITRUM
                    )
                    wallet_address = client.account.address
                except Exception as e:
                    logger.error(f"Не удалось получить адрес для кошелька {wallet_name}: {e}")
                    continue
            
            if not wallet_address:
                logger.error(f"Не указан адрес для кошелька {wallet_name}")
                continue
                
            logger.info(f"Выполняю вывод {amount} ETH на кошелек {wallet_name} ({wallet_address})")
            
            result = await helper.withdraw(
                coin='ETH',
                amount=amount,
                address=wallet_address,
                network='Arbitrum One(ARB)'
            )
            
            logger.success(f"Успешный вывод на {wallet_name}: {amount} ETH. ID транзакции: {result.id}")
            
            delay = random.uniform(5, 10)
            logger.info(f"Ожидание {delay:.2f} секунд перед следующим выводом...")
            await asyncio.sleep(delay)
            
        except (WithdrawError, NetworkError) as e:
            logger.error(f"Ошибка при выводе на кошелек {wallet.get('name', 'Неизвестный')}: {str(e)}")
            logger.info("Ожидание 30 секунд перед следующей попыткой...")
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при выводе на кошелек {wallet.get('name', 'Неизвестный')}: {str(e)}")
            await asyncio.sleep(5)


async def process_mexc_withdraw():
    try:
        all_wallets = load_wallets()
        available_wallet_names = [wallet.get('name', '') for wallet in all_wallets]
        
        logger.info(f"Доступные кошельки: {', '.join(available_wallet_names) if available_wallet_names else 'кошельки не найдены'}")
        
        wallet_names_input = input("Введите имена кошельков через пробел (например: acc1 acc2 acc3) или 'all' для выбора всех кошельков: ")
        if wallet_names_input.strip().lower() == 'all':
            wallet_names = available_wallet_names
            logger.info(f"Выбраны все {len(available_wallet_names)} доступных кошельков.")
        else:
            wallet_names = [name.strip() for name in wallet_names_input.split() if name.strip()]
        
        if not wallet_names:
            logger.error("Не указаны имена кошельков")
            return
            
        non_existent_wallets = [name for name in wallet_names if name not in available_wallet_names]
        if non_existent_wallets:
            logger.error(f"Следующие кошельки не найдены: {', '.join(non_existent_wallets)}")
            return
            
        amount_range_input = input("Введите диапазон сумм для вывода ETH (например: 0.001-0.002). МИНИМАЛЬНО: 0.001: ")
        
        try:
            min_str, max_str = amount_range_input.split('-')
            min_amount = float(min_str.strip())
            max_amount = float(max_str.strip())
            
            if min_amount <= 0 or max_amount <= 0:
                logger.error("Суммы должны быть положительными")
                return
                
            if min_amount >= max_amount:
                logger.error("Минимальная сумма должна быть меньше максимальной")
                return
                
        except ValueError:
            logger.error("Неверный формат диапазона. Используйте формат 'мин-макс', например: 0.001-0.002")
            return
        
        confirmation = input(f"Будет выполнен вывод ETH на {len(wallet_names)} кошельков в диапазоне {min_amount}-{max_amount} ETH. Продолжить? (y/n): ")
        if confirmation.lower() != 'y':
            logger.info("Операция отменена пользователем")
            return
            
        await run_mexc_withdraw(wallet_names, (min_amount, max_amount))
        
    except KeyboardInterrupt:
        logger.info("Операция отменена пользователем")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        