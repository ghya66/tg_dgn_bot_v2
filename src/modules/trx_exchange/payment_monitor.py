"""
USDT 支付监听服务

监听收款地址的 USDT 转入，自动匹配订单并发送 TRX
"""

import asyncio
import logging
from collections import deque
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from src.common.db_manager import get_db_context_manual_commit
from src.common.error_collector import collect_error
from src.common.http_client import get_async_client
from src.config import settings

from .models import TRXExchangeOrder
from .trx_sender import TRXSender


# 避免循环导入
if TYPE_CHECKING:
    from telegram import Bot

logger = logging.getLogger(__name__)

# USDT 合约地址
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"

# 已处理交易哈希的最大缓存数量
# 按每30秒轮询一次、每次最多20笔交易计算，10000条可覆盖约4小时的交易
MAX_PROCESSED_TX_CACHE = 10000


class PaymentMonitor:
    """USDT 支付监听器"""

    def __init__(self):
        """初始化监听器"""
        self.receive_address = getattr(settings, "trx_exchange_receive_address", "")
        self.api_url = getattr(settings, "tron_api_url", "https://apilist.tronscanapi.com")
        self.api_key = getattr(settings, "tron_api_key", "")
        self.trx_sender = TRXSender()
        self.running = False
        self.poll_interval = 30  # 轮询间隔（秒）
        self._last_check_time = None
        # 使用 deque 限制已处理交易哈希的缓存大小，防止内存泄漏
        # 当达到 maxlen 时，最旧的元素会被自动移除
        self._processed_tx_hashes: deque = deque(maxlen=MAX_PROCESSED_TX_CACHE)
        # 使用 set 进行 O(1) 查找，与 deque 同步维护
        self._processed_tx_set: set = set()
        # Bot 实例，用于发送用户通知
        self._bot: Bot | None = None

    def set_bot(self, bot: "Bot") -> None:
        """
        设置 Bot 实例用于发送用户通知

        Args:
            bot: Telegram Bot 实例
        """
        self._bot = bot
        logger.info("PaymentMonitor: Bot 实例已设置，用户通知功能已启用")

    def _is_tx_processed(self, tx_hash: str) -> bool:
        """检查交易是否已处理（O(1) 查找）"""
        return tx_hash in self._processed_tx_set

    def _add_processed_tx(self, tx_hash: str) -> None:
        """
        添加已处理的交易哈希

        同时维护 deque 和 set，当 deque 达到 maxlen 时，
        最旧的元素会被自动移除，同时从 set 中删除
        """
        if tx_hash in self._processed_tx_set:
            return

        # 如果 deque 已满，移除最旧的元素
        if len(self._processed_tx_hashes) >= MAX_PROCESSED_TX_CACHE:
            oldest_tx = self._processed_tx_hashes[0]  # 最旧的元素
            self._processed_tx_set.discard(oldest_tx)

        # 添加新元素
        self._processed_tx_hashes.append(tx_hash)
        self._processed_tx_set.add(tx_hash)

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
                collect_error("trx_payment_monitor", f"检查支付时出错: {e}", exception=e)

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

    async def _fetch_usdt_transfers(self) -> list[dict]:
        """获取 USDT 转账记录"""
        try:
            client = await get_async_client()

            # TronScan TRC20 转账 API
            url = f"{self.api_url}/api/token_trc20/transfers"
            params = {
                "relatedAddress": self.receive_address,
                "contract_address": USDT_CONTRACT,
                "limit": 20,
                "order_by": "-timestamp",
            }

            headers = {"Accept": "application/json"}
            if self.api_key:
                headers["TRON-PRO-API-KEY"] = self.api_key

            response = await client.get(url, params=params, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"获取转账记录失败: {response.status_code}")
                return []

            data = response.json()

            # 只返回转入的交易（to_address 是收款地址）
            transfers = []
            for item in data.get("token_transfers", []):
                if item.get("to_address") == self.receive_address:
                    transfers.append(item)

            return transfers

        except Exception as e:
            logger.error(f"获取转账记录异常: {e}")
            collect_error("trx_fetch_transfers", str(e), exception=e)
            return []

    async def _process_transfer(self, tx: dict):
        """处理单笔转账"""
        tx_hash = tx.get("transaction_id", "")

        # 跳过已处理的交易（使用 O(1) 查找）
        if self._is_tx_processed(tx_hash):
            return

        # 解析金额（USDT 6位精度）
        try:
            amount_raw = int(tx.get("quant", 0))
            amount = Decimal(amount_raw) / Decimal("1000000")
        except (ValueError, TypeError):
            return

        if amount <= 0:
            return

        logger.info(f"检测到 USDT 转入: {amount} USDT, tx: {tx_hash[:16]}...")

        # 匹配订单 - 使用手动提交的上下文管理器确保连接正确关闭
        with get_db_context_manual_commit() as db:
            try:
                order = await self._match_order(db, amount)

                if not order:
                    logger.warning(f"未找到匹配订单: {amount} USDT")
                    self._add_processed_tx(tx_hash)
                    return

                logger.info(f"匹配到订单: {order.order_id}, 金额: {order.usdt_amount}")

                # 更新订单状态
                order.status = "PAID"
                order.tx_hash = tx_hash
                order.paid_at = datetime.now(UTC)
                db.commit()

                # 自动发送 TRX
                await self._send_trx(db, order)

                # 标记已处理
                self._add_processed_tx(tx_hash)

            except Exception as e:
                logger.error(f"处理转账失败: {e}", exc_info=True)
                db.rollback()

    async def _match_order(self, db: Session, amount: Decimal) -> TRXExchangeOrder | None:
        """
        根据金额匹配订单

        使用唯一金额（3位小数后缀）进行精确匹配
        """
        # 查找 PENDING 状态且金额匹配的订单
        order = (
            db.query(TRXExchangeOrder)
            .filter(
                TRXExchangeOrder.status == "PENDING",
                TRXExchangeOrder.usdt_amount == amount,
            )
            .order_by(TRXExchangeOrder.created_at.desc())
            .first()
        )

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
            order.completed_at = datetime.now(UTC)
            db.commit()

            logger.info(f"订单 {order.order_id} 已完成，TRX 发送哈希: {send_tx_hash}")

            # 通知用户发货成功
            await self._notify_user_success(order, send_tx_hash)

        except Exception as e:
            logger.error(f"发送 TRX 失败 (订单 {order.order_id}): {e}", exc_info=True)
            order.status = "SEND_FAILED"
            order.error_message = str(e)
            db.commit()
            # 通知用户发货失败
            await self._notify_user_failure(order, str(e))

    async def _notify_user_success(self, order: TRXExchangeOrder, tx_hash: str):
        """
        发送 TRX 发货成功通知给用户

        Args:
            order: 订单对象
            tx_hash: 发送交易哈希
        """
        if not self._bot:
            logger.warning(f"无法发送通知：Bot 实例未设置 (订单: {order.order_id})")
            return

        # 构建通知消息
        message = (
            "✅ <b>TRX 发货成功</b>\n\n"
            f"📦 订单号: <code>{order.order_id}</code>\n"
            f"💰 发送金额: <b>{order.trx_amount} TRX</b>\n"
            f"📍 收款地址: <code>{order.recipient_address[:8]}...{order.recipient_address[-6:]}</code>\n"
            f'🔗 交易哈希: <a href="https://tronscan.org/#/transaction/{tx_hash}">{tx_hash[:16]}...</a>\n\n'
            "感谢您的使用！"
        )

        try:
            await self._bot.send_message(
                chat_id=order.user_id, text=message, parse_mode="HTML", disable_web_page_preview=True
            )
            logger.info(f"已发送 TRX 发货成功通知给用户 {order.user_id} (订单: {order.order_id})")
        except Exception as e:
            logger.error(f"发送成功通知失败 (订单: {order.order_id}): {e}")
            collect_error("trx_notify_success", str(e), exception=e)

    async def _notify_user_failure(self, order: TRXExchangeOrder, error_msg: str):
        """
        发送 TRX 发货失败通知给用户

        Args:
            order: 订单对象
            error_msg: 错误信息
        """
        if not self._bot:
            logger.warning(f"无法发送通知：Bot 实例未设置 (订单: {order.order_id})")
            return

        # 构建通知消息
        message = (
            "❌ <b>TRX 发货失败</b>\n\n"
            f"📦 订单号: <code>{order.order_id}</code>\n"
            f"💰 应发金额: <b>{order.trx_amount} TRX</b>\n\n"
            "⚠️ 您的付款已收到，但 TRX 发送失败。\n"
            "请联系客服处理，我们会尽快为您解决。\n\n"
            "抱歉给您带来不便！"
        )

        try:
            await self._bot.send_message(chat_id=order.user_id, text=message, parse_mode="HTML")
            logger.info(f"已发送 TRX 发货失败通知给用户 {order.user_id} (订单: {order.order_id})")
        except Exception as e:
            logger.error(f"发送失败通知失败 (订单: {order.order_id}): {e}")
            collect_error("trx_notify_failure", str(e), exception=e)


# 全局监听器实例
_monitor: PaymentMonitor | None = None


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
