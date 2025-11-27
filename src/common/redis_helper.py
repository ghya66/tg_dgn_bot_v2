"""
Redis 连接辅助模块
支持 Zeabur 自动注入的环境变量和连接字符串
"""
import redis.asyncio as redis
from typing import Optional
import logging

from ..config import settings

logger = logging.getLogger(__name__)


def get_redis_kwargs(decode_responses: bool = True) -> dict:
    """
    获取 Redis 连接参数
    优先使用 REDIS_CONNECTION_STRING（Zeabur 注入）
    否则使用分离的 host/port/password 配置
    """
    # 如果有连接字符串，解析它
    if settings.redis_connection_string:
        # 连接字符串格式: redis://[:password@]host:port[/db]
        return {
            "url": settings.redis_connection_string,
            "decode_responses": decode_responses,
        }
    
    # 使用分离的配置
    return {
        "host": settings.redis_host,
        "port": settings.redis_port,
        "db": settings.redis_db,
        "password": settings.redis_password or None,
        "decode_responses": decode_responses,
    }


def create_redis_client(decode_responses: bool = True) -> redis.Redis:
    """
    创建 Redis 客户端
    """
    kwargs = get_redis_kwargs(decode_responses)
    
    if "url" in kwargs:
        url = kwargs.pop("url")
        return redis.Redis.from_url(url, **kwargs)
    
    return redis.Redis(**kwargs)


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
