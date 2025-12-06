"""
Redis 连接辅助模块
支持 Zeabur 自动注入的环境变量和连接字符串
包含自动重连机制和健康检查
"""

import asyncio
import logging

import redis.asyncio as redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import (
    BusyLoadingError,
)
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
)
from redis.exceptions import (
    TimeoutError as RedisTimeoutError,
)

from ..config import settings


logger = logging.getLogger(__name__)

# 重连配置
REDIS_RETRY_ON_TIMEOUT = True
REDIS_SOCKET_TIMEOUT = 5.0  # 秒
REDIS_SOCKET_CONNECT_TIMEOUT = 5.0  # 秒
REDIS_RETRY_ATTEMPTS = 3
REDIS_HEALTH_CHECK_INTERVAL = 30  # 秒


def get_redis_kwargs(decode_responses: bool = True) -> dict:
    """
    获取 Redis 连接参数
    优先使用 REDIS_CONNECTION_STRING（Zeabur 注入）
    否则使用分离的 host/port/password 配置

    包含重连和超时配置以提高生产环境稳定性
    """
    # 创建重试策略：指数退避，最多重试 REDIS_RETRY_ATTEMPTS 次
    retry = Retry(
        ExponentialBackoff(cap=10, base=0.1),  # 最大退避 10 秒，基础 0.1 秒
        retries=REDIS_RETRY_ATTEMPTS,
        supported_errors=(RedisConnectionError, RedisTimeoutError, BusyLoadingError),
    )

    # 基础配置
    base_kwargs = {
        "decode_responses": decode_responses,
        "retry_on_timeout": REDIS_RETRY_ON_TIMEOUT,
        "socket_timeout": REDIS_SOCKET_TIMEOUT,
        "socket_connect_timeout": REDIS_SOCKET_CONNECT_TIMEOUT,
        "retry": retry,
        "health_check_interval": REDIS_HEALTH_CHECK_INTERVAL,
    }

    # 如果有连接字符串，解析它
    if settings.redis_connection_string:
        # 连接字符串格式: redis://[:password@]host:port[/db]
        return {
            "url": settings.redis_connection_string,
            **base_kwargs,
        }

    # 使用分离的配置
    return {
        "host": settings.redis_host,
        "port": settings.redis_port,
        "db": settings.redis_db,
        "password": settings.redis_password or None,
        **base_kwargs,
    }


def create_redis_client(decode_responses: bool = True) -> redis.Redis:
    """
    创建 Redis 客户端

    包含以下生产环境优化：
    - retry_on_timeout: 超时自动重试
    - socket_timeout: 操作超时保护
    - socket_connect_timeout: 连接超时保护
    - retry: 指数退避重连策略
    - health_check_interval: 定期健康检查
    """
    kwargs = get_redis_kwargs(decode_responses)

    if "url" in kwargs:
        url = kwargs.pop("url")
        client = redis.Redis.from_url(url, **kwargs)
    else:
        client = redis.Redis(**kwargs)

    logger.debug(
        "创建 Redis 客户端: retry_on_timeout=%s, socket_timeout=%s, retries=%s",
        REDIS_RETRY_ON_TIMEOUT,
        REDIS_SOCKET_TIMEOUT,
        REDIS_RETRY_ATTEMPTS,
    )

    return client


async def check_redis_connection() -> bool:
    """
    检查 Redis 连接是否可用
    """
    try:
        client = create_redis_client()
        await client.ping()
        await client.close()
        return True
    except Exception as e:
        logger.warning(f"Redis 连接检查失败: {e}")
        return False


async def execute_with_retry(client: redis.Redis, operation: str, *args, max_retries: int = 3, **kwargs):
    """
    带重试的 Redis 操作执行器

    用于需要额外重试逻辑的复杂操作（如 Lua 脚本）

    Args:
        client: Redis 客户端
        operation: 操作名称（如 'get', 'set', 'eval'）
        *args: 操作参数
        max_retries: 最大重试次数
        **kwargs: 操作关键字参数

    Returns:
        操作结果

    Raises:
        最后一次重试的异常
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            method = getattr(client, operation)
            return await method(*args, **kwargs)
        except (RedisConnectionError, RedisTimeoutError, BusyLoadingError) as e:
            last_error = e
            wait_time = min(2**attempt * 0.1, 5)  # 指数退避，最大 5 秒
            logger.warning(
                "Redis 操作 %s 失败 (尝试 %d/%d): %s，%s 秒后重试", operation, attempt + 1, max_retries, e, wait_time
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)

    logger.error("Redis 操作 %s 在 %d 次重试后仍然失败", operation, max_retries)
    raise last_error
