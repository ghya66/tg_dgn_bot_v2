"""
API中间件配置

包含：
- 请求日志中间件
- 速率限制中间件（基于 Redis 滑动窗口算法）
"""

import logging
import time
from typing import Callable, Optional
from fastapi import FastAPI, Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from ..common.redis_helper import create_redis_client
from ..config import settings


logger = logging.getLogger(__name__)


# 速率限制配置
class RateLimitConfig:
    """速率限制配置"""
    # 按 IP 限制（针对未认证请求）
    IP_LIMIT_REQUESTS: int = 60  # 每分钟最大请求数
    IP_LIMIT_WINDOW_SECONDS: int = 60  # 时间窗口（秒）

    # 按 API Key 限制（针对已认证请求）
    API_KEY_LIMIT_REQUESTS: int = 300  # 每分钟最大请求数
    API_KEY_LIMIT_WINDOW_SECONDS: int = 60  # 时间窗口（秒）

    # 白名单路径（不受速率限制）
    WHITELIST_PATHS: list = [
        "/health",
        "/api/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    ]

    # Redis key 前缀
    REDIS_KEY_PREFIX: str = "rate_limit:"


# 全局 Redis 客户端（延迟初始化）
_redis_client = None


async def get_redis_client():
    """获取或创建 Redis 客户端"""
    global _redis_client
    if _redis_client is None:
        _redis_client = create_redis_client()
    return _redis_client


async def close_rate_limit_redis():
    """关闭速率限制 Redis 客户端"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def log_requests(request: Request, call_next: Callable) -> Response:
    """
    请求日志中间件

    记录所有API请求的详细信息，并添加 trace_id 关联日志
    """
    from src.common.logging_config import set_trace_id, clear_trace_id, get_trace_id

    start_time = time.time()

    # 设置 trace_id（优先使用请求头中的，否则自动生成）
    trace_id = request.headers.get("X-Trace-ID") or set_trace_id()
    if not request.headers.get("X-Trace-ID"):
        set_trace_id(trace_id)

    # 记录请求信息
    logger.info(
        f"API Request: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    try:
        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录响应信息
        logger.info(
            f"API Response: {request.method} {request.url.path} "
            f"status={response.status_code} time={process_time:.3f}s"
        )

        # 添加处理时间和 trace_id 到响应头
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Trace-ID"] = trace_id

        return response
    finally:
        # 清除 trace_id
        clear_trace_id()


async def check_rate_limit(
    identifier: str,
    limit: int,
    window_seconds: int,
) -> tuple[bool, int, int]:
    """
    检查速率限制（滑动窗口算法）

    Args:
        identifier: 限制标识符（如 IP 或 API Key）
        limit: 时间窗口内最大请求数
        window_seconds: 时间窗口（秒）

    Returns:
        tuple: (是否允许, 剩余请求数, 重置时间戳)
    """
    try:
        redis = await get_redis_client()
        current_time = int(time.time())
        window_start = current_time - window_seconds
        key = f"{RateLimitConfig.REDIS_KEY_PREFIX}{identifier}"

        # 使用 Redis 管道执行原子操作
        pipe = redis.pipeline()

        # 1. 移除过期的请求记录
        pipe.zremrangebyscore(key, 0, window_start)

        # 2. 获取当前窗口内的请求数
        pipe.zcard(key)

        # 3. 添加当前请求（使用时间戳作为分数和成员）
        # 使用 current_time + 微秒确保唯一性
        member = f"{current_time}:{time.time_ns()}"
        pipe.zadd(key, {member: current_time})

        # 4. 设置 key 过期时间
        pipe.expire(key, window_seconds + 1)

        results = await pipe.execute()

        # results[1] 是 zcard 的结果（移除过期记录后的计数）
        current_count = results[1]

        # 计算剩余请求数和重置时间
        remaining = max(0, limit - current_count - 1)  # -1 因为刚添加了一个
        reset_time = current_time + window_seconds

        # 判断是否超过限制
        is_allowed = current_count < limit

        return is_allowed, remaining, reset_time

    except Exception as e:
        # Redis 不可用时，允许请求通过（降级策略）
        logger.warning(f"速率限制检查失败，降级放行: {e}")
        return True, limit, int(time.time()) + window_seconds


def get_client_identifier(request: Request) -> tuple[str, str]:
    """
    获取客户端标识符

    Returns:
        tuple: (标识符类型, 标识符值)
        - 如果有 API Key，返回 ("api_key", key_value)
        - 否则返回 ("ip", client_ip)
    """
    # 检查 API Key（从 header 或 query 参数）
    api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")

    if api_key:
        # 使用 API Key 的哈希值作为标识符（避免在 Redis 中存储完整 key）
        import hashlib
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        return "api_key", f"key:{key_hash}"

    # 使用客户端 IP
    # 支持代理场景：优先使用 X-Forwarded-For
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 取第一个 IP（最原始的客户端 IP）
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    return "ip", f"ip:{client_ip}"


async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """
    速率限制中间件

    使用 Redis 滑动窗口算法限制 API 请求频率：
    - 未认证请求：按 IP 限制，60 次/分钟
    - 已认证请求：按 API Key 限制，300 次/分钟
    - 白名单路径不受限制
    """
    # 检查是否在白名单中
    path = request.url.path
    if path in RateLimitConfig.WHITELIST_PATHS:
        return await call_next(request)

    # 获取客户端标识符
    id_type, identifier = get_client_identifier(request)

    # 根据标识符类型选择限制参数
    if id_type == "api_key":
        limit = RateLimitConfig.API_KEY_LIMIT_REQUESTS
        window = RateLimitConfig.API_KEY_LIMIT_WINDOW_SECONDS
    else:
        limit = RateLimitConfig.IP_LIMIT_REQUESTS
        window = RateLimitConfig.IP_LIMIT_WINDOW_SECONDS

    # 检查速率限制
    is_allowed, remaining, reset_time = await check_rate_limit(
        identifier, limit, window
    )

    if not is_allowed:
        logger.warning(
            f"速率限制触发: {identifier}, path={path}, limit={limit}/{window}s"
        )
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too Many Requests",
                "message": f"请求过于频繁，请在 {window} 秒后重试",
                "retry_after": window,
            },
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(window),
            }
        )

    # 处理请求
    response = await call_next(request)

    # 添加速率限制信息到响应头
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_time)

    return response


def setup_middleware(app: FastAPI):
    """
    设置所有中间件

    Args:
        app: FastAPI应用实例
    """
    # 添加请求日志中间件
    @app.middleware("http")
    async def add_log_requests(request: Request, call_next):
        return await log_requests(request, call_next)

    # 添加速率限制中间件
    @app.middleware("http")
    async def add_rate_limit(request: Request, call_next):
        return await rate_limit_middleware(request, call_next)

    # 添加可信主机中间件（生产环境使用）
    # app.add_middleware(
    #     TrustedHostMiddleware,
    #     allowed_hosts=["example.com", "*.example.com"]
    # )

    # 注意：Redis 连接清理已移至 app.py 的 lifespan 中统一管理

    logger.info("✅ API中间件设置完成（含速率限制: IP=%d/%ds, API_KEY=%d/%ds）",
                RateLimitConfig.IP_LIMIT_REQUESTS,
                RateLimitConfig.IP_LIMIT_WINDOW_SECONDS,
                RateLimitConfig.API_KEY_LIMIT_REQUESTS,
                RateLimitConfig.API_KEY_LIMIT_WINDOW_SECONDS)
