"""能量订单状态同步任务测试"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.tasks.energy_sync import EnergySyncTask, get_energy_sync_task


class TestEnergySyncTask:
    """EnergySyncTask 测试"""
    
    def test_map_api_status_completed(self):
        """测试状态映射：成功"""
        task = EnergySyncTask()
        data = {"status": 1, "hash": "abc123def456"}
        assert task._map_api_status(data) == "COMPLETED"
    
    def test_map_api_status_failed(self):
        """测试状态映射：失败"""
        task = EnergySyncTask()
        data = {"status": 0, "hash": ""}
        assert task._map_api_status(data) == "FAILED"
    
    def test_map_api_status_processing(self):
        """测试状态映射：处理中（hash=Waiting）"""
        task = EnergySyncTask()
        data = {"status": 1, "hash": "Waiting"}  # 即使 status=1，hash=Waiting 也是处理中
        assert task._map_api_status(data) == "PROCESSING"
    
    def test_map_api_status_unknown(self):
        """测试状态映射：未知状态"""
        task = EnergySyncTask()
        data = {"status": 99, "hash": "something"}
        assert task._map_api_status(data) == "PROCESSING"
    
    def test_map_api_status_missing_hash(self):
        """测试状态映射：缺少 hash 字段"""
        task = EnergySyncTask()
        data = {"status": 1}  # 没有 hash 字段
        assert task._map_api_status(data) == "COMPLETED"
    
    def test_map_api_status_failed_with_empty_hash(self):
        """测试状态映射：失败且 hash 为空"""
        task = EnergySyncTask()
        data = {"status": 0, "hash": ""}
        assert task._map_api_status(data) == "FAILED"
    
    def test_set_bot(self):
        """测试设置 Bot 实例"""
        task = EnergySyncTask()
        mock_bot = MagicMock()
        task.set_bot(mock_bot)
        assert task._bot is mock_bot
    
    @pytest.mark.asyncio
    async def test_sync_single_order_success(self):
        """测试同步单个订单：成功"""
        task = EnergySyncTask()
        
        mock_client = AsyncMock()
        mock_client.query_order.return_value = MagicMock(
            data={"status": 1, "hash": "abc123"}
        )
        
        order = {
            "order_id": "ENERGY_001",
            "api_order_id": "12345",
            "status": "PROCESSING",
            "user_id": 10001,
            "energy_amount": 65000,
        }
        
        with patch.object(task, '_update_order_status') as mock_update:
            with patch.object(task, '_notify_user', new_callable=AsyncMock):
                await task._sync_single_order(mock_client, order)
                mock_update.assert_called_once_with("ENERGY_001", "COMPLETED", "abc123")
    
    @pytest.mark.asyncio
    async def test_sync_single_order_no_change(self):
        """测试同步单个订单：状态未变化"""
        task = EnergySyncTask()
        
        mock_client = AsyncMock()
        mock_client.query_order.return_value = MagicMock(
            data={"status": 1, "hash": "Waiting"}
        )
        
        order = {
            "order_id": "ENERGY_001",
            "api_order_id": "12345",
            "status": "PROCESSING",  # 当前状态已经是 PROCESSING
            "user_id": 10001,
            "energy_amount": 65000,
        }
        
        with patch.object(task, '_update_order_status') as mock_update:
            await task._sync_single_order(mock_client, order)
            # 状态没变，不应该调用更新
            mock_update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_sync_single_order_not_found(self):
        """测试同步单个订单：订单不存在"""
        from src.modules.energy.client import EnergyAPIError, EnergyAPIClient
        
        task = EnergySyncTask()
        
        mock_client = AsyncMock()
        mock_client.query_order.side_effect = EnergyAPIError(
            EnergyAPIClient.CODE_ORDER_NOT_FOUND, "订单不存在"
        )
        
        order = {
            "order_id": "ENERGY_001",
            "api_order_id": "99999",
            "status": "PROCESSING",
            "user_id": 10001,
            "energy_amount": 65000,
        }
        
        # 不应抛出异常
        await task._sync_single_order(mock_client, order)
    
    @pytest.mark.asyncio
    async def test_sync_single_order_empty_data(self):
        """测试同步单个订单：API 返回空数据"""
        task = EnergySyncTask()
        
        mock_client = AsyncMock()
        mock_client.query_order.return_value = MagicMock(data=None)
        
        order = {
            "order_id": "ENERGY_001",
            "api_order_id": "12345",
            "status": "PROCESSING",
            "user_id": 10001,
            "energy_amount": 65000,
        }
        
        with patch.object(task, '_update_order_status') as mock_update:
            await task._sync_single_order(mock_client, order)
            # 空数据不应该调用更新
            mock_update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_notify_user_completed(self):
        """测试通知用户：订单完成"""
        task = EnergySyncTask()
        mock_bot = AsyncMock()
        task.set_bot(mock_bot)
        
        order = {
            "order_id": "ENERGY_001",
            "user_id": 10001,
            "energy_amount": 65000,
        }
        
        await task._notify_user(order, "COMPLETED", "abc123def456")
        
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs["chat_id"] == 10001
        assert "能量订单已完成" in call_args.kwargs["text"]
    
    @pytest.mark.asyncio
    async def test_notify_user_failed(self):
        """测试通知用户：订单失败"""
        task = EnergySyncTask()
        mock_bot = AsyncMock()
        task.set_bot(mock_bot)
        
        order = {
            "order_id": "ENERGY_001",
            "user_id": 10001,
            "energy_amount": 65000,
        }
        
        await task._notify_user(order, "FAILED", "")
        
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs["chat_id"] == 10001
        assert "能量订单失败" in call_args.kwargs["text"]
    
    @pytest.mark.asyncio
    async def test_notify_user_no_bot(self):
        """测试通知用户：未设置 Bot"""
        task = EnergySyncTask()
        # 不设置 bot
        
        order = {
            "order_id": "ENERGY_001",
            "user_id": 10001,
            "energy_amount": 65000,
        }
        
        # 不应抛出异常
        await task._notify_user(order, "COMPLETED", "abc123")


class TestGetEnergySyncTask:
    """get_energy_sync_task 测试"""

    def test_get_energy_sync_task_singleton(self):
        """测试单例模式"""
        # 重置全局实例
        import src.tasks.energy_sync as module
        module._sync_task = None

        task1 = get_energy_sync_task()
        task2 = get_energy_sync_task()

        assert task1 is task2


class TestEnergySyncURLParams:
    """测试 EnergyAPIClient 使用正确的 URL 参数"""

    @pytest.mark.asyncio
    async def test_sync_orders_uses_config_urls(self):
        """测试 sync_orders 使用配置中的 URL 参数"""
        from src.config import settings

        task = EnergySyncTask()

        # Mock _get_pending_orders 返回一个订单
        mock_orders = [{
            "order_id": "ENERGY_TEST",
            "api_order_id": "12345",
            "status": "PROCESSING",
            "user_id": 10001,
            "energy_amount": 65000,
        }]

        with patch.object(task, '_get_pending_orders', return_value=mock_orders):
            with patch('src.tasks.energy_sync.EnergyAPIClient') as MockClient:
                # 设置 mock 返回值
                mock_instance = AsyncMock()
                mock_instance.query_order.return_value = MagicMock(
                    data={"status": 1, "hash": "abc123"}
                )
                mock_instance.__aenter__.return_value = mock_instance
                mock_instance.__aexit__.return_value = None
                MockClient.return_value = mock_instance

                with patch.object(task, '_update_order_status'):
                    with patch.object(task, '_notify_user', new_callable=AsyncMock):
                        await task.sync_orders()

                # 验证 EnergyAPIClient 被正确调用，包含 URL 参数
                MockClient.assert_called_once_with(
                    username=settings.energy_api_username,
                    password=settings.energy_api_password,
                    base_url=settings.energy_api_base_url,
                    backup_url=settings.energy_api_backup_url,
                )

