"""
全局 HTTP 客户端管理模块

提供连接池复用，降低延迟与资源消耗。
支持 keep-alive 和连接池（httpx.AsyncClient 默认支持）。
"""

import logging
from typing import Optional

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

# 全局异步客户端实例
_async_client: Optional[httpx.AsyncClient] = None


async def get_async_client() -> httpx.AsyncClient:
    """
    获取全局异步 HTTP 客户端
    
    使用连接池复用，避免频繁创建/销毁连接。
    
    Returns:
        httpx.AsyncClient 实例
    """
    global _async_client
    
    if _async_client is None:
        _async_client = httpx.AsyncClient(
            timeout=settings.api_timeout_default_secs,
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0,
            ),
            follow_redirects=True,
        )
        logger.info(
            "全局 HTTP 客户端已初始化 (timeout=%ss, keepalive=20, max_conn=100)",
            settings.api_timeout_default_secs
        )
    
    return _async_client


async def close_async_client() -> None:
    """
    关闭全局异步 HTTP 客户端
    
    应在应用关闭时调用，优雅释放连接资源。
    """
    global _async_client
    
    if _async_client is not None:
        await _async_client.aclose()
        _async_client = None
        logger.info("全局 HTTP 客户端已关闭")


def is_client_initialized() -> bool:
    """检查客户端是否已初始化"""
    return _async_client is not None
