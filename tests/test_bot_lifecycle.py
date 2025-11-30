"""
Bot 生命周期测试
验证启动和停止时资源正确管理
"""

import pytest
import asyncio
import logging

logger = logging.getLogger(__name__)


class TestBotLifecycle:
    """Bot 生命周期测试"""
    
    def test_bot_v2_class_exists(self):
        """测试 Bot 类存在"""
        from src.bot_v2 import TelegramBotV2
        
        bot = TelegramBotV2()
        assert bot is not None
        
        print("✅ TelegramBotV2 类存在")
    
    def test_bootstrap_has_http_client_init(self):
        """测试启动时初始化 HTTP 客户端"""
        import inspect
        from src.bot_v2 import TelegramBotV2
        
        source = inspect.getsource(TelegramBotV2._bootstrap_application)
        
        assert "get_async_client" in source, "应初始化 HTTP 客户端"
        assert "全局 HTTP 客户端已初始化" in source, "应记录初始化日志"
        
        print("✅ 启动时初始化 HTTP 客户端")
    
    def test_stop_has_http_client_close(self):
        """测试停止时关闭 HTTP 客户端"""
        import inspect
        from src.bot_v2 import TelegramBotV2
        
        source = inspect.getsource(TelegramBotV2.stop)
        
        assert "close_async_client" in source, "应关闭 HTTP 客户端"
        
        print("✅ 停止时关闭 HTTP 客户端")
    
    def test_stop_has_redis_disconnect(self):
        """测试停止时断开 Redis"""
        import inspect
        from src.bot_v2 import TelegramBotV2
        
        source = inspect.getsource(TelegramBotV2.stop)
        
        assert "order_manager.disconnect" in source, "应断开 order_manager"
        assert "suffix_manager.disconnect" in source, "应断开 suffix_manager"
        
        print("✅ 停止时断开 Redis 连接")
    
    def test_stop_has_scheduler_shutdown(self):
        """测试停止时关闭定时任务"""
        import inspect
        from src.bot_v2 import TelegramBotV2
        
        source = inspect.getsource(TelegramBotV2.stop)
        
        assert "scheduler.shutdown" in source, "应关闭定时任务调度器"
        
        print("✅ 停止时关闭定时任务调度器")
    
    @pytest.mark.asyncio
    async def test_http_client_lifecycle(self):
        """测试 HTTP 客户端生命周期"""
        from src.common.http_client import (
            get_async_client,
            close_async_client,
            is_client_initialized
        )
        
        # 初始状态
        assert not is_client_initialized(), "初始时不应有客户端"
        
        # 获取客户端
        client = await get_async_client()
        assert client is not None, "应返回客户端"
        assert is_client_initialized(), "获取后应初始化"
        
        # 关闭客户端
        await close_async_client()
        assert not is_client_initialized(), "关闭后不应有客户端"
        
        print("✅ HTTP 客户端生命周期正确")
    
    def test_global_error_handler_exists(self):
        """测试全局错误处理器存在"""
        import inspect
        from src.bot_v2 import TelegramBotV2
        
        assert hasattr(TelegramBotV2, '_global_error_handler'), "应有全局错误处理器"
        
        source = inspect.getsource(TelegramBotV2._global_error_handler)
        assert "context.error" in source, "应记录错误"
        assert "发生错误" in source, "应通知用户"
        
        print("✅ 全局错误处理器存在")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
