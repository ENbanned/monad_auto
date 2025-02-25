import aiohttp
import time
import hmac
import hashlib
from typing import Optional, Union, Dict, Any, List
from urllib.parse import urlencode, quote
from dataclasses import dataclass


class WithdrawError(Exception):
    pass


class NetworkError(Exception):
    pass


@dataclass
class WithdrawResponse:
    id: str
    status: str


class MexcAssistant:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        secret_key: str,
        recv_window: int = 5000
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.secret_key = secret_key
        self.recv_window = recv_window


    def _get_timestamp(self) -> str:
        return str(int(time.time() * 1000))


    def _get_signature(self, sign_params: Dict[str, Any], req_time: str) -> str:
        if sign_params:
            sign_params = urlencode(sign_params, quote_via=quote)
            to_sign = f"{sign_params}&timestamp={req_time}"
        else:
            to_sign = f"timestamp={req_time}"
        
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature


    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:

        req_time = self._get_timestamp()
        signature = self._get_signature(params, req_time)
        
        params['timestamp'] = req_time
        params['signature'] = signature

        url = f"{self.base_url}{endpoint}"
        headers = {
            'X-MEXC-APIKEY': self.api_key,
            'Content-Type': 'application/json',
        }

        try:
            async with aiohttp.ClientSession() as session:
                if method == 'GET':
                    async with session.get(url, headers=headers, params=params) as response:
                        response_text = await response.text()
                        if response.status != 200:
                            raise WithdrawError(f"API error {response.status}: {response_text}")
                        return await response.json()
                else:
                    async with session.post(url, headers=headers, params=params) as response:
                        response_text = await response.text()
                        if response.status != 200:
                            raise WithdrawError(f"API error {response.status}: {response_text}")
                        return await response.json()

        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error: {str(e)}")


    async def withdraw(
        self,
        coin: str,
        amount: Union[int, float],
        address: str,
        network: str,
        memo: Optional[str] = None,
        remark: Optional[str] = None,
        withdraw_order_id: Optional[str] = None
    ) -> WithdrawResponse:
        
        params = {
            'coin': coin,
            'amount': str(amount),
            'address': address,
            'network': network 
        }

        if memo:
            params['memo'] = memo
        if remark:
            params['remark'] = remark
        if withdraw_order_id:
            params['withdrawOrderId'] = withdraw_order_id

        try:
            result = await self._make_request(
                'POST',
                '/api/v3/capital/withdraw/apply',
                params
            )
            
            return WithdrawResponse(
                id=result.get('id'),
                status='SUCCESS'
            )
            
        except Exception as e:
            raise WithdrawError(f"Withdraw failed: {str(e)}")


    async def get_withdraw_history(
        self,
        coin: Optional[str] = None,
        status: Optional[int] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        params = {
            'offset': offset,
            'limit': limit
        }
        
        if coin:
            params['coin'] = coin
        if status is not None:
            params['status'] = status
            
        try:
            result = await self._make_request(
                'GET',
                '/api/v3/capital/withdraw/history',
                params
            )
            return result
        except Exception as e:
            raise NetworkError(f"Failed to get withdraw history: {str(e)}")
     
            
    async def get_account_info(self) -> Dict[str, Any]:
        try:
            result = await self._make_request(
                'GET',
                '/api/v3/account',
                {}
            )
            return result
        except Exception as e:
            raise NetworkError(f"Failed to get account info: {str(e)}")
    
            
    async def get_asset_balances(self, coin: Optional[str] = None) -> List[Dict[str, Any]]:
        account_info = await self.get_account_info()
        balances = account_info.get('balances', [])
        
        if coin:
            return [balance for balance in balances if balance.get('asset') == coin]
        return balances