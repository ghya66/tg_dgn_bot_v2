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

    def test_build_order_detail_with_all_fields(self):
        """测试订单详情文本构建（含所有字段）"""
        from src.modules.orders.query_handler import _build_order_detail_text
        from datetime import datetime

        mock_order = MagicMock()
        mock_order.order_id = "TEST456"
        mock_order.user_id = 789012
        mock_order.order_type = "deposit"
        mock_order.status = "DELIVERED"
        mock_order.amount_usdt = 50_000_000
        mock_order.created_at = datetime(2025, 1, 1, 10, 0, 0)
        mock_order.paid_at = datetime(2025, 1, 1, 10, 5, 0)
        mock_order.delivered_at = datetime(2025, 1, 1, 10, 6, 0)
        mock_order.expires_at = datetime(2025, 1, 1, 11, 0, 0)
        mock_order.recipient = "@testuser"
        mock_order.premium_months = 3
        mock_order.user_confirmed_at = datetime(2025, 1, 1, 10, 4, 0)
        mock_order.user_confirm_source = "button"
        mock_order.user_tx_hash = "usertxhash123456789012345678901234567890"
        mock_order.tx_hash = "systemtxhash123456789012345678901234567890"

        result = _build_order_detail_text(mock_order)

        assert "TEST456" in result
        assert "50.000 USDT" in result
        assert "@testuser" in result
        assert "3 个月" in result
        assert "用户确认" in result
        assert "button" in result
        assert "用户填写 TX Hash" in result
        assert "系统 TX Hash" in result


class TestOrdersCommandAsync:
    """测试订单命令异步方法"""

    @pytest.mark.asyncio
    async def test_orders_command_unauthorized(self):
        """测试非管理员访问订单命令"""
        from src.modules.orders.query_handler import orders_command
        from telegram.ext import ConversationHandler

        update = MagicMock()
        update.effective_user.id = 999999  # 非管理员ID
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.user_data = {}

        with patch('src.modules.orders.query_handler.settings') as mock_settings:
            mock_settings.bot_owner_id = 123456  # 管理员ID
            result = await orders_command(update, context)

        assert result == ConversationHandler.END
        update.message.reply_text.assert_called_once()
        args = update.message.reply_text.call_args[0][0]
        assert "仅限管理员" in args

    @pytest.mark.asyncio
    async def test_orders_command_authorized(self):
        """测试管理员访问订单命令"""
        from src.modules.orders.query_handler import orders_command, SHOW_ORDERS

        update = MagicMock()
        update.effective_user.id = 123456  # 管理员ID
        update.callback_query = None
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.user_data = {}

        with patch('src.modules.orders.query_handler.settings') as mock_settings, \
             patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_settings.bot_owner_id = 123456

            # Mock 数据库会话
            mock_db = MagicMock()
            mock_db.query.return_value.scalar.return_value = 0
            mock_session.return_value = mock_db

            result = await orders_command(update, context)

        assert result == SHOW_ORDERS
        assert 'order_filters' in context.user_data

    @pytest.mark.asyncio
    async def test_show_orders_menu_with_message(self):
        """测试显示订单菜单（通过消息）"""
        from src.modules.orders.query_handler import show_orders_menu, SHOW_ORDERS

        update = MagicMock()
        update.callback_query = None
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.user_data = {'order_filters': {'page': 1}}

        with patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.scalar.return_value = 5
            mock_db.query.return_value.scalar.return_value = 10
            mock_session.return_value = mock_db

            result = await show_orders_menu(update, context)

        assert result == SHOW_ORDERS
        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_orders_menu_with_callback(self):
        """测试显示订单菜单（通过回调）"""
        from src.modules.orders.query_handler import show_orders_menu, SHOW_ORDERS

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {
            'order_filters': {
                'order_type': 'premium',
                'status': 'PAID',
                'user_id': 123456,
                'page': 1
            }
        }

        with patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.scalar.return_value = 5
            mock_db.query.return_value.scalar.return_value = 10
            mock_session.return_value = mock_db

            result = await show_orders_menu(update, context)

        assert result == SHOW_ORDERS
        update.callback_query.edit_message_text.assert_called_once()


