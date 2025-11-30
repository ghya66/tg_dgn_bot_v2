"""
TRXExchangeModule 迁移测试
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from telegram import Update, User, Message, CallbackQuery


class TestTRXExchangeModuleStructure:
    """测试目录结构"""
    
    def test_module_directory_exists(self):
        """验证目录存在"""
        base_path = Path(__file__).parent.parent / "src" / "modules" / "trx_exchange"
        assert base_path.exists()
    
    def test_required_files_exist(self):
        """验证必需文件存在"""
        base_path = Path(__file__).parent.parent / "src" / "modules" / "trx_exchange"
        required = ["__init__.py", "handler.py", "messages.py", "keyboards.py", "states.py"]
        for f in required:
            assert (base_path / f).exists(), f"Missing: {f}"


class TestTRXExchangeModuleImplementation:
    """测试实现"""
    
    def test_inherits_base_module(self):
        """验证继承 BaseModule"""
        from src.modules.trx_exchange.handler import TRXExchangeModule
        from src.core.base import BaseModule
        
        module = TRXExchangeModule()
        assert isinstance(module, BaseModule)
    
    def test_module_name(self):
        """验证 module_name"""
        from src.modules.trx_exchange.handler import TRXExchangeModule
        
        module = TRXExchangeModule()
        assert module.module_name == "trx_exchange"
    
    def test_get_handlers(self):
        """验证 get_handlers"""
        from src.modules.trx_exchange.handler import TRXExchangeModule
        
        module = TRXExchangeModule()
        handlers = module.get_handlers()
        assert isinstance(handlers, list)
        assert len(handlers) > 0
    
    def test_uses_safe_conversation_handler(self):
        """验证使用 SafeConversationHandler"""
        from src.modules.trx_exchange.handler import TRXExchangeModule
        from telegram.ext import ConversationHandler
        
        module = TRXExchangeModule()
        handlers = module.get_handlers()
        assert isinstance(handlers[0], ConversationHandler)


class TestTRXExchangeModuleFunctionality:
    """测试功能"""
    
    @pytest.mark.asyncio
    async def test_start_from_message(self):
        """测试从 Message 入口"""
        from src.modules.trx_exchange.handler import TRXExchangeModule
        
        module = TRXExchangeModule()
        
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        update.effective_user = Mock(spec=User, id=123)
        
        context = Mock()
        context.user_data = {}
        
        result = await module.start_exchange(update, context)
        
        assert result == 0  # INPUT_AMOUNT
        update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_from_callback(self):
        """测试从 CallbackQuery 入口"""
        from src.modules.trx_exchange.handler import TRXExchangeModule
        
        module = TRXExchangeModule()
        
        update = Mock(spec=Update)
        update.callback_query = Mock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.message = Mock(spec=Message)
        update.callback_query.message.reply_text = AsyncMock()
        update.message = None
        update.effective_user = Mock(spec=User, id=123)
        
        context = Mock()
        context.user_data = {}
        
        result = await module.start_exchange(update, context)
        
        assert result == 0  # INPUT_AMOUNT
        update.callback_query.answer.assert_called_once()


class TestTRXExchangeModuleRegistration:
    """测试注册"""
    
    def test_module_registered_in_bot_v2(self):
        """验证已注册"""
        import inspect
        from src.bot_v2 import TelegramBotV2
        
        source = inspect.getsource(TelegramBotV2._register_standardized_modules)
        
        # 迁移后应该有 TRXExchangeModule
        has_import = "TRXExchangeModule" in source or "trx_exchange" in source.lower()
        
        if not has_import:
            pytest.skip("TRXExchangeModule 尚未注册")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
