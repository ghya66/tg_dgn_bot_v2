"""
健康检查模块主处理器 - 标准化版本
"""

import logging

from telegram.ext import BaseHandler, CommandHandler

from src.core.base import BaseModule

from .service import health_command


logger = logging.getLogger(__name__)


class HealthModule(BaseModule):
    """
    标准化的健康检查模块
    """

    def __init__(self):
        """初始化健康检查模块"""
        logger.info("HealthModule initialized")

    @property
    def module_name(self) -> str:
        """模块名称"""
        return "health"

    def get_handlers(self) -> list[BaseHandler]:
        """获取模块处理器"""
        return [CommandHandler("health", health_command)]

    def validate_config(self) -> bool:
        """验证模块配置"""
        return True

    def on_startup(self) -> None:
        """模块启动时的初始化"""
        logger.info("HealthModule started")

    def on_shutdown(self) -> None:
        """模块关闭时的清理"""
        logger.info("HealthModule stopped")