class TestOrdersListAsync:
    """测试订单列表异步方法"""

    @pytest.mark.asyncio
    async def test_show_orders_list_empty(self):
        """测试显示空订单列表"""
        from src.modules.orders.query_handler import show_orders_list, SHOW_ORDERS

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {'order_filters': {'page': 1, 'per_page': 10}}

        with patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_db.execute.return_value.scalars.return_value.all.return_value = []
            mock_db.execute.return_value.scalar.return_value = 0
            mock_session.return_value = mock_db

            result = await show_orders_list(update, context)

        assert result == SHOW_ORDERS
        update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_orders_list_with_orders(self):
        """测试显示有订单的列表"""
        from src.modules.orders.query_handler import show_orders_list, SHOW_ORDERS
        from datetime import datetime

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {
            'order_filters': {
                'page': 1,
                'per_page': 10,
                'order_type': None,
                'status': None,
                'user_id': None
            }
        }

        # Mock订单
        mock_order = MagicMock()
        mock_order.order_id = "ORDER001"
        mock_order.order_type = "premium"
        mock_order.status = "PAID"
        mock_order.amount_usdt = 10_000_000
        mock_order.user_id = 123456
        mock_order.created_at = datetime(2025, 1, 1, 10, 0, 0)

        with patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_order]
            mock_db.execute.return_value.scalar.return_value = 1
            mock_session.return_value = mock_db

            result = await show_orders_list(update, context)

        assert result == SHOW_ORDERS
        call_args = update.callback_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "ORDER001" in text

    @pytest.mark.asyncio
    async def test_show_orders_list_with_pagination(self):
        """测试显示订单列表（带分页）"""
        from src.modules.orders.query_handler import show_orders_list, SHOW_ORDERS
        from datetime import datetime

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {'order_filters': {'page': 2, 'per_page': 10}}

        mock_order = MagicMock()
        mock_order.order_id = "ORDER002"
        mock_order.order_type = "deposit"
        mock_order.status = "PENDING"
        mock_order.amount_usdt = 5_000_000
        mock_order.user_id = 789012
        mock_order.created_at = datetime(2025, 1, 2, 15, 30, 0)

        with patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_order]
            mock_db.execute.return_value.scalar.return_value = 25  # 多页
            mock_session.return_value = mock_db

            result = await show_orders_list(update, context)

        assert result == SHOW_ORDERS
        # 检查分页按钮
        call_kwargs = update.callback_query.edit_message_text.call_args[1]
        reply_markup = call_kwargs['reply_markup']
        assert reply_markup is not None


class TestFilterFunctions:
    """测试过滤功能"""

    @pytest.mark.asyncio
    async def test_filter_by_type(self):
        """测试按类型过滤"""
        from src.modules.orders.query_handler import filter_by_type, SHOW_ORDERS

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()

        result = await filter_by_type(update, context)

        assert result == SHOW_ORDERS
        update.callback_query.answer.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "按订单类型筛选" in text

    @pytest.mark.asyncio
    async def test_filter_by_status(self):
        """测试按状态过滤"""
        from src.modules.orders.query_handler import filter_by_status, SHOW_ORDERS

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()

        result = await filter_by_status(update, context)

        assert result == SHOW_ORDERS
        update.callback_query.answer.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "按订单状态筛选" in text

    @pytest.mark.asyncio
    async def test_prompt_user_id_input(self):
        """测试提示用户输入ID"""
        from src.modules.orders.query_handler import prompt_user_id_input, INPUT_USER_ID

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()

        result = await prompt_user_id_input(update, context)

        assert result == INPUT_USER_ID
        call_args = update.callback_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "按用户筛选" in text


