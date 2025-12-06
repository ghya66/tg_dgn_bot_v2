"""
订单超时自动处理任务

定期检查数据库中的 PENDING 订单，自动将超时订单标记为 EXPIRED，
并释放占用的 Redis 后缀（如果适用）。

注意：此模块使用异步方法，与 AsyncIOScheduler 兼容。
"""

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from telegram import Bot

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.common.db_manager import get_db_context_manual_commit
from src.common.settings_service import get_order_timeout_minutes

from ..database import Order
from ..payments.suffix_manager import SuffixManager


logger = logging.getLogger(__name__)


class OrderExpiryTask:
    """订单超时处理任务"""

    def __init__(self):
        """初始化任务"""
        self.suffix_manager = SuffixManager()
        self._bot: Bot | None = None
        logger.info("订单超时处理任务初始化完成")

    def set_bot(self, bot: "Bot") -> None:
        """设置 Bot 实例用于发送通知"""
        self._bot = bot
        logger.info("订单超时任务已绑定 Bot 实例")

    async def check_and_expire_orders(self) -> dict:
        """
        检查并处理过期订单

        Returns:
            dict: 处理结果统计
                {
                    "checked": int,  # 检查的订单数
                    "expired": int,  # 已过期的订单数
                    "suffix_released": int,  # 释放的后缀数
                    "errors": int  # 处理错误数
                }
        """
        timeout_minutes = get_order_timeout_minutes()
        logger.info("订单超时检查任务：本次使用超时时间 %s 分钟", timeout_minutes)

        stats = {"checked": 0, "expired": 0, "suffix_released": 0, "errors": 0}

        # 使用手动提交的上下文管理器，确保连接正确关闭
        with get_db_context_manual_commit() as session:
            try:
                # 计算超时时间点
                timeout_time = datetime.now() - timedelta(minutes=timeout_minutes)

                # 查询所有超时的 PENDING 订单
                stmt = select(Order).where(Order.status == "PENDING", Order.created_at < timeout_time)
                expired_orders = session.execute(stmt).scalars().all()

                stats["checked"] = len(expired_orders)

                if not expired_orders:
                    logger.debug("没有发现过期订单")
                    return stats

                logger.info(f"发现 {len(expired_orders)} 个过期订单，开始处理...")

                # 处理每个过期订单
                for order in expired_orders:
                    try:
                        await self._expire_single_order(session, order, stats)
                    except Exception as e:
                        logger.error(f"处理订单 {order.order_id} 失败: {e}", exc_info=True)
                        stats["errors"] += 1

                # 提交所有更改
                session.commit()

                logger.info(
                    f"订单超时处理完成 - "
                    f"检查: {stats['checked']}, "
                    f"已过期: {stats['expired']}, "
                    f"释放后缀: {stats['suffix_released']}, "
                    f"错误: {stats['errors']}"
                )

            except Exception as e:
                logger.error(f"订单超时检查任务失败: {e}", exc_info=True)
                session.rollback()
                stats["errors"] += 1

        return stats

    async def _expire_single_order(self, session: Session, order: Order, stats: dict):
        """
        处理单个过期订单（异步方法）

        Args:
            session: 数据库会话
            order: 订单对象
            stats: 统计字典
        """
        order_id = order.order_id
        order_type = order.order_type

        # 更新订单状态
        order.status = "EXPIRED"

        logger.info(
            f"订单 {order_id} 已过期 (类型: {order_type}, 创建时间: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
        )

        stats["expired"] += 1

        # 释放 Redis 后缀（仅适用于使用3位小数后缀的订单类型）
        if self._should_release_suffix(order_type):
            try:
                # 从订单金额中提取后缀
                suffix = self._extract_suffix_from_amount(order.amount_usdt)

                if suffix:
                    # 使用 await 替代 asyncio.run()，避免嵌套事件循环
                    released = await self.suffix_manager.release_suffix(suffix, order_id)
                    if released:
                        logger.info(f"释放后缀 {suffix} (订单: {order_id})")
                        stats["suffix_released"] += 1
                    else:
                        logger.warning(f"无法释放后缀 {suffix} (订单: {order_id})")

            except Exception as e:
                logger.error(f"释放后缀失败 (订单: {order_id}): {e}")

        # 通知用户订单已过期
        await self._notify_user_order_expired(order, stats)

    def _should_release_suffix(self, order_type: str) -> bool:
        """
        判断订单类型是否需要释放后缀

        Args:
            order_type: 订单类型

        Returns:
            bool: 是否需要释放后缀
        """
        # 使用3位小数后缀的订单类型
        suffix_order_types = ["premium", "deposit", "trx_exchange"]
        return order_type in suffix_order_types

    def _extract_suffix_from_amount(self, amount_micro_usdt: int) -> int | None:
        """
        从微 USDT 金额中提取后缀

        Args:
            amount_micro_usdt: 微 USDT 金额（整数，单位：微 USDT）

        Returns:
            Optional[int]: 后缀（1-999），如果无法提取则返回 None
        """
        try:
            # 将微 USDT 转为 USDT（保留3位小数）
            amount_usdt = amount_micro_usdt / 1_000_000

            # 提取小数部分的后三位
            # 例如：10.123 USDT -> 123
            suffix = int(round(amount_usdt * 1000)) % 1000

            # 验证后缀范围（1-999）
            if 1 <= suffix <= 999:
                return suffix
            else:
                logger.warning(f"提取的后缀 {suffix} 超出范围 (金额: {amount_usdt} USDT)")
                return None

        except Exception as e:
            logger.error(f"提取后缀失败 (金额: {amount_micro_usdt}): {e}")
            return None

    async def _notify_user_order_expired(self, order: Order, stats: dict):
        """
        通知用户订单已过期（异步方法）

        Args:
            order: 订单对象
            stats: 统计字典
        """
        if not self._bot:
            logger.debug("未设置 Bot 实例，跳过用户通知")
            return

        user_id = order.user_id
        order_id = order.order_id
        order_type = order.order_type

        # 构建通知消息
        order_type_names = {
            "premium": "Premium会员",
            "deposit": "余额充值",
            "trx_exchange": "TRX兑换",
            "energy": "能量服务",
        }
        type_name = order_type_names.get(order_type, order_type)

        message = (
            f"⏰ <b>订单已过期</b>\n\n"
            f"订单号: <code>{order_id}</code>\n"
            f"类型: {type_name}\n\n"
            f"订单因超时未支付已自动取消。\n"
            f"如需继续，请重新发起。"
        )

        try:
            # 使用 await 替代 asyncio.run()，避免嵌套事件循环
            await self._bot.send_message(chat_id=user_id, text=message, parse_mode="HTML")
            logger.info(f"已通知用户 {user_id} 订单 {order_id} 过期")
            stats["notified"] = stats.get("notified", 0) + 1
        except Exception as e:
            # 通知失败不影响主流程
            logger.warning(f"通知用户 {user_id} 失败: {e}")

    async def run(self):
        """运行任务（由调度器调用，异步方法）"""
        try:
            logger.debug("开始执行订单超时检查任务...")
            stats = await self.check_and_expire_orders()
            return stats
        except Exception as e:
            logger.error(f"订单超时任务执行失败: {e}", exc_info=True)
            return {"error": str(e)}


# 全局任务实例
order_expiry_task = OrderExpiryTask()
