import asyncio
import random
import requests
import json
import time
import hashlib
import platform
from typing import Optional, Dict, Any
from loguru import logger

from evm import EVMClient, Networks
from data.models import Settings
from fake_useragent import UserAgent


class VisitorIdGenerator:
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        return {
            "platform": platform.system(),
            "architecture": platform.machine(),
            "version": platform.version(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "node": platform.node(),
            "timestamp": str(time.time()),
            "random": str(random.random())
        }

    @staticmethod
    def generate() -> str:
        system_info = VisitorIdGenerator.get_system_info()
        info_str = json.dumps(system_info, sort_keys=True)
        hash_object = hashlib.md5(info_str.encode())
        return hash_object.hexdigest()[:32]


class CapsolverClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.capsolver.com"

    def create_task(self, website_url: str, website_key: str) -> Dict[str, Any]:
        data = {
            "clientKey": self.api_key,
            "task": {
                "type": "ReCaptchaV2TaskProxyless",
                "websiteURL": website_url,
                "websiteKey": website_key,
                "isInvisible": True,
                "userAgent": UserAgent().chrome
            }
        }

        response = requests.post(f"{self.base_url}/createTask", json=data)
        response.raise_for_status()
        
        return response.json()


    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        data = {
            "clientKey": self.api_key,
            "taskId": task_id
        }

        response = requests.post(f"{self.base_url}/getTaskResult", json=data)
        response.raise_for_status()
        
        return response.json()


    def solve_captcha(self, website_url: str, website_key: str, max_attempts: int = 10) -> str:
        task = self.create_task(website_url, website_key)
        task_id = task.get("taskId")

        if not task_id:
            raise Exception("Не удалось создать задачу")

        for _ in range(max_attempts):
            result = self.get_task_result(task_id)
            status = result.get("status")

            if status == "ready":
                return result["solution"]["gRecaptchaResponse"]
            elif status == "failed":
                raise Exception(f"Не удалось решить капчу: {result.get('errorDescription')}")

            time.sleep(3)

        raise Exception("Превышено время ожидания решения капчи")


class MonadFaucet:
    def __init__(self, capsolver_api_key: str, proxy: Optional[str] = None):
        self.base_url = "https://testnet.monad.xyz"
        self.capsolver = CapsolverClient(capsolver_api_key)
        self.visitor_id = VisitorIdGenerator.generate()
        self.proxy = proxy
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://testnet.monad.xyz',
            'referer': 'https://testnet.monad.xyz/',
            'sec-ch-ua': '"Chromium";v="121", "Google Chrome";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': UserAgent().chrome
        }
        self.session = requests.Session()


    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"

        proxies = None
        if self.proxy:
            if not self.proxy.startswith('http'):
                proxy_str = f'http://{self.proxy}'
            else:
                proxy_str = self.proxy

            proxies = {
                'http': proxy_str,
                'https': proxy_str
            }

        response = self.session.request(
            method=method,
            url=url,
            headers=self.headers,
            json=data,
            proxies=proxies
        )

        if not response.ok:
            try:
                err_json = response.json()
                raise requests.HTTPError(
                    f"{response.status_code} {response.reason} | {err_json}",
                    response=response
                )
            except:
                response.raise_for_status()

        return response.json()


    def get_recaptcha_token(self) -> str:
        website_url = "https://testnet.monad.xyz"
        website_key = "6LdOf-EqAAAAAAKJ2QB6IqnJfsOl13El4XZwRD8c"

        token = self.capsolver.solve_captcha(website_url, website_key)
        return token


    def claim_tokens(self, address: str) -> Dict[str, Any]:
        data = {
            "address": address,
            "visitorId": self.visitor_id,
            "recaptchaToken": self.get_recaptcha_token()
        }

        result = self._make_request("POST", "/api/claim", data)
        return result


    def claim_with_retry(self, address: str) -> Dict[str, Any]:
        max_attempts = 10
        attempts = 0

        while True:
            try:
                return self.claim_tokens(address)

            except Exception as e:
                attempts += 1
                error_text = str(e)
                
                if '"message": "reCAPTCHA score too low"' in error_text:
                    if max_attempts < 20:
                        logger.warning("Ошибка: reCAPTCHA score too low. Увеличиваем попытки до 20.")
                        max_attempts = 20

                if attempts >= max_attempts:
                    raise Exception(
                        f"Не удалось получить токены после {max_attempts} попыток.\n"
                        f"Последняя ошибка: {error_text}"
                    )

                delay_time = random.uniform(2, 5)
                logger.info(f"Попытка #{attempts} не удалась, ждём {delay_time:.1f}с, visitorId обновляем.")
                time.sleep(delay_time)
                self.visitor_id = VisitorIdGenerator.generate()


class FaucetClaim:
    async def claim(self, wallet):
        wallet_name = wallet.get('name')

        settings = Settings()

        if not settings.capsolver_api_key:
            logger.error(f"Кошелёк {wallet_name}: Не указан API ключ Capsolver. Клейм пропущен.")
            return

        proxy = wallet.get('proxy')
        if not proxy:
            logger.error(f"Кошелёк {wallet_name}: Не указан прокси. Клейм пропущен.")
            return

        try:
            client = EVMClient(
                private_key=wallet.get('private_key', ''),
                network=Networks.MONAD
            )
            address = client.account.address
        except Exception as e:
            logger.error(f"Кошелёк {wallet_name}: Ошибка при получении адреса: {str(e)}")
            return

        try:
            delay = random.uniform(1, 3)
            await asyncio.sleep(delay)

            logger.info(f"Кошелёк {wallet_name}: Выполняю запрос на кран...")

            faucet = MonadFaucet(
                capsolver_api_key=settings.capsolver_api_key,
                proxy=proxy
            )

            result = await asyncio.to_thread(faucet.claim_with_retry, address)
            logger.success(f"Кошелёк {wallet_name}: Успешно получены токены с крана! Результат: {result}")

        except Exception as e:
            logger.error(f"Кошелёк {wallet_name}: Ошибка при клейме: {str(e)}")
            
