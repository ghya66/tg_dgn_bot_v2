"""
USDT 支付监听服务

监听收款地址的 USDT 转入，自动匹配订单并发送 TRX
"""

import logging
import asyncio
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, Dict, List

from sqlalchemy.orm import Session

from src.config import settings
from src.database import SessionLocal
from .models import TRXExchangeOrder
from src.common.http_client import get_async_client
from .trx_sender import TRXSender
from src.common.error_collector import collect_error

logger = logging.getLogger(__name__)

# USDT 合约地址
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"


class PaymentMonitor:
    """USDT 支付监听器"""
    
    def __init__(self):
        """初始化监听器"""
        self.receive_address = getattr(settings, 'trx_exchange_receive_address', '')
        self.api_url = getattr(settings, 'tron_api_url', 'https://apilist.tronscanapi.com')
        self.api_key = getattr(settings, 'tron_api_key', '')
        self.trx_sender = TRXSender()
        self.running = False
        self.poll_interval = 30  # 轮询间隔（秒）
        self._last_check_time = None
        self._processed_tx_hashes = set()  # 已处理的交易哈希
    
    async def start(self):
        """启动监听服务"""
        if not self.receive_address:
            logger.error("收款地址未配置，无法启动监听服务")
            return
        
        self.running = True
        logger.info(f"启动 USDT 支付监听服务，收款地址: {self.receive_address}")
        
        while self.running:
            try:
                await self._check_payments()
            except Exception as e:
                logger.error(f"检查支付时出错: {e}", exc_info=True)
                collect_error(
                    "trx_payment_monitor",
                    f"检查支付时出错: {e}",
                    exception=e
                )
            
            await asyncio.sleep(self.poll_interval)
    
    def stop(self):
        """停止监听服务"""
        self.running = False
        logger.info("停止 USDT 支付监听服务")
    
    async def _check_payments(self):
        """检查新的 USDT 转入"""
        try:
            # 获取最近的 TRC20 转账
            transfers = await self._fetch_usdt_transfers()
            
            if not transfers:
                return
            
            logger.debug(f"获取到 {len(transfers)} 笔 USDT 转账")
            
            for tx in transfers:
                await self._process_transfer(tx)
                
        except Exception as e:
            logger.error(f"检查支付失败: {e}", exc_info=True)
            collect_error("trx_check_payments", str(e), exception=e)
    
    async def _fetch_usdt_transfers(self) -> List[Dict]:
        """获取 USDT 转账记录"""
        try:
            client = await get_async_client()
            
            # TronScan TRC20 转账 API
            url = f"{self.api_url}/api/token_trc20/transfers"
            params = {
                'relatedAddress': self.receive_address,
                'contract_address': USDT_CONTRACT,
                'limit': 20,
                'order_by': '-timestamp',
            }
            
            headers = {'Accept': 'application/json'}
            if self.api_key:
                headers['TRON-PRO-API-KEY'] = self.api_key
            
            response = await client.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"获取转账记录失败: {response.status_code}")
                return []
            
            data = response.json()
            
            # 只返回转入的交易（to_address 是收款地址）
            transfers = []
            for item in data.get('token_transfers', []):
                if item.get('to_address') == self.receive_address:
                    transfers.append(item)
            
            return transfers
            
        except Exception as e:
            logger.error(f"获取转账记录异常: {e}")
            collect_error("trx_fetch_transfers", str(e), exception=e)
            return []
    
    async def _process_transfer(self, tx: Dict):
        """处理单笔转账"""
        tx_hash = tx.get('transaction_id', '')
        
        # 跳过已处理的交易
        if tx_hash in self._processed_tx_hashes:
            return
        
        # 解析金额（USDT 6位精度）
        try:
            amount_raw = int(tx.get('quant', 0))
            amount = Decimal(amount_raw) / Decimal('1000000')
        except (ValueError, TypeError):
            return
        
        if amount <= 0:
            return
        
        logger.info(f"检测到 USDT 转入: {amount} USDT, tx: {tx_hash[:16]}...")
        
        # 匹配订单
        db: Session = SessionLocal()
        try:
            order = await self._match_order(db, amount)
            
            if not order:
                logger.warning(f"未找到匹配订单: {amount} USDT")
                self._processed_tx_hashes.add(tx_hash)
                return
            
            logger.info(f"匹配到订单: {order.order_id}, 金额: {order.usdt_amount}")
            
            # 更新订单状态
            order.status = "PAID"
            order.tx_hash = tx_hash
            order.paid_at = datetime.now(timezone.utc)
            db.commit()
            
            # 自动发送 TRX
            await self._send_trx(db, order)
            
            # 标记已处理
            self._processed_tx_hashes.add(tx_hash)
            
        except Exception as e:
            logger.error(f"处理转账失败: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()
    
    async def _match_order(self, db: Session, amount: Decimal) -> Optional[TRXExchangeOrder]:
        """
        根据金额匹配订单
        
        使用唯一金额（3位小数后缀）进行精确匹配
        """
        # 查找 PENDING 状态且金额匹配的订单
        order = db.query(TRXExchangeOrder).filter(
            TRXExchangeOrder.status == "PENDING",
            TRXExchangeOrder.usdt_amount == amount,
        ).order_by(TRXExchangeOrder.created_at.desc()).first()
        
        return order
    
    async def _send_trx(self, db: Session, order: TRXExchangeOrder):
        """自动发送 TRX"""
        try:
            order.status = "PROCESSING"
            db.commit()
            
            # 发送 TRX
            send_tx_hash = self.trx_sender.send_trx(
                recipient_address=order.recipient_address,
                amount=order.trx_amount,
                order_id=order.order_id,
            )
            
            # 更新订单状态
            order.status = "COMPLETED"
            order.send_tx_hash = send_tx_hash
            order.completed_at = datetime.now(timezone.utc)
            db.commit()
            
            logger.info(f"订单 {order.order_id} 已完成，TRX 发送哈希: {send_tx_hash}")
            
            # TODO: 通知用户（需要 bot 实例）
            
        except Exception as e:
            logger.error(f"发送 TRX 失败 (订单 {order.order_id}): {e}", exc_info=True)
            order.status = "SEND_FAILED"
            order.error_message = str(e)
            db.commit()


# 全局监听器实例
_monitor: Optional[PaymentMonitor] = None


def get_monitor() -> PaymentMonitor:
    """获取监听器实例"""
    global _monitor
    if _monitor is None:
        _monitor = PaymentMonitor()
    return _monitor


async def start_payment_monitor():
    """启动支付监听（在 bot 启动时调用）"""
    monitor = get_monitor()
    asyncio.create_task(monitor.start())


def stop_payment_monitor():
    """停止支付监听"""
    if _monitor:
        _monitor.stop()
