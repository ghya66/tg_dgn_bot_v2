"""
TRON 区块链 API 统一客户端

支持 TronScan 和 TronGrid 两种数据源，提供：
- 地址余额查询（TRX + USDT）
- 最近交易记录
- 浏览器链接生成
"""

import logging
from typing import Optional, Dict, List
from dataclasses import dataclass

from src.config import settings
from src.common.http_client import get_async_client

logger = logging.getLogger(__name__)

# USDT 合约地址
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"


@dataclass
class AddressInfo:
    """地址信息数据类"""
    address: str
    trx_balance: float
    usdt_balance: float
    recent_txs: List[Dict]
    
    def format_trx(self) -> str:
        return f"{self.trx_balance:.2f}"
    
    def format_usdt(self) -> str:
        return f"{self.usdt_balance:.2f}"


class TronAPIClient:
    """TRON API 统一客户端"""
    
    def __init__(self):
        """初始化客户端"""
        self.api_url = getattr(settings, 'tron_api_url', '')
        self.api_key = getattr(settings, 'tron_api_key', None)
        self.explorer = getattr(settings, 'tron_explorer', 'tronscan')
        self.timeout = getattr(settings, 'tron_timeout_secs', 10)
    
    async def get_address_info(self, address: str) -> Optional[AddressInfo]:
        """
        获取地址信息（余额 + 交易记录）
        
        Args:
            address: TRON 地址
            
        Returns:
            AddressInfo 或 None
        """
        try:
            client = await get_async_client()
            
            # 根据配置选择 API
            if self.explorer == 'tronscan' or 'tronscan' in self.api_url:
                return await self._fetch_from_tronscan(client, address)
            else:
                return await self._fetch_from_trongrid(client, address)
                
        except Exception as e:
            logger.error(f"获取地址信息失败: {e}", exc_info=True)
            return None
    
    async def _fetch_from_tronscan(self, client, address: str) -> Optional[AddressInfo]:
        """使用 TronScan API 获取地址信息"""
        base_url = self.api_url or 'https://apilist.tronscanapi.com'
        
        headers = {'Accept': 'application/json'}
        if self.api_key and self.api_key.strip():
            headers['TRON-PRO-API-KEY'] = self.api_key.strip()
        
        # 1. 获取账户信息
        account_url = f"{base_url}/api/accountv2"
        params = {'address': address}
        
        logger.info(f"请求 TronScan API: {account_url}")
        response = await client.get(account_url, headers=headers, params=params, timeout=self.timeout)
        
        if response.status_code != 200:
            logger.error(f"TronScan API 失败: {response.status_code}")
            return None
        
        data = response.json()
        
        # 解析余额
        trx_balance = self._parse_trx_balance(data)
        usdt_balance = self._parse_usdt_balance(data)
        
        # 2. 获取最近交易
        recent_txs = await self._fetch_tronscan_transactions(client, address, headers)
        
        return AddressInfo(
            address=address,
            trx_balance=trx_balance,
            usdt_balance=usdt_balance,
            recent_txs=recent_txs
        )
    
    async def _fetch_tronscan_transactions(self, client, address: str, headers: dict) -> List[Dict]:
        """获取 TronScan 交易记录"""
        try:
            base_url = self.api_url or 'https://apilist.tronscanapi.com'
            tx_url = f"{base_url}/api/transaction"
            params = {
                'address': address,
                'limit': 5,
                'sort': '-timestamp'
            }
            
            response = await client.get(tx_url, headers=headers, params=params, timeout=self.timeout)
            
            if response.status_code != 200:
                logger.warning(f"获取交易记录失败: {response.status_code}")
                return []
            
            data = response.json()
            txs = data.get('data', [])
            
            result = []
            for tx in txs[:5]:
                # 解析交易方向
                from_addr = tx.get('ownerAddress', '')
                to_addr = tx.get('toAddress', '')
                
                if from_addr == address:
                    direction = "📤 发送"
                elif to_addr == address:
                    direction = "📥 接收"
                else:
                    direction = "🔄 其他"
                
                # 解析金额
                amount = 0
                token = "TRX"
                contract_type = tx.get('contractType', 0)
                
                if contract_type == 1:  # TRX 转账
                    amount = tx.get('amount', 0) / 1_000_000
                    token = "TRX"
                elif contract_type == 31:  # TRC20 转账
                    trigger_info = tx.get('trigger_info', {})
                    amount = float(trigger_info.get('parameter', {}).get('_value', 0)) / 1_000_000
                    token = trigger_info.get('tokenInfo', {}).get('tokenAbbr', 'Token')
                
                # 解析时间
                timestamp = tx.get('timestamp', 0)
                from datetime import datetime
                time_str = datetime.fromtimestamp(timestamp / 1000).strftime('%m-%d %H:%M') if timestamp else ''
                
                result.append({
                    'direction': direction,
                    'amount': f"{amount:.2f}",
                    'token': token,
                    'hash': tx.get('hash', ''),
                    'time': time_str
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取交易记录异常: {e}")
            return []
    
    async def _fetch_from_trongrid(self, client, address: str) -> Optional[AddressInfo]:
        """使用 TronGrid API 获取地址信息"""
        base_url = self.api_url or 'https://api.trongrid.io'
        
        headers = {'Accept': 'application/json'}
        if self.api_key and self.api_key.strip():
            headers['TRON-PRO-API-KEY'] = self.api_key.strip()
        
        account_url = f"{base_url}/v1/accounts/{address}"
        
        response = await client.get(account_url, headers=headers, timeout=self.timeout)
        
        if response.status_code == 401 and self.api_key:
            logger.warning("API 密钥无效，尝试公共 API")
            headers.pop('TRON-PRO-API-KEY', None)
            response = await client.get(account_url, headers=headers, timeout=self.timeout)
        
        if response.status_code != 200:
            logger.error(f"TronGrid API 失败: {response.status_code}")
            return None
        
        data = response.json()
        account_data = data.get('data', [{}])[0] if data.get('data') else {}
        
        # TRX 余额
        trx_balance = 0
        try:
            trx_balance = int(account_data.get('balance', 0)) / 1_000_000
        except (ValueError, TypeError):
            pass
        
        # USDT 余额
        usdt_balance = 0
        for token in account_data.get('trc20', []):
            if USDT_CONTRACT in str(token):
                try:
                    token_value = token.get(list(token.keys())[0], '0')
                    usdt_balance = int(token_value) / 1_000_000
                except (ValueError, TypeError):
                    pass
                break
        
        return AddressInfo(
            address=address,
            trx_balance=trx_balance,
            usdt_balance=usdt_balance,
            recent_txs=[]  # TronGrid 不支持交易列表
        )
    
    def _parse_trx_balance(self, data: dict) -> float:
        """解析 TRX 余额"""
        # 尝试从 balances 数组获取
        for bal in data.get('balances', []):
            if bal.get('tokenId') == '_':
                try:
                    return float(bal.get('balance', 0)) / 1_000_000
                except (ValueError, TypeError):
                    pass
        
        # 尝试直接读取 balance 字段
        try:
            return float(data.get('balance', 0)) / 1_000_000
        except (ValueError, TypeError):
            return 0
    
    def _parse_usdt_balance(self, data: dict) -> float:
        """解析 USDT 余额"""
        tokens = data.get('withPriceTokens', []) or data.get('tokens', [])
        for token in tokens:
            if token.get('tokenId') == USDT_CONTRACT:
                try:
                    return float(token.get('balance', 0)) / 1_000_000
                except (ValueError, TypeError):
                    pass
        return 0
    
    @staticmethod
    def get_explorer_links(address: str) -> Dict[str, str]:
        """
        生成区块链浏览器链接
        
        Args:
            address: TRON 地址
            
        Returns:
            包含 overview 和 txs 链接的字典
        """
        explorer = getattr(settings, 'tron_explorer', 'tronscan').lower()
        
        if explorer == 'oklink':
            base_url = "https://www.oklink.com/zh-hans/trx"
            return {
                "overview": f"{base_url}/address/{address}",
                "txs": f"{base_url}/address/{address}/transaction"
            }
        else:  # tronscan (default)
            base_url = "https://tronscan.org/#"
            return {
                "overview": f"{base_url}/address/{address}",
                "txs": f"{base_url}/address/{address}/transfers"
            }
