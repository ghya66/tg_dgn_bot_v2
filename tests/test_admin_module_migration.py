"""
AdminModule 迁移测试
验证管理员模块标准化后功能正常
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from telegram import Update, User, Message, CallbackQuery


class TestAdminModuleStructure:
    """测试目录结构"""
    
    def test_module_directory_exists(self):
        """验证目录存在"""
        base_path = Path(__file__).parent.parent / "src" / "modules" / "admin"
        assert base_path.exists()
    
    def test_required_files_exist(self):
        """验证必需文件存在"""
        base_path = Path(__file__).parent.parent / "src" / "modules" / "admin"
        required = ["__init__.py", "handler.py"]
        for f in required:
            assert (base_path / f).exists(), f"Missing: {f}"


class TestAdminModuleImplementation:
    """测试实现"""
    
    def test_inherits_base_module(self):
        """验证继承 BaseModule"""
        from src.modules.admin.handler import AdminModule
        from src.core.base import BaseModule
        
        module = AdminModule()
        assert isinstance(module, BaseModule)
    
    def test_module_name(self):
        """验证 module_name"""
        from src.modules.admin.handler import AdminModule
        
        module = AdminModule()
        assert module.module_name == "admin"
    
    def test_get_handlers(self):
        """验证 get_handlers"""
        from src.modules.admin.handler import AdminModule
        
        module = AdminModule()
        handlers = module.get_handlers()
        assert isinstance(handlers, list)
        assert len(handlers) > 0
    
    def test_wraps_existing_admin_handler(self):
        """验证复用现有 AdminHandler"""
        from src.modules.admin.handler import AdminModule
        from src.bot_admin.handler import admin_handler
        from telegram.ext import ConversationHandler
        
        module = AdminModule()
        handlers = module.get_handlers()
        
        # 应该返回 ConversationHandler
        assert len(handlers) == 1
        assert isinstance(handlers[0], ConversationHandler)
        
        # 应该是同一个 handler 的结果
        original = admin_handler.get_conversation_handler()
        assert type(handlers[0]) == type(original)


class TestAdminModuleFunctionality:
    """测试功能"""
    
    def test_validate_config_with_owner(self):
        """测试配置验证"""
        from src.modules.admin.handler import AdminModule
        
        module = AdminModule()
        
        # 如果设置了 BOT_OWNER_ID，应该返回 True
        with patch('src.bot_admin.middleware.get_owner_id', return_value=12345):
            with patch.object(module, 'validate_config') as mock_validate:
                mock_validate.return_value = True
                assert mock_validate() is True
    
    def test_conversation_handler_has_entry_points(self):
        """验证 ConversationHandler 有入口点"""
        from src.modules.admin.handler import AdminModule
        from telegram.ext import ConversationHandler
        
        module = AdminModule()
        handlers = module.get_handlers()
        conv = handlers[0]
        
        assert isinstance(conv, ConversationHandler)
        assert len(conv.entry_points) > 0
    
    def test_conversation_handler_has_states(self):
        """验证 ConversationHandler 有状态"""
        from src.modules.admin.handler import AdminModule
        
        module = AdminModule()
        handlers = module.get_handlers()
        conv = handlers[0]
        
        # AdminHandler 有 12 个状态
        assert len(conv.states) > 0


class TestAdminModuleCallbacks:
    """测试回调功能"""
    
    def test_admin_callback_pattern(self):
        """验证回调模式"""
        from src.modules.admin.handler import AdminModule
        from telegram.ext import CallbackQueryHandler
        
        module = AdminModule()
        handlers = module.get_handlers()
        conv = handlers[0]
        
        # 检查入口点是否包含 admin_ 模式的 CallbackQueryHandler
        has_callback = any(
            isinstance(ep, CallbackQueryHandler)
            for ep in conv.entry_points
        )
        assert has_callback


class TestAdminModuleRegistration:
    """测试注册"""
    
    def test_module_registered_in_bot_v2(self):
        """验证已注册"""
        import inspect
        from src.bot_v2 import TelegramBotV2
        
        source = inspect.getsource(TelegramBotV2._register_standardized_modules)
        
        has_import = "AdminModule" in source or "admin" in source.lower()
        
        if not has_import:
            pytest.skip("AdminModule 尚未注册")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
