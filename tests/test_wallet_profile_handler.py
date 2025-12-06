"""
测试 src/wallet/profile_handler.py
个人中心处理器测试
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from telegram.ext import ConversationHandler


class TestProfileHandlerImport:
    """测试模块导入"""
    
    def test_import_profile_handler(self):
        """测试导入 ProfileHandler"""
        from src.wallet.profile_handler import ProfileHandler
        assert ProfileHandler is not None
    
    def test_import_get_profile_handlers(self):
        """测试导入 get_profile_handlers"""
        from src.wallet.profile_handler import get_profile_handlers
        assert callable(get_profile_handlers)
    
    def test_import_conversation_state(self):
        """测试导入对话状态"""
        from src.wallet.profile_handler import AWAITING_DEPOSIT_AMOUNT
        assert AWAITING_DEPOSIT_AMOUNT == 1


class TestBuildProfileText:
    """测试构建个人中心文本"""
    
    def test_build_profile_text_with_full_name(self):
        """测试使用全名构建文本"""
        from src.wallet.profile_handler import ProfileHandler
        
        user = MagicMock()
        user.full_name = "Test User"
        user.username = "testuser"
        user.id = 123456
        
        result = ProfileHandler._build_profile_text(user, 100.5)
        
        assert "个人中心" in result
        assert "Test User" in result
        assert "123456" in result
        assert "100.500" in result
    
    def test_build_profile_text_with_username_only(self):
        """测试仅使用用户名构建文本"""
        from src.wallet.profile_handler import ProfileHandler
        
        user = MagicMock()
        user.full_name = None
        user.username = "testuser"
        user.id = 123456
        
        result = ProfileHandler._build_profile_text(user, 50.0)
        
        assert "testuser" in result
        assert "50.000" in result
    
    def test_build_profile_text_fallback_to_user_id(self):
        """测试回退到用户ID"""
        from src.wallet.profile_handler import ProfileHandler
        
        user = MagicMock()
        user.full_name = None
        user.username = None
        user.id = 789012
        
        result = ProfileHandler._build_profile_text(user, 0.0)
        
        assert "User_789012" in result
    
    def test_build_profile_text_escapes_html(self):
        """测试HTML转义"""
        from src.wallet.profile_handler import ProfileHandler
        
        user = MagicMock()
        user.full_name = "<script>alert('xss')</script>"
        user.username = None
        user.id = 123
        
        result = ProfileHandler._build_profile_text(user, 10.0)
        
        assert "<script>" not in result
        assert "&lt;script&gt;" in result


class TestProfileCommand:
    """测试 /profile 命令"""
    
    @pytest.mark.asyncio
    async def test_profile_command(self):
        """测试 profile 命令"""
        from src.wallet.profile_handler import ProfileHandler
        
        update = MagicMock()
        update.effective_user.id = 123456
        update.effective_user.full_name = "Test User"
        update.effective_user.username = "testuser"
        update.message.reply_text = AsyncMock()
        
        context = MagicMock()
        
        with patch('src.wallet.profile_handler.WalletManager') as mock_wallet:
            mock_instance = MagicMock()
            mock_instance.get_balance.return_value = 100.0
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_wallet.return_value = mock_instance
            
            await ProfileHandler.profile_command(update, context)
        
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "个人中心" in call_args[0][0]
        assert call_args[1]['parse_mode'] == "HTML"


class TestProfileCommandCallback:
    """测试从主菜单进入个人中心的回调"""
    
    @pytest.mark.asyncio
    async def test_profile_command_callback(self):
        """测试回调进入个人中心"""
        from src.wallet.profile_handler import ProfileHandler
        
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.effective_user.id = 123456
        update.effective_user.full_name = "Test User"
        update.effective_user.username = "testuser"
        
        context = MagicMock()
        
        with patch('src.wallet.profile_handler.WalletManager') as mock_wallet:
            mock_instance = MagicMock()
            mock_instance.get_balance.return_value = 50.0
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_wallet.return_value = mock_instance
            
            await ProfileHandler.profile_command_callback(update, context)
        
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()


class TestBalanceQuery:
    """测试余额查询"""

    @pytest.mark.asyncio
    async def test_balance_query(self):
        """测试余额查询"""
        from src.wallet.profile_handler import ProfileHandler

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.effective_user.id = 123456

        context = MagicMock()

        # Mock deposits and debits
        mock_deposit = MagicMock()
        mock_deposit.total_amount = 100.0
        mock_deposit.status = "PAID"

        mock_debit = MagicMock()
        mock_debit.get_amount.return_value = 30.0

        with patch('src.wallet.profile_handler.WalletManager') as mock_wallet:
            mock_instance = MagicMock()
            mock_instance.get_balance.return_value = 70.0
            mock_instance.get_user_deposits.return_value = [mock_deposit]
            mock_instance.get_user_debits.return_value = [mock_debit]
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_wallet.return_value = mock_instance

            await ProfileHandler.balance_query(update, context)

        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "余额详情" in text
        assert "70.000" in text
        assert "100.000" in text
        assert "30.000" in text


class TestStartDeposit:
    """测试开始充值流程"""

    @pytest.mark.asyncio
    async def test_start_deposit(self):
        """测试开始充值"""
        from src.wallet.profile_handler import ProfileHandler, AWAITING_DEPOSIT_AMOUNT

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()

        result = await ProfileHandler.start_deposit(update, context)

        assert result == AWAITING_DEPOSIT_AMOUNT
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "充值 USDT" in text
        assert "最小充值: 1 USDT" in text


class TestReceiveDepositAmount:
    """测试接收充值金额"""

    @pytest.mark.asyncio
    async def test_receive_deposit_amount_too_small(self):
        """测试金额太小"""
        from src.wallet.profile_handler import ProfileHandler, AWAITING_DEPOSIT_AMOUNT

        update = MagicMock()
        update.effective_user.id = 123456
        update.message.text = "0.5"
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        result = await ProfileHandler.receive_deposit_amount(update, context)

        assert result == AWAITING_DEPOSIT_AMOUNT
        update.message.reply_text.assert_called_once()
        args = update.message.reply_text.call_args[0][0]
        assert "金额太小" in args

    @pytest.mark.asyncio
    async def test_receive_deposit_amount_too_large(self):
        """测试金额过大"""
        from src.wallet.profile_handler import ProfileHandler, AWAITING_DEPOSIT_AMOUNT

        update = MagicMock()
        update.effective_user.id = 123456
        update.message.text = "50000"
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        result = await ProfileHandler.receive_deposit_amount(update, context)

        assert result == AWAITING_DEPOSIT_AMOUNT
        update.message.reply_text.assert_called_once()
        args = update.message.reply_text.call_args[0][0]
        assert "金额过大" in args

    @pytest.mark.asyncio
    async def test_receive_deposit_amount_invalid_format(self):
        """测试无效格式"""
        from src.wallet.profile_handler import ProfileHandler, AWAITING_DEPOSIT_AMOUNT

        update = MagicMock()
        update.effective_user.id = 123456
        update.message.text = "not_a_number"
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        result = await ProfileHandler.receive_deposit_amount(update, context)

        assert result == AWAITING_DEPOSIT_AMOUNT
        update.message.reply_text.assert_called_once()
        args = update.message.reply_text.call_args[0][0]
        assert "格式错误" in args

    @pytest.mark.asyncio
    async def test_receive_deposit_amount_no_suffix(self):
        """测试无可用后缀"""
        from src.wallet.profile_handler import ProfileHandler

        update = MagicMock()
        update.effective_user.id = 123456
        update.message.text = "100"
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        with patch('src.wallet.profile_handler.suffix_manager') as mock_suffix:
            mock_suffix.connect = AsyncMock()
            mock_suffix.allocate_suffix = AsyncMock(return_value=None)

            result = await ProfileHandler.receive_deposit_amount(update, context)

        assert result == ConversationHandler.END
        update.message.reply_text.assert_called_once()
        args = update.message.reply_text.call_args[0][0]
        assert "系统繁忙" in args

    @pytest.mark.asyncio
    async def test_receive_deposit_amount_success(self):
        """测试成功创建充值订单"""
        from src.wallet.profile_handler import ProfileHandler
        from datetime import datetime, timedelta

        update = MagicMock()
        update.effective_user.id = 123456
        update.message.text = "100"
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        # Mock order
        mock_order = MagicMock()
        mock_order.order_id = "ORDER123"
        mock_order.total_amount = 100.001
        mock_order.created_at = datetime.now()
        mock_order.expires_at = datetime.now() + timedelta(minutes=30)

        with patch('src.wallet.profile_handler.suffix_manager') as mock_suffix, \
             patch('src.wallet.profile_handler.WalletManager') as mock_wallet, \
             patch('src.wallet.profile_handler.settings') as mock_settings, \
             patch('src.wallet.profile_handler.get_order_timeout_minutes') as mock_timeout:

            mock_suffix.connect = AsyncMock()
            mock_suffix.allocate_suffix = AsyncMock(return_value=0.001)
            mock_suffix.set_order_id = AsyncMock()

            mock_instance = MagicMock()
            mock_instance.create_deposit_order.return_value = mock_order
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_wallet.return_value = mock_instance

            mock_settings.usdt_trc20_receive_addr = "TTestAddress123"
            mock_timeout.return_value = 30

            result = await ProfileHandler.receive_deposit_amount(update, context)

        assert result == ConversationHandler.END
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        text = call_args[0][0]
        assert "充值订单已创建" in text
        assert "ORDER123" in text


class TestDepositHistory:
    """测试充值记录"""

    @pytest.mark.asyncio
    async def test_deposit_history_empty(self):
        """测试空充值记录"""
        from src.wallet.profile_handler import ProfileHandler

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.effective_user.id = 123456

        context = MagicMock()

        with patch('src.wallet.profile_handler.WalletManager') as mock_wallet:
            mock_instance = MagicMock()
            mock_instance.get_user_deposits.return_value = []
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_wallet.return_value = mock_instance

            await ProfileHandler.deposit_history(update, context)

        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "暂无充值记录" in text

    @pytest.mark.asyncio
    async def test_deposit_history_with_records(self):
        """测试有充值记录"""
        from src.wallet.profile_handler import ProfileHandler
        from datetime import datetime

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.effective_user.id = 123456

        context = MagicMock()

        # Mock deposits
        mock_deposit1 = MagicMock()
        mock_deposit1.total_amount = 100.0
        mock_deposit1.status = "PAID"
        mock_deposit1.created_at = datetime(2025, 1, 1, 10, 0, 0)

        mock_deposit2 = MagicMock()
        mock_deposit2.total_amount = 50.0
        mock_deposit2.status = "PENDING"
        mock_deposit2.created_at = datetime(2025, 1, 2, 15, 30, 0)

        mock_deposit3 = MagicMock()
        mock_deposit3.total_amount = 25.0
        mock_deposit3.status = "EXPIRED"
        mock_deposit3.created_at = datetime(2025, 1, 3, 8, 0, 0)

        with patch('src.wallet.profile_handler.WalletManager') as mock_wallet:
            mock_instance = MagicMock()
            mock_instance.get_user_deposits.return_value = [mock_deposit1, mock_deposit2, mock_deposit3]
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_wallet.return_value = mock_instance

            await ProfileHandler.deposit_history(update, context)

        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "充值记录" in text
        assert "100.000" in text
        assert "50.000" in text
        assert "25.000" in text
        assert "✅" in text  # PAID
        assert "⏰" in text  # PENDING
        assert "❌" in text  # EXPIRED


class TestBackToProfile:
    """测试返回个人中心"""

    @pytest.mark.asyncio
    async def test_back_to_profile(self):
        """测试返回个人中心"""
        from src.wallet.profile_handler import ProfileHandler

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.effective_user.id = 123456

        context = MagicMock()

        with patch('src.wallet.profile_handler.WalletManager') as mock_wallet:
            mock_instance = MagicMock()
            mock_instance.get_balance.return_value = 75.5
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_wallet.return_value = mock_instance

            await ProfileHandler.back_to_profile(update, context)

        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "个人中心" in text
        assert "75.500" in text


class TestCancel:
    """测试取消操作"""

    @pytest.mark.asyncio
    async def test_cancel_with_callback(self):
        """测试通过回调取消"""
        from src.wallet.profile_handler import ProfileHandler

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.message = None

        context = MagicMock()
        context.user_data = {}

        # patch 原始模块位置，因为 NavigationManager 是在 cancel 方法内部 lazy import 的
        with patch('src.common.navigation_manager.NavigationManager') as mock_nav:
            mock_nav.cleanup_and_show_main_menu = AsyncMock(return_value=ConversationHandler.END)

            result = await ProfileHandler.cancel(update, context)

        update.callback_query.answer.assert_called_once_with("已取消")
        mock_nav.cleanup_and_show_main_menu.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_without_callback(self):
        """测试无回调取消"""
        from src.wallet.profile_handler import ProfileHandler

        update = MagicMock()
        update.callback_query = None
        update.message = MagicMock()

        context = MagicMock()
        context.user_data = {}

        # patch 原始模块位置，因为 NavigationManager 是在 cancel 方法内部 lazy import 的
        with patch('src.common.navigation_manager.NavigationManager') as mock_nav:
            mock_nav.cleanup_and_show_main_menu = AsyncMock(return_value=ConversationHandler.END)

            result = await ProfileHandler.cancel(update, context)

        mock_nav.cleanup_and_show_main_menu.assert_called_once()


class TestGetProfileHandlers:
    """测试获取处理器列表"""

    def test_get_profile_handlers(self):
        """测试获取处理器列表"""
        from src.wallet.profile_handler import get_profile_handlers

        handlers = get_profile_handlers()

        assert isinstance(handlers, list)
        assert len(handlers) >= 4  # 至少4个处理器

    def test_handlers_include_conversation_handler(self):
        """测试包含对话处理器"""
        from src.wallet.profile_handler import get_profile_handlers
        from telegram.ext import ConversationHandler

        handlers = get_profile_handlers()

        conv_handlers = [h for h in handlers if isinstance(h, ConversationHandler)]
        assert len(conv_handlers) >= 1