class TestUserIdInput:
    """测试用户ID输入"""

    @pytest.mark.asyncio
    async def test_handle_user_id_input_valid(self):
        """测试有效用户ID输入"""
        from src.modules.orders.query_handler import handle_user_id_input, SHOW_ORDERS

        update = MagicMock()
        update.message.text = "123456789"
        update.message.reply_text = AsyncMock()
        update.callback_query = None

        context = MagicMock()
        context.user_data = {'order_filters': {'page': 1}}

        with patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.scalar.return_value = 0
            mock_db.query.return_value.scalar.return_value = 0
            mock_session.return_value = mock_db

            result = await handle_user_id_input(update, context)

        assert result == SHOW_ORDERS
        assert context.user_data['order_filters']['user_id'] == 123456789

    @pytest.mark.asyncio
    async def test_handle_user_id_input_invalid(self):
        """测试无效用户ID输入"""
        from src.modules.orders.query_handler import handle_user_id_input, INPUT_USER_ID

        update = MagicMock()
        update.message.text = "not_a_number"
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.user_data = {'order_filters': {'page': 1}}

        result = await handle_user_id_input(update, context)

        assert result == INPUT_USER_ID
        update.message.reply_text.assert_called_once()
        args = update.message.reply_text.call_args[0][0]
        assert "格式错误" in args


class TestOrderDetail:
    """测试订单详情"""

    @pytest.mark.asyncio
    async def test_show_order_detail_not_found(self):
        """测试订单不存在"""
        from src.modules.orders.query_handler import show_order_detail, SHOW_ORDERS

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()

        context = MagicMock()

        with patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_db.query.return_value.filter_by.return_value.first.return_value = None
            mock_session.return_value = mock_db

            result = await show_order_detail(update, context, "NOTEXIST")

        assert result == SHOW_ORDERS
        update.callback_query.answer.assert_called_once_with("订单不存在", show_alert=True)

    @pytest.mark.asyncio
    async def test_show_order_detail_found(self):
        """测试订单存在"""
        from src.modules.orders.query_handler import show_order_detail, SHOW_ORDERS
        from datetime import datetime

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()

        mock_order = MagicMock()
        mock_order.order_id = "TESTORDER"
        mock_order.user_id = 123456
        mock_order.order_type = "premium"
        mock_order.status = "PAID"
        mock_order.amount_usdt = 10_000_000
        mock_order.created_at = datetime.now()
        mock_order.paid_at = None
        mock_order.delivered_at = None
        mock_order.expires_at = None
        mock_order.recipient = None
        mock_order.premium_months = None
        mock_order.user_confirmed_at = None
        mock_order.user_confirm_source = None
        mock_order.user_tx_hash = None
        mock_order.tx_hash = None

        with patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_db.query.return_value.filter_by.return_value.first.return_value = mock_order
            mock_session.return_value = mock_db

            result = await show_order_detail(update, context, "TESTORDER")

        assert result == SHOW_ORDERS
        update.callback_query.edit_message_text.assert_called_once()


