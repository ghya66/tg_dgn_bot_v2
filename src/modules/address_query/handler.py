"""
地址查询模块主处理器 - 标准化版本
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    BaseHandler,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from src.core.base import BaseModule
from src.core.formatter import MessageFormatter
from src.core.state_manager import ModuleStateManager
from src.common.conversation_wrapper import SafeConversationHandler
from src.common.navigation_manager import NavigationManager

from .messages import AddressQueryMessages
from .states import *
from .keyboards import AddressQueryKeyboards

# 从本模块导入业务逻辑类
from .validator import AddressValidator
from src.clients.tron import TronAPIClient
from src.database import SessionLocal, AddressQueryLog
from src.common.settings_service import get_address_cooldown_minutes

logger = logging.getLogger(__name__)


class AddressQueryModule(BaseModule):
    """标准化的地址查询模块"""
    
    def __init__(self):
        """初始化地址查询模块"""
        self.formatter = MessageFormatter()
        self.state_manager = ModuleStateManager()
        self.validator = AddressValidator()
        self.tron_client = TronAPIClient()
    
    @property
    def module_name(self) -> str:
        """模块名称"""
        return "address_query"
    
    def get_handlers(self) -> List[BaseHandler]:
        """
        获取模块处理器
        
        Returns:
            包含ConversationHandler的列表
        """
        conv_handler = SafeConversationHandler.create(
            entry_points=[
                CommandHandler("query", self.start_query),
                CallbackQueryHandler(self.start_query, pattern="^(address_query|menu_address_query)$"),
                MessageHandler(filters.Regex("^🔍 地址查询$"), self.start_query),
            ],
            states={
                AWAITING_ADDRESS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_address_input),
                ],
            },
            fallbacks=[
                CallbackQueryHandler(self.cancel, pattern="^addrq_cancel$"),
                # nav_back_to_main 由 NavigationManager 统一处理
                CommandHandler("cancel", self.cancel),
            ],
            name="address_query_conversation",
            allow_reentry=True,
            conversation_timeout=600,  # 10分钟超时
        )
        
        return [conv_handler]
    
    async def start_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        开始地址查询
        兼容 CallbackQuery 和 Message 两种入口
        """
        # 初始化状态
        self.state_manager.init_state(context, self.module_name)
        
        user_id = update.effective_user.id
        
        # 检查限频
        can_query, remaining_minutes = self._check_rate_limit(user_id)
        
        if not can_query:
            text = AddressQueryMessages.RATE_LIMIT.format(
                remaining_minutes=remaining_minutes
            )
            
            keyboard = [[InlineKeyboardButton("🔙 返回主菜单", callback_data="nav_back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # 兼容不同入口
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(
                    text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            
            return ConversationHandler.END
        
        # 提示输入地址
        text = AddressQueryMessages.START_QUERY
        
        keyboard = [[InlineKeyboardButton("❌ 取消", callback_data="addrq_cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 兼容不同入口
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        
        return AWAITING_ADDRESS
    
    async def handle_address_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """处理用户输入的地址"""
        try:
            # 清理地址：移除所有空白字符
            address = ''.join(update.message.text.split())
            user_id = update.effective_user.id
            
            logger.info(f"用户 {user_id} 查询地址: {address}")
            
            # 验证地址格式
            is_valid, error_msg = self.validator.validate(address)
            
            if not is_valid:
                text = AddressQueryMessages.INVALID_ADDRESS
                keyboard = [[InlineKeyboardButton("❌ 取消", callback_data="addrq_cancel")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
                return AWAITING_ADDRESS  # 继续等待输入
            
            # 再次检查限频（防止绕过）
            can_query, remaining_minutes = self._check_rate_limit(user_id)
            
            if not can_query:
                text = AddressQueryMessages.RATE_LIMIT.format(
                    remaining_minutes=remaining_minutes
                )
                keyboard = [[InlineKeyboardButton("🔙 返回主菜单", callback_data="nav_back_to_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
                return ConversationHandler.END
            
            # 记录查询
            self._record_query(user_id)
            
            # 显示查询中提示
            processing_msg = await update.message.reply_text(AddressQueryMessages.PROCESSING)
            
            # 获取地址信息（使用统一客户端）
            address_info = await self.tron_client.get_address_info(address)
            
            # 生成浏览器链接
            links = TronAPIClient.get_explorer_links(address)
            
            # 构建响应消息
            if address_info:
                # 有API数据（AddressInfo dataclass）
                trx_balance = address_info.format_trx()
                usdt_balance = address_info.format_usdt()
                
                # 处理最近交易
                txs = address_info.recent_txs
                if txs:
                    transaction_list = ""
                    for idx, tx in enumerate(txs[:5], 1):
                        direction = tx.get('direction', '?')
                        amount = tx.get('amount', '0')
                        token = tx.get('token', 'TRX')
                        tx_hash = tx.get('hash', '')[:10]  # 只显示前10位
                        timestamp = tx.get('time', '')
                        
                        transaction_list += f"{idx}. {direction} {amount} {token}\n"
                        transaction_list += f"   哈希: <code>{tx_hash}...</code>\n"
                        transaction_list += f"   时间: {timestamp}\n\n"
                    
                    transactions_info = AddressQueryMessages.RECENT_TRANSACTIONS.format(
                        transaction_list=transaction_list
                    )
                else:
                    transactions_info = AddressQueryMessages.NO_TRANSACTIONS
                
                text = AddressQueryMessages.QUERY_RESULT.format(
                    address=address,
                    trx_balance=trx_balance,
                    usdt_balance=usdt_balance,
                    transactions_info=transactions_info
                )
            else:
                # 无API数据
                text = AddressQueryMessages.QUERY_RESULT_NO_API.format(address=address)
            
            # 添加深链接按钮
            keyboard = [
                [
                    InlineKeyboardButton("🔗 链上查询详情", url=links["overview"]),
                    InlineKeyboardButton("🔍 查询转账记录", url=links["txs"])
                ],
                [InlineKeyboardButton("🔙 返回主菜单", callback_data="nav_back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # 删除"查询中"提示
            try:
                await processing_msg.delete()
            except Exception:
                pass  # 忽略删除失败
            
            # 发送结果
            await update.message.reply_text(
                text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            
            logger.info(f"用户 {user_id} 查询地址成功: {address}")
            
            # 清理状态
            self.state_manager.clear_state(context, self.module_name)
            
            # 结束对话
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"处理地址输入时出错: {e}", exc_info=True)
            
            # 发送错误提示
            text = AddressQueryMessages.QUERY_ERROR
            keyboard = [[InlineKeyboardButton("🔙 返回主菜单", callback_data="nav_back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await update.message.reply_text(
                    text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            except Exception:
                pass
            
            return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """取消操作"""
        query = update.callback_query
        if query:
            await query.answer()
        
        # 使用统一的导航管理器（会自动清理状态）
        return await NavigationManager.cleanup_and_show_main_menu(update, context)
    
    def _check_rate_limit(self, user_id: int) -> tuple[bool, int]:
        """
        检查用户查询限频
        
        Args:
            user_id: 用户ID
            
        Returns:
            (是否可以查询, 剩余分钟数)
        """
        try:
            db = SessionLocal()
            cooldown_minutes = get_address_cooldown_minutes()
            
            # 查询最近一次查询记录
            last_query = db.query(AddressQueryLog).filter_by(
                user_id=user_id
            ).order_by(AddressQueryLog.last_query_at.desc()).first()
            
            if last_query:
                time_since_last = datetime.now() - last_query.last_query_at
                if time_since_last < timedelta(minutes=cooldown_minutes):
                    remaining = cooldown_minutes - int(time_since_last.total_seconds() / 60)
                    return False, max(1, remaining)
            
            return True, 0
            
        except Exception as e:
            logger.error(f"检查限频失败: {e}", exc_info=True)
            return True, 0  # 出错时允许查询
        finally:
            db.close()
    
    def _record_query(self, user_id: int):
        """记录查询"""
        try:
            db = SessionLocal()
            
            log = AddressQueryLog(
                user_id=user_id,
                last_query_at=datetime.now()
            )
            db.add(log)
            db.commit()
            
        except Exception as e:
            logger.error(f"记录查询失败: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()
    
    # API 调用已迁移到 src/clients/tron.py (TronAPIClient)
