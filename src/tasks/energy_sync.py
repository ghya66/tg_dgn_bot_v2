"""
能量订单状态同步任务

定期从 trxfast.com 查询订单状态，同步到本地数据库
"""

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from src.common.db_manager import get_db_context, get_db_context_readonly
from src.common.error_collector import collect_error
from src.config import settings
from src.database import EnergyOrder as DBEnergyOrder
from src.modules.energy.client import EnergyAPIClient, EnergyAPIError


if TYPE_CHECKING:
    from telegram import Bot

logger = logging.getLogger(__name__)

# 配置常量
SYNC_INTERVAL_MINUTES = 5  # 同步间隔（分钟）
SYNC_ORDER_AGE_HOURS = 24  # 只同步最近 N 小时内的订单
MAX_ORDERS_PER_SYNC = 50  # 每次同步最大订单数


class EnergySyncTask:
    """能量订单状态同步任务"""

    def __init__(self):
        self._bot: Bot | None = None

    def set_bot(self, bot: "Bot") -> None:
        """设置 Bot 实例用于发送通知"""
        self._bot = bot
        logger.info("EnergySyncTask: Bot 实例已设置")

    async def sync_orders(self) -> None:
        """同步待处理订单的状态（主入口）"""
        try:
            orders = self._get_pending_orders()

            if not orders:
                logger.debug("没有需要同步的能量订单")
                return

            logger.info(f"开始同步 {len(orders)} 个能量订单状态")

            async with EnergyAPIClient(
                username=settings.energy_api_username,
                password=settings.energy_api_password,
                base_url=settings.energy_api_base_url,
                backup_url=settings.energy_api_backup_url,
            ) as client:
                for order in orders:
                    await self._sync_single_order(client, order)

            logger.info("能量订单状态同步完成")

        except Exception as e:
            logger.error(f"能量订单同步失败: {e}", exc_info=True)
            collect_error("energy_sync", str(e), exception=e)

    def _get_pending_orders(self) -> list[dict[str, Any]]:
        """获取需要同步的订单"""
        cutoff_time = datetime.now() - timedelta(hours=SYNC_ORDER_AGE_HOURS)

        with get_db_context_readonly() as db:
            orders = (
                db.query(DBEnergyOrder)
                .filter(
                    DBEnergyOrder.status.in_(["PENDING", "PROCESSING"]),
                    DBEnergyOrder.api_order_id.isnot(None),  # 必须有 API 订单号
                    DBEnergyOrder.created_at >= cutoff_time,
                )
                .limit(MAX_ORDERS_PER_SYNC)
                .all()
            )

            # 提取需要的字段避免 detached instance 问题
            return [
                {
                    "order_id": o.order_id,
                    "api_order_id": o.api_order_id,
                    "status": o.status,
                    "user_id": o.user_id,
                    "energy_amount": o.energy_amount,
                }
                for o in orders
            ]

    async def _sync_single_order(self, client: EnergyAPIClient, order: dict[str, Any]) -> None:
        """同步单个订单状态"""
        order_id = order["order_id"]
        api_order_id = order["api_order_id"]
        current_status = order["status"]

        try:
            response = await client.query_order(api_order_id)

            if response.data is None:
                logger.warning(f"订单 {order_id} API 返回数据为空")
                return

            # 记录 API 返回便于调试
            logger.debug(f"订单 {order_id} API 返回: {response.data}")

            # 映射状态
            new_status = self._map_api_status(response.data)
            tx_hash = response.data.get("hash", "")

            # 状态有变化才更新
            if new_status != current_status:
                self._update_order_status(order_id, new_status, tx_hash)
                logger.info(f"订单 {order_id} 状态更新: {current_status} -> {new_status}")

                # 完成或失败时通知用户
                if new_status in ("COMPLETED", "FAILED"):
                    await self._notify_user(order, new_status, tx_hash)

        except EnergyAPIError as e:
            if e.code == EnergyAPIClient.CODE_ORDER_NOT_FOUND:  # 10004
                logger.warning(f"API 订单不存在: {api_order_id} (本地订单: {order_id})")
            else:
                logger.error(f"查询订单 {order_id} 失败: {e}")
        except Exception as e:
            logger.error(f"同步订单 {order_id} 异常: {e}")

    def _map_api_status(self, data: dict) -> str:
        """
        映射 API 返回状态到本地数据库状态

        逻辑：
        1. data.hash == "Waiting" → PROCESSING（处理中优先）
        2. data.status == 1 → COMPLETED（成功）
        3. data.status == 0 → FAILED（失败）
        """
        status = data.get("status")
        tx_hash = data.get("hash", "")

        # 先检查 hash 是否为 "Waiting"（处理中）
        if tx_hash == "Waiting":
            return "PROCESSING"

        # 根据 status 字段判断最终状态
        if status == 1:
            return "COMPLETED"
        elif status == 0:
            return "FAILED"
        else:
            return "PROCESSING"

    def _update_order_status(self, order_id: str, new_status: str, tx_hash: str = None) -> None:
        """更新订单状态"""
        with get_db_context() as db:
            order = db.query(DBEnergyOrder).filter_by(order_id=order_id).first()
            if order:
                order.status = new_status
                if new_status == "COMPLETED":
                    order.completed_at = datetime.now()
                if tx_hash and tx_hash != "Waiting":
                    order.user_tx_hash = tx_hash  # 保存交易哈希

    async def _notify_user(self, order: dict[str, Any], status: str, tx_hash: str) -> None:
        """通知用户订单状态变更"""
        if not self._bot:
            return

        user_id = order["user_id"]
        order_id = order["order_id"]
        energy_amount = order.get("energy_amount", 0) or 0

        if status == "COMPLETED":
            message = (
                f"✅ <b>能量订单已完成</b>\n\n📦 订单号: <code>{order_id}</code>\n⚡ 能量数量: {energy_amount:,}\n"
            )
            if tx_hash and tx_hash != "Waiting":
                message += f"🔗 交易哈希: <code>{tx_hash[:16]}...</code>\n"
            message += "\n能量已发放到指定地址！"
        else:
            message = f"❌ <b>能量订单失败</b>\n\n📦 订单号: <code>{order_id}</code>\n\n请联系客服处理。"

        try:
            await self._bot.send_message(chat_id=user_id, text=message, parse_mode="HTML")
            logger.info(f"已通知用户 {user_id} 订单 {order_id} 状态: {status}")
        except Exception as e:
            logger.error(f"发送通知失败: {e}")


# 全局实例
_sync_task: EnergySyncTask | None = None


def get_energy_sync_task() -> EnergySyncTask:
    """获取同步任务实例"""
    global _sync_task
    if _sync_task is None:
        _sync_task = EnergySyncTask()
    return _sync_task


async def run_energy_sync() -> None:
    """运行能量订单同步（供调度器调用）"""
    task = get_energy_sync_task()
    await task.sync_orders()
