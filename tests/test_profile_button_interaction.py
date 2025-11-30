"""
ProfileModule 按钮交互测试
验证个人中心按钮功能正常
"""
import pytest
from unittest.mock import AsyncMock, Mock
from telegram import Update, User, Message, CallbackQuery


class TestProfileButtonInteraction:
    """测试 ProfileModule 按钮交互"""
    
    @pytest.mark.asyncio
    async def test_profile_from_reply_button(self):
        """测试从 Reply 按钮进入个人中心"""
        from src.modules.profile.handler import ProfileModule
        
        module = ProfileModule()
        
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.text = "👤 个人中心"
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        update.effective_user = Mock(spec=User, id=123, full_name="Test User")
        
        context = Mock()
        context.user_data = {}
        
        result = await module.show_profile(update, context)
        
        assert result is not None
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "个人中心" in call_args[0][0] or "个人中心" in str(call_args[1])
        print("[OK] Reply button '👤 个人中心' works")
    
    @pytest.mark.asyncio
    async def test_profile_from_inline_button(self):
        """测试从 Inline 按钮进入个人中心"""
        from src.modules.profile.handler import ProfileModule
        
        module = ProfileModule()
        
        update = Mock(spec=Update)
        update.callback_query = Mock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.message = Mock(spec=Message)
        update.callback_query.message.edit_text = AsyncMock()
        update.callback_query.data = "menu_profile"
        update.message = None
        update.effective_user = Mock(spec=User, id=123, full_name="Test")
        
        context = Mock()
        context.user_data = {}
        
        result = await module.show_profile(update, context)
        
        assert result is not None
        update.callback_query.answer.assert_called_once()
        update.callback_query.message.edit_text.assert_called_once()
        print("[OK] Inline button 'menu_profile' works")
    
    @pytest.mark.asyncio
    async def test_balance_button(self):
        """测试余额查询按钮"""
        from src.modules.profile.handler import ProfileModule
        
        module = ProfileModule()
        
        update = Mock(spec=Update)
        update.callback_query = Mock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "profile_balance"
        update.effective_user = Mock(spec=User, id=123)
        
        context = Mock()
        
        result = await module.show_balance(update, context)
        
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        print("[OK] Balance button works")
    
    @pytest.mark.asyncio
    async def test_deposit_button(self):
        """测试充值按钮"""
        from src.modules.profile.handler import ProfileModule
        
        module = ProfileModule()
        
        update = Mock(spec=Update)
        update.callback_query = Mock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "profile_deposit"
        update.effective_user = Mock(spec=User, id=123)
        
        context = Mock()
        
        result = await module.start_deposit(update, context)
        
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        print("[OK] Deposit button works")
    
    @pytest.mark.asyncio
    async def test_history_button(self):
        """测试充值记录按钮"""
        from src.modules.profile.handler import ProfileModule
        
        module = ProfileModule()
        
        update = Mock(spec=Update)
        update.callback_query = Mock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "profile_history"
        update.effective_user = Mock(spec=User, id=123)
        
        context = Mock()
        
        result = await module.show_history(update, context)
        
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        print("[OK] History button works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
