"""
TRX兑换模块主处理器 - 标准化版本
"""

import logging
import uuid
from typing import List
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    BaseHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
from sqlalchemy.orm import Session

from src.core.base import BaseModule
from src.core.formatter import MessageFormatter
from src.core.state_manager import ModuleStateManager
from src.common.conversation_wrapper import SafeConversationHandler
from src.common.navigation_manager import NavigationManager
from src.config import settings
from src.database import SessionLocal
from .models import TRXExchangeOrder
from .rate_manager import RateManager
from .trx_sender import TRXSender
from src.common.settings_service import get_order_timeout_minutes

from .messages import TRXExchangeMessages
from .keyboards import TRXExchangeKeyboards
from .states import *


logger = logging.getLogger(__name__)


class TRXExchangeModule(BaseModule):
    """标准化的TRX兑换模块"""
    
    def __init__(self):
        """初始化TRX兑换模块"""
        self.formatter = MessageFormatter()
        self.state_manager = ModuleStateManager()
        self.trx_sender = TRXSender()
    
    @property
    def module_name(self) -> str:
        """模块名称"""
        return "trx_exchange"
    
    def get_handlers(self) -> List[BaseHandler]:
        """获取模块处理器"""
        return [self._create_conversation_handler()]
    
    def _create_conversation_handler(self):
        """创建对话处理器"""
        return SafeConversationHandler.create(
            entry_points=[
                CommandHandler("trx", self.start_exchange),
                MessageHandler(filters.Regex("^💱 TRX闪兑$"), self.start_exchange),
                CallbackQueryHandler(self.start_exchange, pattern="^menu_trx_exchange$"),
            ],
            states={
                INPUT_AMOUNT: [
                    CallbackQueryHandler(self.cancel_input, pattern="^trx_cancel_input$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.input_amount)
                ],
                INPUT_ADDRESS: [
                    CallbackQueryHandler(self.cancel_input, pattern="^trx_cancel_input$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.input_address)
                ],
                CONFIRM_PAYMENT: [
                    CallbackQueryHandler(self.confirm_payment, pattern="^trx_(paid|cancel)_")
                ],
                INPUT_TX_HASH: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_tx_hash_input),
                    CallbackQueryHandler(self.skip_tx_hash, pattern="^trx_skip_hash$"),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CallbackQueryHandler(self.cancel_input, pattern="^trx_cancel_input$"),
            ],
            name="trx_exchange",
            conversation_timeout=600,  # 10分钟超时
        )
    
    def generate_order_id(self) -> str:
        """生成唯一订单ID"""
        return f"TRX{uuid.uuid4().hex[:16].upper()}"
    
    def generate_unique_amount(self, base_amount: Decimal) -> Decimal:
        """生成带3位小数后缀的唯一金额"""
        import random
        suffix = random.randint(1, 999)
        return base_amount + Decimal(f"0.{suffix:03d}")
    
    async def start_exchange(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """开始TRX兑换流程"""
        # 初始化状态
        self.state_manager.init_state(context, self.module_name)
        
        # 兼容 Message 和 CallbackQuery 两种入口
        if update.callback_query:
            await update.callback_query.answer()
            message = update.callback_query.message
        else:
            message = update.message
        
        await message.reply_text(
            TRXExchangeMessages.WELCOME,
            parse_mode="HTML",
            reply_markup=TRXExchangeKeyboards.cancel_button()
        )
        
        return INPUT_AMOUNT
    
    async def input_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """处理USDT金额输入"""
        user_input = update.message.text.strip()
        
        # 验证金额
        try:
            amount = Decimal(user_input)
        except Exception:
            await update.message.reply_text(TRXExchangeMessages.INVALID_AMOUNT, parse_mode="HTML")
            return INPUT_AMOUNT
        
        # 检查最小/最大限额
        if amount < Decimal("5"):
            await update.message.reply_text(TRXExchangeMessages.INVALID_AMOUNT, parse_mode="HTML")
            return INPUT_AMOUNT
        
        if amount > Decimal("20000"):
            await update.message.reply_text(TRXExchangeMessages.INVALID_AMOUNT, parse_mode="HTML")
            return INPUT_AMOUNT
        
        # 获取当前汇率
        db: Session = SessionLocal()
        try:
            rate = RateManager.get_rate(db)
            trx_amount = RateManager.calculate_trx_amount(amount, rate)
        finally:
            db.close()
        
        # 保存到 context
        context.user_data["exchange_usdt_amount"] = amount
        context.user_data["exchange_rate"] = rate
        context.user_data["exchange_trx_amount"] = trx_amount
        
        await update.message.reply_text(
            TRXExchangeMessages.INPUT_ADDRESS,
            parse_mode="HTML",
            reply_markup=TRXExchangeKeyboards.cancel_button()
        )
        
        return INPUT_ADDRESS
    
    async def input_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """处理TRX地址输入"""
        address = update.message.text.strip()
        
        # 验证地址
        if not self.trx_sender.validate_address(address):
            await update.message.reply_text(TRXExchangeMessages.INVALID_ADDRESS, parse_mode="HTML")
            return INPUT_ADDRESS
        
        # 保存地址
        context.user_data["exchange_recipient_address"] = address
        
        # 显示支付页面
        return await self.show_payment(update, context)
    
    async def show_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """显示支付信息"""
        user_id = update.effective_user.id
        usdt_amount = context.user_data["exchange_usdt_amount"]
        rate = context.user_data["exchange_rate"]
        trx_amount = context.user_data["exchange_trx_amount"]
        recipient_address = context.user_data["exchange_recipient_address"]
        
        # 创建订单
        db: Session = SessionLocal()
        now_utc = datetime.now(timezone.utc)
        timeout_minutes = get_order_timeout_minutes()
        expires_at = now_utc + timedelta(minutes=timeout_minutes)
        
        try:
            unique_amount = self.generate_unique_amount(usdt_amount)
            order_id = self.generate_order_id()
            
            order = TRXExchangeOrder(
                order_id=order_id,
                user_id=user_id,
                usdt_amount=unique_amount,
                trx_amount=trx_amount,
                exchange_rate=rate,
                recipient_address=recipient_address,
                payment_address=settings.trx_exchange_receive_address,
                status="PENDING",
                created_at=now_utc,
                expires_at=expires_at,
            )
            db.add(order)
            db.commit()
            
            logger.info(f"Created TRX exchange order: {order_id}")
        finally:
            db.close()
        
        # 保存订单ID
        context.user_data["exchange_order_id"] = order_id
        
        # 发送支付信息
        payment_address = settings.trx_exchange_receive_address
        qrcode_file_id = getattr(settings, 'trx_exchange_qrcode_file_id', None)
        
        message_text = TRXExchangeMessages.PAYMENT_INFO.format(
            order_id=order_id,
            usdt_amount=usdt_amount,
            trx_amount=trx_amount,
            rate=rate,
            receive_address=recipient_address,
            payment_amount=unique_amount,
            payment_address=payment_address,
            timeout_minutes=timeout_minutes
        )
        
        # 发送消息
        if qrcode_file_id and qrcode_file_id != "YOUR_QRCODE_FILE_ID_HERE":
            try:
                await update.effective_message.reply_photo(
                    photo=qrcode_file_id,
                    caption=message_text,
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.warning(f"Failed to send QR code: {e}")
                await update.effective_message.reply_text(message_text, parse_mode="HTML")
        else:
            await update.effective_message.reply_text(message_text, parse_mode="HTML")
        
        # 发送确认按钮
        await update.effective_message.reply_text(
            "支付完成后，请点击下方按钮确认：",
            reply_markup=TRXExchangeKeyboards.payment_buttons(order_id),
        )
        
        return CONFIRM_PAYMENT
    
    async def confirm_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """处理支付确认"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        order_id = context.user_data.get("exchange_order_id")
        
        if "cancel" in data:
            await query.edit_message_text("订单已取消")
            return ConversationHandler.END
        
        # 检查订单是否过期
        db: Session = SessionLocal()
        try:
            order = db.query(TRXExchangeOrder).filter_by(order_id=order_id).first()
            if order and order.expires_at:
                now_utc = datetime.now(timezone.utc)
                if order.expires_at.tzinfo is None:
                    expires_at = order.expires_at.replace(tzinfo=timezone.utc)
                else:
                    expires_at = order.expires_at
                
                if now_utc > expires_at:
                    await query.edit_message_text(TRXExchangeMessages.PAYMENT_EXPIRED)
                    return ConversationHandler.END
        finally:
            db.close()
        
        # 请求交易哈希
        await query.edit_message_text(
            TRXExchangeMessages.WAITING_TX_HASH,
            reply_markup=TRXExchangeKeyboards.skip_tx_hash()
        )
        
        return INPUT_TX_HASH
    
    async def handle_tx_hash_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """处理交易哈希输入"""
        tx_hash = update.message.text.strip()
        order_id = context.user_data.get("exchange_order_id")
        
        # 保存交易哈希
        db: Session = SessionLocal()
        try:
            order = db.query(TRXExchangeOrder).filter_by(order_id=order_id).first()
            if order:
                order.tx_hash = tx_hash
                order.status = "PAID"
                db.commit()
        finally:
            db.close()
        
        await update.message.reply_text(
            TRXExchangeMessages.ORDER_SUBMITTED.format(
                order_id=order_id,
                tx_hash=tx_hash
            ),
            parse_mode="HTML"
        )
        
        # 清理状态
        self.state_manager.clear_state(context, self.module_name)
        
        return ConversationHandler.END
    
    async def skip_tx_hash(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """跳过交易哈希"""
        query = update.callback_query
        await query.answer()
        
        order_id = context.user_data.get("exchange_order_id")
        
        await query.edit_message_text(
            TRXExchangeMessages.ORDER_SKIP_HASH.format(order_id=order_id),
            parse_mode="HTML"
        )
        
        # 清理状态
        self.state_manager.clear_state(context, self.module_name)
        
        return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """取消操作"""
        if update.callback_query:
            await update.callback_query.answer("已取消")
        
        return await NavigationManager.cleanup_and_show_main_menu(update, context)
    
    async def cancel_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """取消输入阶段（按钮回调）"""
        query = update.callback_query
        await query.answer("已取消")
        
        # 清理状态
        self.state_manager.clear_state(context, self.module_name)
        
        # 编辑消息显示取消提示
        await query.edit_message_text("❌ 已取消 TRX 兑换")
        
        return ConversationHandler.END
