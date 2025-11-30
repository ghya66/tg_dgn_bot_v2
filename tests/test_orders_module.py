"""
订单查询模块测试脚本

测试：
1. 模块导入
2. 状态定义
3. 回调处理函数
4. ConversationHandler 配置
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestOrdersModuleImport:
    """测试订单模块导入"""
    
    def test_import_query_handler(self):
        """测试导入 query_handler"""
        from src.modules.orders.query_handler import (
            SHOW_ORDERS,
            INPUT_USER_ID,
            get_orders_handler,
            orders_command,
            show_orders_menu,
            show_orders_list,
            filter_by_type,
            filter_by_status,
            show_order_detail,
            prompt_user_id_input,
            handle_user_id_input,
            handle_callback,
        )
        assert SHOW_ORDERS == 0
        assert INPUT_USER_ID == 1
    
    def test_import_orders_module(self):
        """测试导入 OrdersModule"""
        from src.modules.orders.handler import OrdersModule
        
        module = OrdersModule()
        assert module.module_name == "orders"


class TestOrderTypeMapping:
    """测试订单类型映射"""
    
    def test_order_types(self):
        """测试订单类型定义"""
        from src.modules.orders.query_handler import ORDER_TYPE_NAMES
        
        assert "premium" in ORDER_TYPE_NAMES
        assert "deposit" in ORDER_TYPE_NAMES
        assert "trx_exchange" in ORDER_TYPE_NAMES
        assert "energy" in ORDER_TYPE_NAMES
    
    def test_order_statuses(self):
        """测试订单状态定义"""
        from src.modules.orders.query_handler import ORDER_STATUS_NAMES
        
        assert "PENDING" in ORDER_STATUS_NAMES
        assert "PAID" in ORDER_STATUS_NAMES
        assert "DELIVERED" in ORDER_STATUS_NAMES
        assert "EXPIRED" in ORDER_STATUS_NAMES
        assert "CANCELLED" in ORDER_STATUS_NAMES


class TestConversationHandler:
    """测试 ConversationHandler 配置"""
    
    def test_handler_states(self):
        """测试状态配置"""
        from src.modules.orders.query_handler import get_orders_handler, SHOW_ORDERS, INPUT_USER_ID
        
        handler = get_orders_handler()
        
        # 检查状态存在
        assert SHOW_ORDERS in handler.states
        assert INPUT_USER_ID in handler.states
    
    def test_handler_entry_points(self):
        """测试入口点配置"""
        from src.modules.orders.query_handler import get_orders_handler
        
        handler = get_orders_handler()
        
        # 检查入口点
        assert len(handler.entry_points) == 1


class TestHelperFunctions:
    """测试辅助函数"""
    
    def test_format_datetime(self):
        """测试时间格式化"""
        from src.modules.orders.query_handler import _format_datetime
        from datetime import datetime
        
        # 有值
        dt = datetime(2025, 1, 15, 10, 30, 45)
        result = _format_datetime(dt)
        assert result == "2025-01-15 10:30:45"
        
        # 无值
        assert _format_datetime(None) == "-"
    
    def test_format_amount(self):
        """测试金额格式化"""
        from src.modules.orders.query_handler import _format_amount
        
        # 正常金额（微USDT）
        assert _format_amount(10_000_000) == "10.000 USDT"
        assert _format_amount(100_500_000) == "100.500 USDT"
        
        # 无值
        assert _format_amount(None) == "-"
    
    def test_mask_tx_hash(self):
        """测试交易哈希掩码"""
        from src.modules.orders.query_handler import _mask_tx_hash
        
        # 长哈希
        long_hash = "abc123def456ghi789jkl012mno345pqr678"
        result = _mask_tx_hash(long_hash)
        assert result == "abc123...r678"
        
        # 短哈希
        short_hash = "abc123"
        assert _mask_tx_hash(short_hash) == short_hash
        
        # 空值
        assert _mask_tx_hash("") == ""


class TestCallbackPatterns:
    """测试回调模式"""
    
    def test_callback_patterns_no_conflict(self):
        """测试回调模式无冲突"""
        # 订单模块回调前缀
        orders_prefix = "orders_"
        
        # 其他模块前缀
        other_prefixes = ["admin_", "energy_", "premium_", "menu_", "trx_"]
        
        # 确保无冲突
        for prefix in other_prefixes:
            assert not orders_prefix.startswith(prefix)
            assert not prefix.startswith(orders_prefix)


class TestHTMLFormat:
    """测试 HTML 格式"""
    
    def test_build_order_detail_text(self):
        """测试订单详情文本构建"""
        from src.modules.orders.query_handler import _build_order_detail_text
        
        # 创建 mock Order
        mock_order = MagicMock()
        mock_order.order_id = "TEST123"
        mock_order.user_id = 123456
        mock_order.order_type = "premium"
        mock_order.status = "PAID"
        mock_order.amount_usdt = 10_000_000
        mock_order.created_at = None
        mock_order.paid_at = None
        mock_order.delivered_at = None
        mock_order.expires_at = None
        mock_order.recipient = None
        mock_order.premium_months = None
        mock_order.user_confirmed_at = None
        mock_order.user_confirm_source = None
        mock_order.user_tx_hash = None
        mock_order.tx_hash = None
        
        result = _build_order_detail_text(mock_order)
        
        # 检查 HTML 格式
        assert "<b>" in result
        assert "<code>" in result
        assert "**" not in result  # 不应有 Markdown
        assert "`" not in result or "<code>" in result  # 使用 HTML code
