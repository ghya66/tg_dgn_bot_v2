"""
个人中心模块主处理器 - 标准化版本
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    BaseHandler,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.common.conversation_wrapper import SafeConversationHandler
from src.common.navigation_manager import NavigationManager
from src.common.settings_service import get_order_timeout_minutes
from src.config import settings
from src.core.base import BaseModule
from src.core.formatter import MessageFormatter
from src.core.state_manager import ModuleStateManager
from src.payments.suffix_manager import suffix_manager
from src.wallet.wallet_manager import WalletManager

from .keyboards import ProfileKeyboards
from .messages import ProfileMessages
from .states import *


logger = logging.getLogger(__name__)


class ProfileModule(BaseModule):
    """标准化的个人中心模块"""

    def __init__(self):
        """初始化个人中心模块"""
        self.formatter = MessageFormatter()
        self.state_manager = ModuleStateManager()
        self.wallet_manager = WalletManager

    @property
    def module_name(self) -> str:
        """模块名称"""
        return "profile"

    def get_handlers(self) -> list[BaseHandler]:
        """获取模块处理器"""
        return [self._create_conversation_handler()]

    def _create_conversation_handler(self):
        """创建对话处理器"""
        return SafeConversationHandler.create(
            entry_points=[
                CommandHandler("profile", self.show_profile),
                MessageHandler(filters.Regex("^👤 个人中心$"), self.show_profile),
                CallbackQueryHandler(self.show_profile, pattern="^menu_profile$"),
            ],
            states={
                MAIN_MENU: [
                    CallbackQueryHandler(self.show_balance, pattern="^profile_balance$"),
                    CallbackQueryHandler(self.start_deposit, pattern="^profile_deposit$"),
                    CallbackQueryHandler(self.show_history, pattern="^profile_history$"),
                    CallbackQueryHandler(self.show_profile, pattern="^profile_back$"),
                ],
                AWAITING_DEPOSIT_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_deposit_amount),
                    CallbackQueryHandler(self.show_profile, pattern="^profile_back$"),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
            ],
            name="profile",
            conversation_timeout=600,  # 10分钟超时
        )

    async def show_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """显示个人中心主界面"""
        # 初始化状态
        self.state_manager.init_state(context, self.module_name)

        # 兼容 Message 和 CallbackQuery 两种入口
        if update.callback_query:
            await update.callback_query.answer()
            message = update.callback_query.message
            send_method = message.edit_text
        else:
            message = update.message
            send_method = message.reply_text

        user = update.effective_user
        user_id = user.id

        # 获取余额
        with self.wallet_manager() as wallet:
            balance = wallet.get_balance(user_id)

        # 构建消息
        display_name = user.full_name or user.username or f"User_{user_id}"
        safe_name = self.formatter.escape_html(display_name)

        text = ProfileMessages.PROFILE_MAIN.format(name=safe_name, user_id=user_id, balance=balance)

        await send_method(text, parse_mode="HTML", reply_markup=ProfileKeyboards.main_menu())

        return MAIN_MENU

    async def show_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """显示余额详情"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        with self.wallet_manager() as wallet:
            balance = wallet.get_balance(user_id)
            deposits = wallet.get_user_deposits(user_id, limit=5)
            debits = wallet.get_user_debits(user_id, limit=5)

        # 统计信息
        total_deposited = sum(d.total_amount for d in deposits if d.status == "PAID")
        total_spent = sum(d.get_amount() for d in debits)

        text = (
            "<b>余额详情</b>\n\n"
            f"当前余额: <code>{balance:.3f}</code> USDT\n"
            f"累计充值: <code>{total_deposited:.3f}</code> USDT\n"
            f"累计消费: <code>{total_spent:.3f}</code> USDT\n"
        )

        await query.edit_message_text(text, parse_mode="HTML", reply_markup=ProfileKeyboards.back_to_profile())

        return MAIN_MENU

    async def start_deposit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """开始充值流程"""
        query = update.callback_query
        await query.answer()

        # 添加取消按钮，方便用户返回
        keyboard = [[InlineKeyboardButton("❌ 取消", callback_data="profile_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(ProfileMessages.DEPOSIT_START, parse_mode="HTML", reply_markup=reply_markup)

        return AWAITING_DEPOSIT_AMOUNT

    async def receive_deposit_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """接收充值金额"""
        user_id = update.effective_user.id
        text = update.message.text.strip()

        # 解析金额
        try:
            amount = float(text)
            if amount < 1:
                await update.message.reply_text(ProfileMessages.INVALID_AMOUNT, parse_mode="HTML")
                return AWAITING_DEPOSIT_AMOUNT
            if amount > 10000:
                await update.message.reply_text(
                    "金额过大，最大充值 10000 USDT\n\n请重新输入或 /cancel 取消", parse_mode="HTML"
                )
                return AWAITING_DEPOSIT_AMOUNT
        except ValueError:
            await update.message.reply_text(ProfileMessages.INVALID_AMOUNT, parse_mode="HTML")
            return AWAITING_DEPOSIT_AMOUNT

        # 分配唯一后缀
        await suffix_manager.connect()
        suffix = await suffix_manager.allocate_suffix()

        if suffix is None:
            await update.message.reply_text("系统繁忙，请稍后再试")
            return ConversationHandler.END

        # 创建充值订单
        with self.wallet_manager() as wallet:
            order = wallet.create_deposit_order(
                user_id=user_id,
                base_amount=amount,
                unique_suffix=suffix,
            )

        # 保存订单ID到后缀池
        await suffix_manager.set_order_id(suffix, order.order_id)

        # 获取超时时间
        timeout_minutes = get_order_timeout_minutes()

        # 发送支付信息
        text = ProfileMessages.PAYMENT_INFO.format(
            amount_with_suffix=order.total_amount,
            receive_address=settings.usdt_trc20_receive_addr,
            timeout_minutes=timeout_minutes,
        )

        await update.message.reply_text(text, parse_mode="HTML", reply_markup=ProfileKeyboards.back_to_profile())

        return ConversationHandler.END

    async def show_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """显示充值记录"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        with self.wallet_manager() as wallet:
            deposits = wallet.get_user_deposits(user_id, limit=10)

        if not deposits:
            text = ProfileMessages.DEPOSIT_HISTORY_EMPTY
        else:
            records = []
            for deposit in deposits:
                status_emoji = {"PAID": "✅", "PENDING": "⏰", "EXPIRED": "❌"}.get(deposit.status, "❓")

                record = ProfileMessages.DEPOSIT_RECORD_ITEM.format(
                    created_at=deposit.created_at.strftime("%Y-%m-%d %H:%M"),
                    amount=deposit.total_amount,
                    status=f"{status_emoji} {deposit.status}",
                )
                records.append(record)

            text = ProfileMessages.DEPOSIT_HISTORY.format(count=len(deposits), records="\n\n".join(records))

        await query.edit_message_text(text, parse_mode="HTML", reply_markup=ProfileKeyboards.back_to_profile())

        return MAIN_MENU

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """取消操作"""
        if update.callback_query:
            await update.callback_query.answer("已取消")

        # 使用统一的导航管理器
        return await NavigationManager.cleanup_and_show_main_menu(update, context)
