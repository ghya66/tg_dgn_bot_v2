"""
全局 HTTP 客户端测试
"""

import pytest


class TestHttpClient:
    """全局 HTTP 客户端测试"""
    
    def test_http_client_module_exists(self):
        """测试 HTTP 客户端模块存在"""
        from src.common import http_client
        
        assert hasattr(http_client, 'get_async_client'), "应有 get_async_client 函数"
        assert hasattr(http_client, 'close_async_client'), "应有 close_async_client 函数"
        assert hasattr(http_client, 'is_client_initialized'), "应有 is_client_initialized 函数"
        
        print("✅ HTTP 客户端模块存在")
    
    @pytest.mark.asyncio
    async def test_get_async_client_returns_client(self):
        """测试 get_async_client 返回客户端"""
        from src.common.http_client import get_async_client, close_async_client
        import httpx
        
        client = await get_async_client()
        
        assert isinstance(client, httpx.AsyncClient), "应返回 AsyncClient 实例"
        
        # 清理
        await close_async_client()
        
        print("✅ get_async_client 返回正确的客户端")
    
    @pytest.mark.asyncio
    async def test_client_is_singleton(self):
        """测试客户端是单例"""
        from src.common.http_client import get_async_client, close_async_client
        
        client1 = await get_async_client()
        client2 = await get_async_client()
        
        assert client1 is client2, "多次调用应返回同一实例"
        
        # 清理
        await close_async_client()
        
        print("✅ HTTP 客户端是单例")
    
    @pytest.mark.asyncio
    async def test_close_client(self):
        """测试关闭客户端"""
        from src.common.http_client import get_async_client, close_async_client, is_client_initialized
        
        await get_async_client()
        assert is_client_initialized(), "初始化后应为 True"
        
        await close_async_client()
        assert not is_client_initialized(), "关闭后应为 False"
        
        print("✅ 关闭客户端正常")
    
    def test_bot_bootstrap_initializes_client(self):
        """测试 Bot 启动时初始化客户端"""
        import inspect
        from src.bot_v2 import TelegramBotV2
        
        source = inspect.getsource(TelegramBotV2._bootstrap_application)
        
        assert "get_async_client" in source, "_bootstrap_application 应初始化 HTTP 客户端"
        
        print("✅ Bot 启动时初始化 HTTP 客户端")
    
    def test_bot_stop_closes_client(self):
        """测试 Bot 停止时关闭客户端"""
        import inspect
        from src.bot_v2 import TelegramBotV2
        
        source = inspect.getsource(TelegramBotV2.stop)
        
        assert "close_async_client" in source, "stop 方法应关闭 HTTP 客户端"
        
        print("✅ Bot 停止时关闭 HTTP 客户端")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
