"""
统一文案服务

提供文案的读取和缓存管理，优先从数据库读取，回退到环境变量。
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 内存缓存
_content_cache = {}


def get_welcome_message() -> str:
    """获取欢迎语"""
    return _get_content("welcome_message", _get_default_welcome())


def get_free_clone_message() -> str:
    """获取免费克隆文案"""
    return _get_content("free_clone_message", _get_default_clone())


def get_support_contact() -> str:
    """获取客服联系方式"""
    return _get_content("support_contact", _get_default_support())


def _get_content(key: str, default: str) -> str:
    """
    获取文案内容
    
    优先级：数据库 > 环境变量 > 默认值
    """
    # 检查缓存
    if key in _content_cache:
        return _content_cache[key]
    
    # 从数据库读取
    try:
        from src.bot_admin.config_manager import config_manager
        db_value = config_manager.get_content(key, "")
        if db_value:
            _content_cache[key] = db_value
            return db_value
    except Exception as e:
        logger.warning(f"从数据库读取文案失败 ({key}): {e}")
    
    # 回退到默认值
    return default


def clear_content_cache(key: Optional[str] = None):
    """
    清除文案缓存
    
    Args:
        key: 指定键，为 None 时清除所有
    """
    global _content_cache
    if key:
        _content_cache.pop(key, None)
        logger.debug(f"清除文案缓存: {key}")
    else:
        _content_cache.clear()
        logger.debug("清除所有文案缓存")


def _get_default_welcome() -> str:
    """获取默认欢迎语"""
    from src.config import settings
    return getattr(settings, 'welcome_message', '欢迎使用 Bot！')


def _get_default_clone() -> str:
    """获取默认克隆文案"""
    from src.config import settings
    return getattr(settings, 'free_clone_message', '免费克隆功能')


def _get_default_support() -> str:
    """获取默认客服联系"""
    from src.config import settings
    return getattr(settings, 'support_contact', '@support')
