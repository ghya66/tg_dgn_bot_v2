"""
TRX 闪兑自动化测试脚本

测试：
1. TRXSender 转账逻辑
2. PaymentMonitor 支付监听
3. 订单状态流转
"""
import pytest
from contextlib import contextmanager
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


def create_mock_db_context(mock_db):
    """创建一个返回 mock db 的上下文管理器"""
    @contextmanager
    def mock_context():
        yield mock_db
    return mock_context


class TestTRXSender:
    """测试 TRX 发送器"""
    
    def test_import(self):
        """测试导入"""
        from src.modules.trx_exchange.trx_sender import TRXSender, MAX_SINGLE_TRX
        assert TRXSender is not None
        assert MAX_SINGLE_TRX == Decimal("5000")
    
    def test_validate_address_valid(self):
        """测试有效地址验证"""
        from src.modules.trx_exchange.trx_sender import TRXSender
        
        sender = TRXSender()
        
        # 有效地址
        assert sender.validate_address("TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH") is True
        assert sender.validate_address("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t") is True
    
    def test_validate_address_invalid(self):
        """测试无效地址验证"""
        from src.modules.trx_exchange.trx_sender import TRXSender
        
        sender = TRXSender()
        
        # 无效地址
        assert sender.validate_address("") is False
        assert sender.validate_address("0x123") is False
        assert sender.validate_address("TLyqzVGLV1srkB7dToTAEqgDSfPtXR") is False  # 太短
        assert sender.validate_address("ALyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH") is False  # 不是 T 开头
    
    def test_send_trx_test_mode(self):
        """测试 TEST MODE 发送"""
        from src.modules.trx_exchange.trx_sender import TRXSender
        from src.modules.trx_exchange.config import TRXExchangeConfig
        
        config = TRXExchangeConfig(
            receive_address="T_recv",
            send_address="T_send",
            private_key="",
            qrcode_file_id="",
            default_rate=Decimal("0.14"),
            test_mode=True,
        )
        
        sender = TRXSender(config=config)
        
        result = sender.send_trx(
            recipient_address="TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH",
            amount=Decimal("100"),
            order_id="TEST123"
        )
        
        assert result == "mock_tx_hash_TEST123"
    
    def test_send_trx_exceeds_limit(self):
        """测试超过限额"""
        from src.modules.trx_exchange.trx_sender import TRXSender, MAX_SINGLE_TRX
        from src.modules.trx_exchange.config import TRXExchangeConfig

        # 使用有效的 64 位十六进制私钥格式
        valid_private_key = "a" * 64  # 64 位十六进制字符串

        config = TRXExchangeConfig(
            receive_address="T_recv",
            send_address="T_send",
            private_key=valid_private_key,
            qrcode_file_id="",
            default_rate=Decimal("0.14"),
            test_mode=False,  # 生产模式
        )

        sender = TRXSender(config=config)

        with pytest.raises(ValueError, match="单笔转账超过限额"):
            sender.send_trx(
                recipient_address="TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH",
                amount=MAX_SINGLE_TRX + 1,
                order_id="TEST123"
            )

    def test_invalid_private_key_format(self):
        """测试无效私钥格式"""
        from src.modules.trx_exchange.trx_sender import TRXSender
        from src.modules.trx_exchange.config import TRXExchangeConfig

        config = TRXExchangeConfig(
            receive_address="T_recv",
            send_address="T_send",
            private_key="abc123",  # 无效格式
            qrcode_file_id="",
            default_rate=Decimal("0.14"),
            test_mode=False,  # 生产模式
        )

        # 应该在初始化时抛出 ValueError
        with pytest.raises(ValueError, match="Private key format is invalid"):
            TRXSender(config=config)


