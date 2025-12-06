"""
管理员模块主处理器 - 标准化版本

采用最小改动策略：
- 继承 BaseModule 接口
- 复用现有 AdminHandler 所有逻辑
- 不修改原有功能代码
"""

import logging

from telegram.ext import BaseHandler

from src.bot_admin.handler import admin_handler
from src.core.base import BaseModule


logger = logging.getLogger(__name__)


class AdminModule(BaseModule):
    """
    标准化的管理员模块

    采用包装模式，复用现有 AdminHandler 的所有功能。
    这种方式最大程度保证了功能稳定性和向后兼容性。
    """

    def __init__(self):
        """初始化管理员模块"""
        # 复用全局 admin_handler 实例
        self._admin_handler = admin_handler
        logger.info("AdminModule initialized (wrapping existing AdminHandler)")

    @property
    def module_name(self) -> str:
        """模块名称"""
        return "admin"

    def get_handlers(self) -> list[BaseHandler]:
        """
        获取模块处理器

        直接返回现有 AdminHandler 的 ConversationHandler，
        不做任何修改，保证功能完全一致。
        """
        return [self._admin_handler.get_conversation_handler()]

    def validate_config(self) -> bool:
        """验证模块配置"""
        from src.bot_admin.middleware import get_owner_id

        owner_id = get_owner_id()
        if not owner_id:
            logger.warning("BOT_OWNER_ID not configured for AdminModule")
            return False

        logger.info(f"AdminModule configured with owner_id: {owner_id}")
        return True

    def on_startup(self) -> None:
        """模块启动时的初始化"""
        logger.info("AdminModule started")

    def on_shutdown(self) -> None:
        """模块关闭时的清理"""
        logger.info("AdminModule stopped")
