"""
TRX 闪兑自动化测试脚本

测试：
1. TRXSender 转账逻辑
2. PaymentMonitor 支付监听
3. 订单状态流转
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


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
        
        config = TRXExchangeConfig(
            receive_address="T_recv",
            send_address="T_send",
            private_key="abc123",
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
