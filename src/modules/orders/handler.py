"""
订单查询模块主处理器 - 标准化版本

采用最小改动策略，复用现有 get_orders_handler 逻辑
"""

import logging
from typing import List
from telegram.ext import BaseHandler

from src.core.base import BaseModule
from .query_handler import get_orders_handler


logger = logging.getLogger(__name__)


class OrdersModule(BaseModule):
    """
    标准化的订单查询模块
    
    采用包装模式，复用现有 get_orders_handler 的所有功能。
    """
    
    def __init__(self):
        """初始化订单查询模块"""
        logger.info("OrdersModule initialized")
    
    @property
    def module_name(self) -> str:
        """模块名称"""
        return "orders"
    
    def get_handlers(self) -> List[BaseHandler]:
        """获取模块处理器"""
        return [get_orders_handler()]
    
    def validate_config(self) -> bool:
        """验证模块配置"""
        from src.bot_admin.middleware import get_owner_id
        
        owner_id = get_owner_id()
        if not owner_id:
            logger.warning("BOT_OWNER_ID not configured for OrdersModule")
            return False
        
        return True
    
    def on_startup(self) -> None:
        """模块启动时的初始化"""
        logger.info("OrdersModule started")
    
    def on_shutdown(self) -> None:
        """模块关闭时的清理"""
        logger.info("OrdersModule stopped")
