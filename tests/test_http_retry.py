"""
HTTP 重试工具测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx


class TestGetWithRetry:
    """get_with_retry 测试"""
    
    @pytest.mark.asyncio
    async def test_successful_request_no_retry(self):
        """测试成功请求不重试"""
        from src.common.http_utils import get_with_retry
        from src.common.http_client import get_async_client, close_async_client
        
        # 创建 Mock 响应
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        
        client = await get_async_client()
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            resp = await get_with_retry("https://api.example.com/test")
            
            assert resp.status_code == 200
            assert mock_get.call_count == 1  # 只调用一次
        
        await close_async_client()
        print("✅ 成功请求不重试")
    
    @pytest.mark.asyncio
    async def test_retry_on_connect_error_then_success(self):
        """测试连接错误后重试成功"""
        from src.common.http_utils import get_with_retry
        from src.common.http_client import get_async_client, close_async_client
        
        # 创建 Mock 响应
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        
        client = await get_async_client()
        
        call_count = 0
        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.ConnectError("Connection refused")
            return mock_response
        
        with patch.object(client, 'get', side_effect=side_effect):
            resp = await get_with_retry(
                "https://api.example.com/test",
                retries=2,
                retry_delay=0.1
            )
            
            assert resp.status_code == 200
            assert call_count == 2  # 第一次失败，第二次成功
        
        await close_async_client()
        print("✅ 连接错误后重试成功")
    
    @pytest.mark.asyncio
    async def test_retry_on_500_error(self):
        """测试 5xx 错误重试"""
        from src.common.http_utils import get_with_retry
        from src.common.http_client import get_async_client, close_async_client
        
        # 创建 500 错误响应
        mock_request = MagicMock(spec=httpx.Request)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.request = mock_request
        
        client = await get_async_client()
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            with pytest.raises(httpx.HTTPStatusError):
                await get_with_retry(
                    "https://api.example.com/test",
                    retries=2,
                    retry_delay=0.1
                )
            
            assert mock_get.call_count == 3  # 重试 2 次，总共 3 次
        
        await close_async_client()
        print("✅ 5xx 错误重试后仍失败则抛出异常")
    
    @pytest.mark.asyncio
    async def test_no_retry_on_404_error(self):
        """测试 4xx 错误不重试"""
        from src.common.http_utils import get_with_retry
        from src.common.http_client import get_async_client, close_async_client
        
        # 创建 404 错误响应
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        
        client = await get_async_client()
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            resp = await get_with_retry("https://api.example.com/test")
            
            assert resp.status_code == 404
            assert mock_get.call_count == 1  # 不重试
        
        await close_async_client()
        print("✅ 4xx 错误不重试")
    
    @pytest.mark.asyncio
    async def test_timeout_retry(self):
        """测试超时重试"""
        from src.common.http_utils import get_with_retry
        from src.common.http_client import get_async_client, close_async_client
        
        # 创建 Mock 响应
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        
        client = await get_async_client()
        
        call_count = 0
        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise httpx.ReadTimeout("Read timed out")
            return mock_response
        
        with patch.object(client, 'get', side_effect=side_effect):
            resp = await get_with_retry(
                "https://api.example.com/test",
                retries=2,
                retry_delay=0.1
            )
            
            assert resp.status_code == 200
            assert call_count == 3  # 前两次超时，第三次成功
        
        await close_async_client()
        print("✅ 超时重试成功")
    
    @pytest.mark.asyncio
    async def test_exhaust_retries_raises(self):
        """测试重试耗尽后抛出异常"""
        from src.common.http_utils import get_with_retry
        from src.common.http_client import get_async_client, close_async_client
        
        client = await get_async_client()
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")
            
            with pytest.raises(httpx.ConnectError):
                await get_with_retry(
                    "https://api.example.com/test",
                    retries=2,
                    retry_delay=0.1
                )
            
            assert mock_get.call_count == 3  # 总共尝试 3 次
        
        await close_async_client()
        print("✅ 重试耗尽后抛出异常")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
