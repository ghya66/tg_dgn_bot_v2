"""
统一文案服务 - 向后兼容层

⚠️ 注意：此模块已重构为重定向层
所有功能已统一到 src.utils.content_helper，此处保留向后兼容接口。

新代码请直接使用：
    from src.utils.content_helper import get_content, clear_content_cache
"""

import logging

from src.utils.content_helper import clear_content_cache as _clear_cache
from src.utils.content_helper import get_content as _get_content


logger = logging.getLogger(__name__)


def get_welcome_message() -> str:
    """
    获取欢迎语

    向后兼容接口，内部重定向到 content_helper
    """
    from src.config import settings

    return _get_content("welcome_message", default=settings.welcome_message)


def get_free_clone_message() -> str:
    """
    获取免费克隆文案

    向后兼容接口，内部重定向到 content_helper
    """
    from src.config import settings

    return _get_content("free_clone_message", default=settings.free_clone_message)


def get_support_contact() -> str:
    """
    获取客服联系方式

    向后兼容接口，内部重定向到 content_helper
    """
    from src.config import settings

    return _get_content("support_contact", default=settings.support_contact)


def clear_content_cache(key: str | None = None):
    """
    清除文案缓存

    向后兼容接口，内部重定向到 content_helper.clear_content_cache

    Args:
        key: 指定键，为 None 时清除所有
    """
    _clear_cache(key)
    logger.debug(f"[兼容层] 缓存清除请求已转发: {key or '全部'}")