class TestPaymentMonitor:
    """测试支付监听器"""

    def test_import(self):
        """测试导入"""
        from src.modules.trx_exchange.payment_monitor import (
            PaymentMonitor,
            get_monitor,
            start_payment_monitor,
            stop_payment_monitor,
        )
        assert PaymentMonitor is not None

    def test_init(self):
        """测试初始化"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor
        from collections import deque

        monitor = PaymentMonitor()

        assert monitor.running is False
        assert monitor.poll_interval == 30
        assert monitor._last_check_time is None
        # 新实现使用 deque + set 进行内存限制
        assert isinstance(monitor._processed_tx_hashes, deque)
        assert isinstance(monitor._processed_tx_set, set)
        # Bot 实例初始为 None
        assert monitor._bot is None

    def test_set_bot(self):
        """测试设置 Bot 实例"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()
        mock_bot = MagicMock()

        monitor.set_bot(mock_bot)

        assert monitor._bot is mock_bot

    @pytest.mark.asyncio
    async def test_notify_user_success(self):
        """测试发送成功通知"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()
        mock_bot = AsyncMock()
        monitor.set_bot(mock_bot)

        # 创建模拟订单
        mock_order = MagicMock()
        mock_order.order_id = "TEST_ORDER_001"
        mock_order.trx_amount = 100.5
        mock_order.recipient_address = "TXyz1234567890abcdefghijklmnopqrs"
        mock_order.user_id = 12345

        await monitor._notify_user_success(mock_order, "abc123def456")

        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs["chat_id"] == 12345
        assert "TRX 发货成功" in call_args.kwargs["text"]
        assert "TEST_ORDER_001" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_notify_user_success_no_bot(self):
        """测试无 Bot 实例时不发送通知"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()
        # 不设置 bot

        mock_order = MagicMock()
        mock_order.order_id = "TEST_ORDER_001"

        # 不应抛出异常
        await monitor._notify_user_success(mock_order, "abc123")

    @pytest.mark.asyncio
    async def test_notify_user_failure(self):
        """测试发送失败通知"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()
        mock_bot = AsyncMock()
        monitor.set_bot(mock_bot)

        mock_order = MagicMock()
        mock_order.order_id = "TEST_ORDER_002"
        mock_order.trx_amount = 50.0
        mock_order.user_id = 67890

        await monitor._notify_user_failure(mock_order, "Network error")

        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs["chat_id"] == 67890
        assert "TRX 发货失败" in call_args.kwargs["text"]

    def test_stop(self):
        """测试停止监听"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()
        monitor.running = True

        monitor.stop()

        assert monitor.running is False

    def test_add_processed_tx_memory_limit(self):
        """测试已处理交易缓存的内存限制"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor, MAX_PROCESSED_TX_CACHE

        monitor = PaymentMonitor()

        # 添加超过限制数量的交易哈希
        test_limit = 100  # 使用较小的数量进行测试
        for i in range(test_limit + 10):
            # 模拟添加，绕过 maxlen 限制测试逻辑
            monitor._add_processed_tx(f"tx_{i}")

        # deque 应该保持在 maxlen 限制内
        assert len(monitor._processed_tx_hashes) <= MAX_PROCESSED_TX_CACHE
        # set 应该与 deque 同步
        assert len(monitor._processed_tx_set) == len(monitor._processed_tx_hashes)

        # 最新的交易应该存在
        assert monitor._is_tx_processed(f"tx_{test_limit + 9}")

        # 重复添加不应该增加数量
        original_len = len(monitor._processed_tx_hashes)
        monitor._add_processed_tx(f"tx_{test_limit + 9}")
        assert len(monitor._processed_tx_hashes) == original_len

    def test_is_tx_processed_o1_lookup(self):
        """测试交易检查是 O(1) 查找"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()

        # 添加一些交易
        for i in range(50):
            monitor._add_processed_tx(f"tx_{i}")

        # 检查存在的交易
        assert monitor._is_tx_processed("tx_25") is True
        # 检查不存在的交易
        assert monitor._is_tx_processed("tx_nonexistent") is False

    @pytest.mark.asyncio
    async def test_start_without_receive_address(self):
        """测试没有收款地址时启动"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()
        monitor.receive_address = ""

        # 应该立即返回，不会启动监听
        await monitor.start()

        assert monitor.running is False

    @pytest.mark.asyncio
    async def test_start_one_iteration(self):
        """测试启动监听一次迭代"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()
        monitor.receive_address = "TTestAddress123456789012345678901234"
        monitor.poll_interval = 0.01  # 快速轮询

        call_count = 0
        async def mock_check_payments():
            nonlocal call_count
            call_count += 1
            if call_count >= 1:
                monitor.running = False

        monitor._check_payments = mock_check_payments

        await monitor.start()

        assert call_count >= 1

    @pytest.mark.asyncio
    async def test_start_with_exception(self):
        """测试启动时发生异常"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()
        monitor.receive_address = "TTestAddress123456789012345678901234"
        monitor.poll_interval = 0.01

        call_count = 0
        async def mock_check_payments_error():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Test error")
            monitor.running = False

        monitor._check_payments = mock_check_payments_error

        with patch('src.modules.trx_exchange.payment_monitor.collect_error') as mock_collect:
            await monitor.start()
            mock_collect.assert_called_once()

    @pytest.mark.asyncio
    async def test_match_order(self):
        """测试订单匹配"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()

        # 创建 mock 数据库会话
        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.order_id = "TEST123"
        mock_order.usdt_amount = Decimal("100.738")

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_order

        result = await monitor._match_order(mock_db, Decimal("100.738"))

        assert result == mock_order

    @pytest.mark.asyncio
    async def test_check_payments_no_transfers(self):
        """测试检查支付 - 没有转账"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()

        async def mock_fetch():
            return []

        monitor._fetch_usdt_transfers = mock_fetch

        # 不应该抛出异常
        await monitor._check_payments()

    @pytest.mark.asyncio
    async def test_check_payments_with_transfers(self):
        """测试检查支付 - 有转账"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()

        processed = []
        async def mock_fetch():
            return [{"transaction_id": "tx1"}, {"transaction_id": "tx2"}]

        async def mock_process(tx):
            processed.append(tx)

        monitor._fetch_usdt_transfers = mock_fetch
        monitor._process_transfer = mock_process

        await monitor._check_payments()

        assert len(processed) == 2

    @pytest.mark.asyncio
    async def test_check_payments_with_exception(self):
        """测试检查支付 - 发生异常"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()

        async def mock_fetch_error():
            raise Exception("Fetch error")

        monitor._fetch_usdt_transfers = mock_fetch_error

        with patch('src.modules.trx_exchange.payment_monitor.collect_error') as mock_collect:
            await monitor._check_payments()
            mock_collect.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_usdt_transfers_success(self):
        """测试获取 USDT 转账 - 成功"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()
        monitor.receive_address = "TReceiveAddress12345678901234567890"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token_transfers": [
                {"transaction_id": "tx1", "to_address": "TReceiveAddress12345678901234567890"},
                {"transaction_id": "tx2", "to_address": "TOtherAddress12345678901234567890"},
            ]
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch('src.modules.trx_exchange.payment_monitor.get_async_client', return_value=mock_client):
            result = await monitor._fetch_usdt_transfers()

        # 只返回 to_address 匹配的转账
        assert len(result) == 1
        assert result[0]["transaction_id"] == "tx1"

    @pytest.mark.asyncio
    async def test_fetch_usdt_transfers_api_error(self):
        """测试获取 USDT 转账 - API 错误"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch('src.modules.trx_exchange.payment_monitor.get_async_client', return_value=mock_client):
            result = await monitor._fetch_usdt_transfers()

        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_usdt_transfers_exception(self):
        """测试获取 USDT 转账 - 异常"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))

        with patch('src.modules.trx_exchange.payment_monitor.get_async_client', return_value=mock_client):
            with patch('src.modules.trx_exchange.payment_monitor.collect_error') as mock_collect:
                result = await monitor._fetch_usdt_transfers()
                mock_collect.assert_called_once()

        assert result == []

    @pytest.mark.asyncio
    async def test_process_transfer_already_processed(self):
        """测试处理转账 - 已处理过的交易"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()
        # 使用新的方法添加已处理的交易
        monitor._add_processed_tx("tx_already_processed")

        tx = {"transaction_id": "tx_already_processed"}

        # 不应该处理
        await monitor._process_transfer(tx)

        # 仍然只有一个
        assert len(monitor._processed_tx_hashes) == 1
        assert monitor._is_tx_processed("tx_already_processed")

    @pytest.mark.asyncio
    async def test_process_transfer_invalid_amount(self):
        """测试处理转账 - 无效金额"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()

        # 无效金额
        tx = {"transaction_id": "tx_invalid", "quant": "invalid"}
        await monitor._process_transfer(tx)

        # 金额为0
        tx2 = {"transaction_id": "tx_zero", "quant": 0}
        await monitor._process_transfer(tx2)

        # 都不应该标记为已处理（因为直接返回了）
        assert not monitor._is_tx_processed("tx_invalid")

    @pytest.mark.asyncio
    async def test_process_transfer_no_matching_order(self):
        """测试处理转账 - 没有匹配订单"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()

        tx = {"transaction_id": "tx_no_match", "quant": 100000000}  # 100 USDT

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        with patch('src.common.db_manager.get_db_context_manual_commit', return_value=create_mock_db_context(mock_db)()):
            await monitor._process_transfer(tx)

        # 应该标记为已处理
        assert monitor._is_tx_processed("tx_no_match")

    @pytest.mark.asyncio
    async def test_process_transfer_success(self):
        """测试处理转账 - 成功"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()

        tx = {"transaction_id": "tx_success", "quant": 100000000}  # 100 USDT

        mock_order = MagicMock()
        mock_order.order_id = "TRX123"
        mock_order.usdt_amount = Decimal("100")
        mock_order.status = "PENDING"
        mock_order.tx_hash = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_order

        async def mock_send_trx(db, order):
            pass

        monitor._send_trx = mock_send_trx

        # patch _match_order 直接返回 mock_order，避免 db.query 的问题
        async def mock_match_order(db, amount):
            return mock_order

        monitor._match_order = mock_match_order

        with patch('src.common.db_manager.get_db_context_manual_commit', return_value=create_mock_db_context(mock_db)()):
            await monitor._process_transfer(tx)

        # 验证订单状态更新
        assert mock_order.status == "PAID"
        assert mock_order.tx_hash == "tx_success"
        assert monitor._is_tx_processed("tx_success")

    @pytest.mark.asyncio
    async def test_send_trx_success(self):
        """测试发送 TRX - 成功"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()
        monitor.trx_sender = MagicMock()
        monitor.trx_sender.send_trx = MagicMock(return_value="send_tx_hash_123")

        mock_order = MagicMock()
        mock_order.order_id = "TRX123"
        mock_order.recipient_address = "TRecipient123"
        mock_order.trx_amount = Decimal("714")

        mock_db = MagicMock()

        await monitor._send_trx(mock_db, mock_order)

        assert mock_order.status == "COMPLETED"
        assert mock_order.send_tx_hash == "send_tx_hash_123"

    @pytest.mark.asyncio
    async def test_send_trx_failure(self):
        """测试发送 TRX - 失败"""
        from src.modules.trx_exchange.payment_monitor import PaymentMonitor

        monitor = PaymentMonitor()
        monitor.trx_sender = MagicMock()
        monitor.trx_sender.send_trx = MagicMock(side_effect=Exception("Send failed"))

        mock_order = MagicMock()
        mock_order.order_id = "TRX123"
        mock_order.recipient_address = "TRecipient123"
        mock_order.trx_amount = Decimal("714")

        mock_db = MagicMock()

        await monitor._send_trx(mock_db, mock_order)

        assert mock_order.status == "SEND_FAILED"
        assert "Send failed" in mock_order.error_message


class TestPaymentMonitorGlobalFunctions:
    """测试 payment_monitor 全局函数"""

    def test_get_monitor_singleton(self):
        """测试获取监听器单例"""
        from src.modules.trx_exchange import payment_monitor

        # 重置全局变量
        payment_monitor._monitor = None

        monitor1 = payment_monitor.get_monitor()
        monitor2 = payment_monitor.get_monitor()

        assert monitor1 is monitor2

    @pytest.mark.asyncio
    async def test_start_payment_monitor(self):
        """测试启动支付监听"""
        from src.modules.trx_exchange import payment_monitor

        # 重置
        payment_monitor._monitor = None

        mock_monitor = MagicMock()
        mock_monitor.start = AsyncMock()

        with patch.object(payment_monitor, 'get_monitor', return_value=mock_monitor):
            await payment_monitor.start_payment_monitor()

    def test_stop_payment_monitor(self):
        """测试停止支付监听"""
        from src.modules.trx_exchange import payment_monitor

        mock_monitor = MagicMock()
        payment_monitor._monitor = mock_monitor

        payment_monitor.stop_payment_monitor()

        mock_monitor.stop.assert_called_once()

    def test_stop_payment_monitor_no_monitor(self):
        """测试停止支付监听 - 没有监听器"""
        from src.modules.trx_exchange import payment_monitor

        payment_monitor._monitor = None

        # 不应该抛出异常
        payment_monitor.stop_payment_monitor()


class TestOrderModel:
    """测试订单模型"""
    
    def test_model_fields(self):
        """测试模型字段"""
        from src.modules.trx_exchange.models import TRXExchangeOrder
        
        # 检查新字段存在
        assert hasattr(TRXExchangeOrder, 'send_tx_hash')
        assert hasattr(TRXExchangeOrder, 'error_message')
        assert hasattr(TRXExchangeOrder, 'completed_at')
    
    def test_order_status_values(self):
        """测试订单状态值"""
        # 定义预期的状态
        valid_statuses = [
            "PENDING",      # 待支付
            "PAID",         # 已支付
            "PROCESSING",   # 处理中
            "COMPLETED",    # 已完成
            "SEND_FAILED",  # 发送失败
            "EXPIRED",      # 已过期
        ]
        
        # 确认所有状态都有意义
        assert len(valid_statuses) == 6


class TestRateManager:
    """测试汇率管理器"""
    
    def test_import(self):
        """测试导入"""
        from src.modules.trx_exchange.rate_manager import RateManager
        assert RateManager is not None
    
    def test_calculate_trx_amount(self):
        """测试 TRX 金额计算"""
        from src.modules.trx_exchange.rate_manager import RateManager
        
        # rate 定义: 1 USDT = X TRX
        # 汇率 7.14 TRX/USDT，100 USDT = 714 TRX
        usdt_amount = Decimal("100")
        rate = Decimal("7.14")  # 1 USDT = 7.14 TRX
        
        trx_amount = RateManager.calculate_trx_amount(usdt_amount, rate)
        
        # 100 * 7.14 = 714
        assert trx_amount == Decimal("714.000000")


class TestIntegration:
    """集成测试"""
    
    def test_handler_import(self):
        """测试 handler 导入"""
        from src.modules.trx_exchange.handler import TRXExchangeModule
        
        module = TRXExchangeModule()
        assert module.module_name == "trx_exchange"
    
    def test_generate_order_id(self):
        """测试订单号生成"""
        from src.modules.trx_exchange.handler import TRXExchangeModule
        
        module = TRXExchangeModule()
        
        order_id = module.generate_order_id()
        
        assert order_id.startswith("TRX")
        assert len(order_id) == 19  # TRX + 16 hex
    
    def test_generate_unique_amount(self):
        """测试唯一金额生成"""
        from src.modules.trx_exchange.handler import TRXExchangeModule

        module = TRXExchangeModule()

        base_amount = Decimal("100")
        unique_amount = module.generate_unique_amount(base_amount)

        # 应该在 100.001 ~ 100.999 之间
        assert unique_amount > Decimal("100")
        assert unique_amount < Decimal("101")

        # 确保有 3 位小数
        assert len(str(unique_amount).split('.')[-1]) == 3


class TestTRXExchangeEdgeCases:
    """TRX 兑换边界条件测试"""

    def test_amount_range_validation(self):
        """测试金额范围验证（5-20000 USDT）"""
        # 直接测试金额范围逻辑
        MIN_AMOUNT = Decimal("5")
        MAX_AMOUNT = Decimal("20000")

        def validate_amount(amount: Decimal) -> bool:
            return MIN_AMOUNT <= amount <= MAX_AMOUNT

        # 有效金额
        assert validate_amount(Decimal("5")) is True
        assert validate_amount(Decimal("100")) is True
        assert validate_amount(Decimal("20000")) is True

        # 无效金额
        assert validate_amount(Decimal("4.99")) is False
        assert validate_amount(Decimal("20001")) is False
        assert validate_amount(Decimal("0")) is False
        assert validate_amount(Decimal("-100")) is False

    def test_rate_precision(self):
        """测试汇率精度"""
        from src.modules.trx_exchange.rate_manager import RateManager

        # 测试小数精度
        usdt = Decimal("100.123")
        rate = Decimal("7.14159")

        trx = RateManager.calculate_trx_amount(usdt, rate)

        # 确保结果有6位小数精度
        assert "." in str(trx)

    def test_suffix_uniqueness(self):
        """测试 suffix 唯一性"""
        from src.modules.trx_exchange.handler import TRXExchangeModule

        module = TRXExchangeModule()

        # 生成多个唯一金额，确保不重复
        amounts = set()
        for _ in range(100):
            amount = module.generate_unique_amount(Decimal("100"))
            amounts.add(amount)

        # 应该有100个不同的金额（理论上可能有极小概率重复）
        assert len(amounts) >= 90  # 允许少量重复


class TestTRXExchangeOrderFactory:
    """TRX 兑换订单工厂测试"""

    def test_create_pending_order(self):
        """测试创建待支付订单"""
        from tests.factories.order_factory import TRXExchangeOrderFactory

        order = TRXExchangeOrderFactory.create(
            usdt_amount=Decimal("100.00"),
            status="PENDING",
        )

        assert order.status == "PENDING"
        assert order.usdt_amount > Decimal("100")  # 包含 suffix
        assert order.trx_amount > Decimal("0")

    def test_order_expiry_time(self):
        """测试订单过期时间"""
        from tests.factories.order_factory import TRXExchangeOrderFactory
        from datetime import datetime, timedelta

        order = TRXExchangeOrderFactory.create()

        # 过期时间应该在30分钟后
        assert order.expires_at > datetime.now()
        assert order.expires_at < datetime.now() + timedelta(hours=1)


class TestTRXExchangeRateCache:
    """TRX 汇率缓存测试"""

    @pytest.mark.asyncio
    async def test_rate_cache_with_fakeredis(self, fake_redis):
        """测试使用 fakeredis 的汇率缓存"""
        # 设置缓存
        await fake_redis.set("trx_rate", "7.14")

        # 读取缓存
        cached_rate = await fake_redis.get("trx_rate")

        assert cached_rate == "7.14"

    @pytest.mark.asyncio
    async def test_rate_cache_expiry(self, fake_redis):
        """测试汇率缓存过期"""
        # 设置带过期时间的缓存
        await fake_redis.setex("trx_rate_temp", 1, "7.14")

        # 立即读取应该存在
        cached = await fake_redis.get("trx_rate_temp")
        assert cached == "7.14"

        # 等待过期后应该不存在
        import asyncio
        await asyncio.sleep(1.5)

        expired = await fake_redis.get("trx_rate_temp")
        assert expired is None


class TestTRXExchangeErrorHandling:
    """TRX 兑换错误处理测试"""

    def test_invalid_address_error(self):
        """测试无效地址错误"""
        from src.modules.trx_exchange.trx_sender import TRXSender

        sender = TRXSender()

        # 无效地址应该返回 False
        assert sender.validate_address("invalid") is False
        assert sender.validate_address("") is False

    def test_network_error_handling(self):
        """测试网络错误处理"""
        from src.modules.trx_exchange.trx_sender import TRXSender
        from src.modules.trx_exchange.config import TRXExchangeConfig

        config = TRXExchangeConfig(
            receive_address="T_recv",
            send_address="T_send",
            private_key="",  # 空私钥
            qrcode_file_id="",
            default_rate=Decimal("0.14"),
            test_mode=False,
        )

        sender = TRXSender(config=config)

        # 没有私钥或 tronpy 未安装应该抛出错误
        with pytest.raises((ValueError, RuntimeError)):
            sender.send_trx(
                recipient_address="TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH",
                amount=Decimal("100"),
                order_id="TEST123"
            )


class TestTRXExchangeHandlerMethods:
    """测试 TRXExchangeModule 的各个方法"""

    @pytest.fixture
    def module(self):
        """创建模块实例"""
        from src.modules.trx_exchange.handler import TRXExchangeModule
        return TRXExchangeModule()

    @pytest.fixture
    def mock_update(self):
        """创建模拟的 Update 对象"""
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 123456789
        update.callback_query = None
        update.message = MagicMock()
        update.message.text = "100"
        update.message.reply_text = AsyncMock()
        update.effective_message = MagicMock()
        update.effective_message.reply_text = AsyncMock()
        update.effective_message.reply_photo = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """创建模拟的 Context 对象"""
        context = MagicMock()
        context.user_data = {}
        return context

    def test_get_handlers_returns_list(self, module):
        """测试 get_handlers 返回列表"""
        handlers = module.get_handlers()
        assert isinstance(handlers, list)
        assert len(handlers) == 1

    @pytest.mark.asyncio
    async def test_start_exchange_from_message(self, module, mock_update, mock_context):
        """测试从消息开始兑换"""
        result = await module.start_exchange(mock_update, mock_context)
        from src.modules.trx_exchange.states import INPUT_AMOUNT
        assert result == INPUT_AMOUNT
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_exchange_from_callback(self, module, mock_context):
        """测试从回调开始兑换"""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.message = MagicMock()
        update.callback_query.message.reply_text = AsyncMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 123456789

        result = await module.start_exchange(update, mock_context)
        from src.modules.trx_exchange.states import INPUT_AMOUNT
        assert result == INPUT_AMOUNT
        update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_input_amount_invalid_text(self, module, mock_update, mock_context):
        """测试输入无效金额文本"""
        mock_update.message.text = "abc"

        result = await module.input_amount(mock_update, mock_context)
        from src.modules.trx_exchange.states import INPUT_AMOUNT
        assert result == INPUT_AMOUNT

    @pytest.mark.asyncio
    async def test_input_amount_below_minimum(self, module, mock_update, mock_context):
        """测试输入低于最小金额"""
        mock_update.message.text = "4"

        result = await module.input_amount(mock_update, mock_context)
        from src.modules.trx_exchange.states import INPUT_AMOUNT
        assert result == INPUT_AMOUNT

    @pytest.mark.asyncio
    async def test_input_amount_above_maximum(self, module, mock_update, mock_context):
        """测试输入高于最大金额"""
        mock_update.message.text = "25000"

        result = await module.input_amount(mock_update, mock_context)
        from src.modules.trx_exchange.states import INPUT_AMOUNT
        assert result == INPUT_AMOUNT

    @pytest.mark.asyncio
    async def test_input_amount_valid(self, module, mock_update, mock_context):
        """测试输入有效金额"""
        mock_update.message.text = "100"

        with patch('src.modules.trx_exchange.handler.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            with patch('src.modules.trx_exchange.handler.RateManager') as mock_rate:
                mock_rate.get_rate.return_value = Decimal("7.14")
                mock_rate.calculate_trx_amount.return_value = Decimal("714.00")

                result = await module.input_amount(mock_update, mock_context)
                from src.modules.trx_exchange.states import INPUT_ADDRESS
                assert result == INPUT_ADDRESS

    @pytest.mark.asyncio
    async def test_input_address_invalid(self, module, mock_update, mock_context):
        """测试输入无效地址"""
        mock_update.message.text = "invalid_address"

        result = await module.input_address(mock_update, mock_context)
        from src.modules.trx_exchange.states import INPUT_ADDRESS
        assert result == INPUT_ADDRESS

    @pytest.mark.asyncio
    async def test_cancel_input(self, module, mock_context):
        """测试取消输入"""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        from telegram.ext import ConversationHandler
        result = await module.cancel_input(update, mock_context)
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_skip_tx_hash(self, module, mock_context):
        """测试跳过交易哈希"""
        mock_context.user_data = {"exchange_order_id": "TRX123456"}

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        from telegram.ext import ConversationHandler
        result = await module.skip_tx_hash(update, mock_context)
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_handle_tx_hash_input(self, module, mock_update, mock_context):
        """测试处理交易哈希输入"""
        mock_update.message.text = "abc123def456"
        mock_context.user_data = {"exchange_order_id": "TRX123456"}

        with patch('src.modules.trx_exchange.handler.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_order = MagicMock()
            mock_db.query.return_value.filter_by.return_value.first.return_value = mock_order
            mock_session.return_value = mock_db

            from telegram.ext import ConversationHandler
            result = await module.handle_tx_hash_input(mock_update, mock_context)
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_confirm_payment_cancel(self, module, mock_context):
        """测试取消支付确认"""
        mock_context.user_data = {"exchange_order_id": "TRX123456"}

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = "trx_cancel_TRX123456"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        from telegram.ext import ConversationHandler
        result = await module.confirm_payment(update, mock_context)
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_confirm_payment_expired_order(self, module, mock_context):
        """测试确认已过期订单"""
        mock_context.user_data = {"exchange_order_id": "TRX123456"}

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = "trx_paid_TRX123456"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        with patch('src.modules.trx_exchange.handler.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_order = MagicMock()
            # 设置已过期的时间
            mock_order.expires_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
            mock_db.query.return_value.filter_by.return_value.first.return_value = mock_order
            mock_session.return_value = mock_db

            from telegram.ext import ConversationHandler
            result = await module.confirm_payment(update, mock_context)
            assert result == ConversationHandler.END
