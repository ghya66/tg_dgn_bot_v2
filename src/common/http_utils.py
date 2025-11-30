"""
HTTP 工具模块

提供统一的 GET-with-retry 封装，用于只读查询操作。

⚠️ 警告：
- 仅用于纯读取、不改变状态的操作
- 禁止用于链上交易、订单状态变更等写操作
"""

import asyncio
import logging
from typing import Optional, Dict, Any

import httpx

from src.common.http_client import get_async_client
from src.config import settings

logger = logging.getLogger(__name__)


async def get_with_retry(
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    retries: int = 2,
    retry_delay: float = 0.5,
) -> httpx.Response:
    """
    带重试的 GET 请求封装
    
    用于只读查询操作，如：
    - 获取 OKX USDT-CNY 汇率
    - 查询 Tron 地址余额
    - 查询订单状态（只读）
    
    ⚠️ 禁止用于：
    - 发送链上交易（TRX/USDT 转账）
    - 改变订单状态
    - 开通 Premium 等非幂等操作
    
    Args:
        url: 请求 URL
        params: 查询参数
        headers: 请求头
        timeout: 超时时间（秒），默认使用配置值
        retries: 重试次数（默认2，总共尝试3次）
        retry_delay: 重试间隔（秒）
    
    Returns:
        httpx.Response 响应对象
    
    Raises:
        httpx.HTTPStatusError: 超过重试次数后仍失败
        httpx.ConnectError: 网络连接错误
        httpx.ReadTimeout: 读取超时
    """
    client = await get_async_client()
    timeout = timeout or settings.api_timeout_default_secs
    
    last_exc: Optional[Exception] = None
    
    for attempt in range(retries + 1):
        try:
            resp = await client.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout
            )
            
            # 对 5xx 服务器错误进行重试
            if resp.status_code >= 500:
                logger.warning(
                    f"服务器错误 {resp.status_code}，URL: {url}，尝试 {attempt + 1}/{retries + 1}"
                )
                raise httpx.HTTPStatusError(
                    f"Server error: {resp.status_code}",
                    request=resp.request,
                    response=resp,
                )
            
            # 4xx 客户端错误不重试，直接返回
            return resp
            
        except (
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.NetworkError,
            httpx.HTTPStatusError,
        ) as e:
            last_exc = e
            
            if attempt < retries:
                logger.warning(
                    f"请求失败，将在 {retry_delay}s 后重试 "
                    f"(尝试 {attempt + 1}/{retries + 1}): {e}"
                )
                await asyncio.sleep(retry_delay)
            else:
                logger.error(
                    f"请求失败，已达最大重试次数 ({retries + 1}): {e}"
                )
                raise
    
    # 理论上不会到这里，但为了类型安全
    if last_exc:
        raise last_exc
    raise RuntimeError("Unexpected state in get_with_retry")
