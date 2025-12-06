"""
API应用主文件
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from .routes import router as api_router, close_energy_api_client
from .middleware import setup_middleware, close_rate_limit_redis


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("API application starting up...")
    yield
    # 关闭时执行
    logger.info("API application shutting down, cleaning up resources...")
    try:
        # 关闭能量 API 客户端
        await close_energy_api_client()
        logger.debug("Energy API client closed")
    except Exception as e:
        logger.error(f"Error closing energy API client: {e}")

    try:
        # 关闭速率限制 Redis 客户端
        await close_rate_limit_redis()
        logger.debug("Rate limit Redis client closed")
    except Exception as e:
        logger.error(f"Error closing rate limit Redis: {e}")

    logger.info("API application cleanup complete")


def create_api_app() -> FastAPI:
    """创建FastAPI应用实例"""

    app = FastAPI(
        title="TG Bot API",
        description="Telegram Bot REST API接口",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 设置其他中间件
    setup_middleware(app)

    # 注册路由
    app.include_router(api_router, prefix="/api")

    # 全局异常处理
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "status_code": exc.status_code}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "status_code": 500}
        )

    return app