class TestHandleCallback:
    """测试回调处理"""

    @pytest.mark.asyncio
    async def test_handle_callback_unauthorized(self):
        """测试未授权回调"""
        from src.modules.orders.query_handler import handle_callback
        from telegram.ext import ConversationHandler

        update = MagicMock()
        update.effective_user.id = 999999
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.data = "orders_list"

        context = MagicMock()
        context.user_data = {'order_filters': {}}

        with patch('src.modules.orders.query_handler.settings') as mock_settings:
            mock_settings.bot_owner_id = 123456
            result = await handle_callback(update, context)

        assert result == ConversationHandler.END
        update.callback_query.answer.assert_called_once_with("⛔ 权限不足", show_alert=True)

    @pytest.mark.asyncio
    async def test_handle_callback_orders_list(self):
        """测试订单列表回调"""
        from src.modules.orders.query_handler import handle_callback, SHOW_ORDERS
        from datetime import datetime

        update = MagicMock()
        update.effective_user.id = 123456
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "orders_list"

        context = MagicMock()
        context.user_data = {'order_filters': {'page': 1, 'per_page': 10}}

        with patch('src.modules.orders.query_handler.settings') as mock_settings, \
             patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_settings.bot_owner_id = 123456
            mock_db = MagicMock()
            mock_db.execute.return_value.scalars.return_value.all.return_value = []
            mock_db.execute.return_value.scalar.return_value = 0
            mock_session.return_value = mock_db

            result = await handle_callback(update, context)

        assert result == SHOW_ORDERS

    @pytest.mark.asyncio
    async def test_handle_callback_filter_type(self):
        """测试类型过滤回调"""
        from src.modules.orders.query_handler import handle_callback, SHOW_ORDERS

        update = MagicMock()
        update.effective_user.id = 123456
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "orders_filter_type"

        context = MagicMock()
        context.user_data = {'order_filters': {}}

        with patch('src.modules.orders.query_handler.settings') as mock_settings:
            mock_settings.bot_owner_id = 123456
            result = await handle_callback(update, context)

        assert result == SHOW_ORDERS

    @pytest.mark.asyncio
    async def test_handle_callback_set_type_filter(self):
        """测试设置类型过滤"""
        from src.modules.orders.query_handler import handle_callback, SHOW_ORDERS

        update = MagicMock()
        update.effective_user.id = 123456
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "orders_type_premium"

        context = MagicMock()
        context.user_data = {'order_filters': {'page': 1}}

        with patch('src.modules.orders.query_handler.settings') as mock_settings, \
             patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_settings.bot_owner_id = 123456
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.scalar.return_value = 0
            mock_db.query.return_value.scalar.return_value = 0
            mock_session.return_value = mock_db

            result = await handle_callback(update, context)

        assert result == SHOW_ORDERS
        assert context.user_data['order_filters']['order_type'] == 'premium'

    @pytest.mark.asyncio
    async def test_handle_callback_set_status_filter(self):
        """测试设置状态过滤"""
        from src.modules.orders.query_handler import handle_callback, SHOW_ORDERS

        update = MagicMock()
        update.effective_user.id = 123456
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "orders_status_PAID"

        context = MagicMock()
        context.user_data = {'order_filters': {'page': 1}}

        with patch('src.modules.orders.query_handler.settings') as mock_settings, \
             patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_settings.bot_owner_id = 123456
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.scalar.return_value = 0
            mock_db.query.return_value.scalar.return_value = 0
            mock_session.return_value = mock_db

            result = await handle_callback(update, context)

        assert result == SHOW_ORDERS
        assert context.user_data['order_filters']['status'] == 'PAID'

    @pytest.mark.asyncio
    async def test_handle_callback_pagination(self):
        """测试分页回调"""
        from src.modules.orders.query_handler import handle_callback, SHOW_ORDERS

        update = MagicMock()
        update.effective_user.id = 123456
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "orders_page_3"

        context = MagicMock()
        context.user_data = {'order_filters': {'page': 1, 'per_page': 10}}

        with patch('src.modules.orders.query_handler.settings') as mock_settings, \
             patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_settings.bot_owner_id = 123456
            mock_db = MagicMock()
            mock_db.execute.return_value.scalars.return_value.all.return_value = []
            mock_db.execute.return_value.scalar.return_value = 30
            mock_session.return_value = mock_db

            result = await handle_callback(update, context)

        assert result == SHOW_ORDERS
        assert context.user_data['order_filters']['page'] == 3

    @pytest.mark.asyncio
    async def test_handle_callback_clear_filter(self):
        """测试清除过滤"""
        from src.modules.orders.query_handler import handle_callback, SHOW_ORDERS

        update = MagicMock()
        update.effective_user.id = 123456
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "orders_clear_filter"

        context = MagicMock()
        context.user_data = {
            'order_filters': {
                'order_type': 'premium',
                'status': 'PAID',
                'user_id': 123,
                'page': 5
            }
        }

        with patch('src.modules.orders.query_handler.settings') as mock_settings, \
             patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_settings.bot_owner_id = 123456
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.scalar.return_value = 0
            mock_db.query.return_value.scalar.return_value = 0
            mock_session.return_value = mock_db

            result = await handle_callback(update, context)

        assert result == SHOW_ORDERS
        filters = context.user_data['order_filters']
        assert filters['order_type'] is None
        assert filters['status'] is None
        assert filters['user_id'] is None
        assert filters['page'] == 1

    @pytest.mark.asyncio
    async def test_handle_callback_close(self):
        """测试关闭回调"""
        from src.modules.orders.query_handler import handle_callback
        from telegram.ext import ConversationHandler

        update = MagicMock()
        update.effective_user.id = 123456
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.delete_message = AsyncMock()
        update.callback_query.data = "orders_close"

        context = MagicMock()
        context.user_data = {'order_filters': {}}

        with patch('src.modules.orders.query_handler.settings') as mock_settings:
            mock_settings.bot_owner_id = 123456
            result = await handle_callback(update, context)

        assert result == ConversationHandler.END
        update.callback_query.delete_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_callback_back(self):
        """测试返回回调"""
        from src.modules.orders.query_handler import handle_callback, SHOW_ORDERS

        update = MagicMock()
        update.effective_user.id = 123456
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "orders_back"

        context = MagicMock()
        context.user_data = {'order_filters': {'page': 1}}

        with patch('src.modules.orders.query_handler.settings') as mock_settings, \
             patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_settings.bot_owner_id = 123456
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.scalar.return_value = 0
            mock_db.query.return_value.scalar.return_value = 0
            mock_session.return_value = mock_db

            result = await handle_callback(update, context)

        assert result == SHOW_ORDERS

    @pytest.mark.asyncio
    async def test_handle_callback_order_detail(self):
        """测试订单详情回调"""
        from src.modules.orders.query_handler import handle_callback, SHOW_ORDERS

        update = MagicMock()
        update.effective_user.id = 123456
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "orders_detail_ORDER123"

        context = MagicMock()
        context.user_data = {'order_filters': {}}

        mock_order = MagicMock()
        mock_order.order_id = "ORDER123"
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

        with patch('src.modules.orders.query_handler.settings') as mock_settings, \
             patch('src.modules.orders.query_handler.SessionLocal') as mock_session:
            mock_settings.bot_owner_id = 123456
            mock_db = MagicMock()
            mock_db.query.return_value.filter_by.return_value.first.return_value = mock_order
            mock_session.return_value = mock_db

            result = await handle_callback(update, context)

        assert result == SHOW_ORDERS


