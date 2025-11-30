"""
帮助模块主处理器 - 标准化版本
"""

import logging
from typing import List
from telegram import Update
from telegram.ext import (
    ContextTypes,
    BaseHandler,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)

from src.core.base import BaseModule
from src.common.conversation_wrapper import SafeConversationHandler

from .messages import HelpMessages
from .keyboards import HelpKeyboards


logger = logging.getLogger(__name__)

# 对话状态
SHOWING_HELP = 0


class HelpModule(BaseModule):
    """标准化的帮助模块"""
    
    def __init__(self):
        """初始化帮助模块"""
        logger.info("HelpModule initialized")
    
    @property
    def module_name(self) -> str:
        """模块名称"""
        return "help"
    
    def get_handlers(self) -> List[BaseHandler]:
        """获取模块处理器"""
        return [self._create_conversation_handler()]
    
    def _create_conversation_handler(self):
        """创建对话处理器"""
        return SafeConversationHandler.create(
            entry_points=[
                CommandHandler("help", self.show_help),
                CallbackQueryHandler(self.show_help, pattern="^menu_help$"),
            ],
            states={
                SHOWING_HELP: [
                    CallbackQueryHandler(self.show_category, pattern="^help_(basic|payment|services|query|faq|quick)$"),
                    CallbackQueryHandler(self.show_help, pattern="^help_back$"),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
            ],
            name="help"
        )
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """显示帮助主菜单"""
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                HelpMessages.MAIN_HELP,
                parse_mode="HTML",
                reply_markup=HelpKeyboards.main_menu()
            )
        else:
            await update.message.reply_text(
                HelpMessages.MAIN_HELP,
                parse_mode="HTML",
                reply_markup=HelpKeyboards.main_menu()
            )
        
        return SHOWING_HELP
    
    async def show_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """显示具体分类的帮助"""
        query = update.callback_query
        await query.answer()
        
        category = query.data.replace("help_", "")
        
        # 静态内容
        static_content = {
            "basic": HelpMessages.BASIC_HELP,
            "faq": HelpMessages.FAQ,
            "quick": HelpMessages.QUICK_START,
        }
        
        # 动态内容（实时读取配置）
        if category == "payment":
            content = HelpMessages.get_payment_help()
        elif category == "services":
            content = HelpMessages.get_services_help()
        elif category == "query":
            content = HelpMessages.get_query_help()
        else:
            content = static_content.get(category, HelpMessages.MAIN_HELP)
        
        await query.edit_message_text(
            content,
            parse_mode="HTML",
            reply_markup=HelpKeyboards.back_buttons()
        )
        
        return SHOWING_HELP
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """取消操作"""
        from src.common.navigation_manager import NavigationManager
        return await NavigationManager.cleanup_and_show_main_menu(update, context)
