#!/usr/bin/env python3
"""
Render.com 专用入口点
支持 Webhook 模式运行 Telegram Bot

与 src/bot_v2.py 的区别：
- 使用 Webhook 模式而非 Polling 模式
- 复用 TelegramBotV2 的初始化逻辑
- 添加 /webhook 端点处理 Telegram 更新
- 适配 Render.com 的端口和健康检查要求
"""

import asyncio
import logging
import os
import signal
import sys

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update

from src.bot_v2 import TelegramBotV2
from src.common.logging_config import setup_logging
from src.database import check_database_health
from src.payments.order import order_manager

# 配置日志
log_format_json = os.environ.get("LOG_FORMAT", "").lower() == "json"
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
setup_logging(level=log_level, json_format=log_format_json)
logger = logging.getLogger(__name__)


class RenderWebhookServer:
    """Render Webhook 服务器

    封装 TelegramBotV2，添加 Webhook 模式支持。
    复用现有的 Bot 初始化逻辑和 FastAPI 应用。
    """

    def __init__(self):
        self.bot: TelegramBotV2 | None = None
        self.app: FastAPI | None = None
        self._shutdown_event = asyncio.Event()

    async def initialize(self):
        """初始化 Bot 和 FastAPI 应用"""
        logger.info("🚀 初始化 Render Webhook 服务器...")

        # 1. 创建并初始化 TelegramBotV2
        self.bot = TelegramBotV2()
        await self.bot.initialize()
        logger.info("✅ TelegramBotV2 初始化完成")

        # 2. 获取 FastAPI 应用实例（在 initialize() 中已创建）
        self.app = self.bot.api_app
        if self.app is None:
            raise RuntimeError("FastAPI 应用未正确初始化")

        # 3. 初始化所有模块（注册 handlers）
        self.bot.registry.initialize_all(self.bot.app)
        logger.info("✅ 所有模块已初始化")

        # 4. 添加 Webhook 端点
        self._setup_webhook_routes()

        # 5. 初始化 Telegram Application（不启动 polling）
        await self.bot.app.initialize()
        await self.bot.app.start()
        logger.info("✅ Telegram Application 已启动")

        # 6. 设置 Telegram Webhook URL
        await self._setup_telegram_webhook()

        # 7. 初始化定时任务
        await self.bot._init_scheduler()

        # 8. 检查生产环境配置
        await self.bot._check_production_config()

        # 9. 启动 TRX 支付监听器
        await self.bot._start_payment_monitor()

        logger.info("✅ Render Webhook 服务器初始化完成")

    def _setup_webhook_routes(self):
        """设置 Webhook 路由"""

        @self.app.post("/webhook")
        async def telegram_webhook(request: Request):
            """处理 Telegram Webhook 请求"""
            try:
                data = await request.json()
                update = Update.de_json(data, self.bot.app.bot)
                await self.bot.app.process_update(update)
                return JSONResponse({"ok": True})
            except Exception as e:
                logger.error(f"Webhook 处理错误: {e}", exc_info=True)
                return JSONResponse({"ok": False, "error": str(e)})

        @self.app.get("/health")
        async def root_health_check():
            """根路径健康检查（Render 使用此端点）"""
            try:
                bot_info = await self.bot.app.bot.get_me()
                db_healthy = False
                try:
                    db_healthy = check_database_health()
                except Exception:
                    pass
                redis_healthy = False
                try:
                    redis_healthy = order_manager.redis_client is not None
                except Exception:
                    pass
                return JSONResponse({
                    "status": "healthy",
                    "bot_username": bot_info.username,
                    "bot_id": bot_info.id,
                    "mode": "webhook",
                    "platform": "render",
                    "database": db_healthy,
                    "redis": redis_healthy
                })
            except Exception as e:
                logger.error(f"健康检查失败: {e}")
                return JSONResponse({"status": "unhealthy", "error": str(e)}, status_code=503)

        @self.app.get("/")
        async def root():
            """根路径（Render 用于检测服务是否启动）"""
            return JSONResponse({
                "service": "tg-dgn-bot",
                "version": "2.0.2",
                "status": "running",
                "mode": "webhook",
                "platform": "render"
            })

        logger.info("✅ Webhook 路由已注册: /, /health, /webhook")

    async def _setup_telegram_webhook(self):
        """设置 Telegram Webhook URL"""
        webhook_url = os.environ.get("BOT_WEBHOOK_URL")
        webhook_secret = os.environ.get("WEBHOOK_SECRET", "")

        if not webhook_url:
            logger.error("❌ BOT_WEBHOOK_URL 环境变量未设置")
            sys.exit(1)

        try:
            await self.bot.app.bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ 旧的 Webhook 已删除")

            webhook_set = await self.bot.app.bot.set_webhook(
                url=webhook_url,
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True,
                secret_token=webhook_secret if webhook_secret else None
            )

            if webhook_set:
                logger.info(f"✅ Telegram Webhook 设置成功: {webhook_url}")
                webhook_info = await self.bot.app.bot.get_webhook_info()
                logger.info(f"📌 Webhook 信息: url={webhook_info.url}, "
                           f"pending_updates={webhook_info.pending_update_count}")
            else:
                logger.warning(f"⚠️ Telegram Webhook 设置返回 False: {webhook_url}")

        except Exception as e:
            logger.error(f"❌ 设置 Telegram Webhook 失败: {e}")
            raise

    async def run(self):
        """运行服务器"""
        port = int(os.environ.get("PORT", 10000))
        host = os.environ.get("BOT_SERVICE_HOST", "0.0.0.0")

        logger.info(f"🌐 启动 Webhook 服务器: {host}:{port}")

        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            timeout_keep_alive=30,
            limit_concurrency=100
        )
        server = uvicorn.Server(config)

        self._setup_signal_handlers()

        try:
            await server.serve()
        except Exception as e:
            logger.error(f"❌ 服务器运行错误: {e}")
            raise
        finally:
            await self.shutdown()

    def _setup_signal_handlers(self):
        """设置信号处理器（优雅关闭）"""
        loop = asyncio.get_event_loop()

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(
                    sig,
                    lambda: asyncio.create_task(self._handle_signal())
                )
            except NotImplementedError:
                pass

    async def _handle_signal(self):
        """处理关闭信号"""
        logger.info("📥 收到关闭信号，开始优雅关闭...")
        self._shutdown_event.set()

    async def shutdown(self):
        """关闭服务器并清理资源"""
        logger.info("⏹️ 正在关闭 Webhook 服务器...")

        if self.bot:
            try:
                await self.bot.app.bot.delete_webhook()
                logger.info("✅ Telegram Webhook 已删除")
            except Exception as e:
                logger.warning(f"删除 Webhook 失败: {e}")

            try:
                from src.modules.trx_exchange.payment_monitor import stop_payment_monitor
                stop_payment_monitor()
                logger.info("✅ TRX 支付监听器已停止")
            except Exception as e:
                logger.warning(f"停止支付监听器失败: {e}")

            if self.bot.scheduler:
                try:
                    self.bot.scheduler.shutdown(wait=False)
                    logger.info("✅ 定时任务调度器已停止")
                except Exception as e:
                    logger.warning(f"停止调度器失败: {e}")

            try:
                await self.bot.app.stop()
                await self.bot.app.shutdown()
                logger.info("✅ Telegram Application 已停止")
            except Exception as e:
                logger.warning(f"停止 Telegram Application 失败: {e}")

            try:
                from src.payments.suffix_manager import suffix_manager
                await order_manager.disconnect()
                await suffix_manager.disconnect()
                logger.info("✅ Redis 连接已断开")
            except Exception as e:
                logger.warning(f"断开 Redis 失败: {e}")

            try:
                from src.common.http_client import close_async_client
                await close_async_client()
                logger.info("✅ HTTP 客户端已关闭")
            except Exception as e:
                logger.warning(f"关闭 HTTP 客户端失败: {e}")

        logger.info("✅ Webhook 服务器已完全关闭")


async def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("🚀 TG DGN Bot - Render Webhook Mode")
    logger.info("=" * 50)

    server = RenderWebhookServer()
    try:
        await server.initialize()
        await server.run()
    except KeyboardInterrupt:
        logger.info("👋 收到键盘中断信号")
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

