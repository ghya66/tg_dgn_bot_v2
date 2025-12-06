"""
Premium 交付服务：自动发货模式
使用 Bot 的 Stars 余额调用 gift_premium_subscription API
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

from src.config import settings
from src.database import PremiumOrder
from src.common.db_manager import get_db_context

logger = logging.getLogger(__name__)


class PremiumDeliveryService:
    """Premium 自动交付服务"""
    
    # Stars 价格配置（TODO: 根据 Telegram 官方定价调整）
    STARS_PRICE = {
        3: 1000,    # 3个月 - 占位值
        6: 1750,    # 6个月 - 占位值
        12: 3000    # 12个月 - 占位值
    }
    
    def __init__(self, bot: Bot, order_manager):
        self.bot = bot
        self.order_manager = order_manager
    
    async def check_stars_balance(self) -> int:
        """检查 Bot 的 Stars 余额"""
        try:
            transactions = await self.bot.get_star_transactions(limit=100)
            balance = 0
            for tx in transactions.transactions:
                if tx.source:  # 收入
                    balance += tx.amount
                if tx.receiver:  # 支出
                    balance -= tx.amount
            logger.info(f"Bot Stars balance: {balance}")
            return balance
        except TelegramError as e:
            logger.error(f"Failed to check Stars balance: {e}")
            return 0
    
    async def deliver_premium(
        self,
        order_id: str,
        buyer_id: int,
        recipient_username: str,
        recipient_id: Optional[int],
        premium_months: int
    ) -> Dict[str, Any]:
        """
        自动发货 Premium
        
        Args:
            order_id: 订单ID
            buyer_id: 买家用户ID
            recipient_username: 收件人用户名
            recipient_id: 收件人用户ID（可能为空，需要解析）
            premium_months: Premium月数
            
        Returns:
            {success: bool, message: str, ...}
        """
        try:
            # Step 1: 确保有 recipient_id
            if not recipient_id:
                recipient_id = await self._resolve_user_id(recipient_username)
                if not recipient_id:
                    return await self._handle_failure(
                        order_id, buyer_id,
                        f"无法获取用户 @{recipient_username} 的ID，请确认用户名正确且用户允许被搜索"
                    )
            
            # Step 2: 检查 Stars 余额
            stars_needed = self.STARS_PRICE.get(premium_months, 1000)
            balance = await self.check_stars_balance()
            
            if balance < stars_needed:
                return await self._handle_failure(
                    order_id, buyer_id,
                    f"Bot Stars 余额不足（需要 {stars_needed}，当前 {balance}），请联系管理员充值"
                )
            
            # Step 3: 调用 gift_premium_subscription API
            await self.bot.gift_premium_subscription(
                user_id=recipient_id,
                month_count=premium_months,
                star_count=stars_needed,
                text=f"🎁 您的 {premium_months} 个月 Telegram Premium 已到账！",
                text_parse_mode="HTML"
            )
            
            # Step 4: 更新订单状态
            await self._mark_delivered(order_id, recipient_id)
            
            # Step 5: 通知买家
            await self._notify_buyer_success(buyer_id, recipient_username, premium_months)
            
            # Step 6: 通知管理员（可选）
            await self._notify_admin_success(order_id, recipient_username, premium_months, stars_needed)
            
            logger.info(f"Premium delivered successfully: order={order_id}, recipient=@{recipient_username}")
            
            return {
                "success": True,
                "message": "发货成功",
                "order_id": order_id,
                "recipient_id": recipient_id,
                "stars_used": stars_needed
            }
            
        except TelegramError as e:
            error_msg = str(e)
            logger.error(f"Premium delivery failed for order {order_id}: {e}")
            
            # 解析常见错误
            if "USER_NOT_FOUND" in error_msg:
                error_msg = f"用户 @{recipient_username} 不存在"
            elif "PREMIUM_CURRENTLY_UNAVAILABLE" in error_msg:
                error_msg = "Premium 服务暂时不可用，请稍后重试"
            elif "BALANCE_TOO_LOW" in error_msg:
                error_msg = "Bot Stars 余额不足"
            
            return await self._handle_failure(order_id, buyer_id, error_msg)
            
        except Exception as e:
            logger.error(f"Unexpected error in delivery: {e}", exc_info=True)
            return await self._handle_failure(order_id, buyer_id, f"系统错误: {str(e)}")
    
    async def _resolve_user_id(self, username: str) -> Optional[int]:
        """通过用户名获取 user_id"""
        try:
            chat = await self.bot.get_chat(f"@{username}")
            return chat.id
        except TelegramError as e:
            logger.warning(f"Failed to resolve username @{username}: {e}")
            return None
    
    async def _mark_delivered(self, order_id: str, recipient_id: int):
        """更新订单状态为已发货"""
        with get_db_context() as db:
            order = db.query(PremiumOrder).filter(
                PremiumOrder.order_id == order_id
            ).first()
            if order:
                order.status = 'DELIVERED'
                order.delivered_at = datetime.now()
                order.recipient_id = recipient_id
                # 上下文管理器会自动 commit

    async def _handle_failure(self, order_id: str, buyer_id: int, error_msg: str) -> Dict[str, Any]:
        """处理发货失败"""
        # 更新订单状态
        with get_db_context() as db:
            order = db.query(PremiumOrder).filter(
                PremiumOrder.order_id == order_id
            ).first()
            if order:
                order.status = 'DELIVERY_FAILED'
                order.fail_reason = error_msg
                # 上下文管理器会自动 commit
        
        # 通知买家
        try:
            await self.bot.send_message(
                chat_id=buyer_id,
                text=(
                    "❌ <b>Premium 发货失败</b>\n\n"
                    f"订单号：<code>{order_id}</code>\n"
                    f"原因：{error_msg}\n\n"
                    "客服将尽快与您联系处理。"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
        
        # 通知管理员
        admin_id = settings.bot_owner_id
        if admin_id:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        "🚨 <b>Premium 发货失败</b>\n\n"
                        f"订单号：<code>{order_id}</code>\n"
                        f"买家ID：<code>{buyer_id}</code>\n"
                        f"错误：{error_msg}\n\n"
                        "请人工处理！"
                    ),
                    parse_mode="HTML"
                )
            except Exception:
                pass
        
        return {
            "success": False,
            "message": error_msg,
            "order_id": order_id
        }
    
    async def _notify_buyer_success(self, buyer_id: int, recipient_username: str, months: int):
        """通知买家发货成功"""
        try:
            await self.bot.send_message(
                chat_id=buyer_id,
                text=(
                    "🎉 <b>Premium 发货成功！</b>\n\n"
                    f"👤 收件人：@{recipient_username}\n"
                    f"🎁 套餐：{months} 个月 Premium\n\n"
                    "感谢您的购买！"
                ),
                parse_mode="HTML"
            )
        except TelegramError as e:
            logger.warning(f"Failed to notify buyer {buyer_id}: {e}")
    
    async def _notify_admin_success(self, order_id: str, recipient_username: str, months: int, stars_used: int):
        """通知管理员发货成功（可选）"""
        admin_id = settings.bot_owner_id
        if not admin_id:
            return
        
        try:
            balance = await self.check_stars_balance()
            await self.bot.send_message(
                chat_id=admin_id,
                text=(
                    "✅ <b>Premium 自动发货成功</b>\n\n"
                    f"订单号：<code>{order_id}</code>\n"
                    f"收件人：@{recipient_username}\n"
                    f"套餐：{months} 个月\n"
                    f"消耗：{stars_used} Stars\n"
                    f"剩余余额：{balance} Stars"
                ),
                parse_mode="HTML"
            )
        except TelegramError as e:
            logger.warning(f"Failed to notify admin: {e}")