class TestCancelFunction:
    """测试取消功能"""

    @pytest.mark.asyncio
    async def test_cancel_with_message(self):
        """测试通过消息取消"""
        from src.modules.orders.query_handler import cancel
        from telegram.ext import ConversationHandler

        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        result = await cancel(update, context)

        assert result == ConversationHandler.END
        update.message.reply_text.assert_called_once_with("已取消订单查询")

    @pytest.mark.asyncio
    async def test_cancel_without_message(self):
        """测试无消息取消"""
        from src.modules.orders.query_handler import cancel
        from telegram.ext import ConversationHandler

        update = MagicMock()
        update.message = None

        context = MagicMock()

        result = await cancel(update, context)

        assert result == ConversationHandler.END


class TestOwnerOnlyDecorator:
    """测试 owner_only 装饰器"""

    @pytest.mark.asyncio
    async def test_owner_only_unauthorized(self):
        """测试非管理员被拒绝"""
        from src.modules.orders.query_handler import owner_only
        from telegram.ext import ConversationHandler

        @owner_only
        async def test_func(update, context):
            return "success"

        update = MagicMock()
        update.effective_user.id = 999999
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        with patch('src.modules.orders.query_handler.settings') as mock_settings:
            mock_settings.bot_owner_id = 123456
            result = await test_func(update, context)

        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_owner_only_authorized(self):
        """测试管理员通过"""
        from src.modules.orders.query_handler import owner_only

        @owner_only
        async def test_func(update, context):
            return "success"

        update = MagicMock()
        update.effective_user.id = 123456

        context = MagicMock()

        with patch('src.modules.orders.query_handler.settings') as mock_settings:
            mock_settings.bot_owner_id = 123456
            result = await test_func(update, context)

        assert result == "success"
