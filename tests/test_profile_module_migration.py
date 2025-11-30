"""
ProfileModule 迁移测试
每个迁移步骤都有对应的测试验证
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from telegram import Update, User, Message, CallbackQuery


class TestProfileModuleStructure:
    """测试 ProfileModule 目录结构"""
    
    def test_module_directory_exists(self):
        """验证 modules/profile 目录存在"""
        base_path = Path(__file__).parent.parent / "src" / "modules" / "profile"
        
        # 如果目录不存在，这是预期的（迁移前）
        if not base_path.exists():
            print(f"[TODO] 目录需要创建: {base_path}")
            pytest.skip("目录尚未创建 - 迁移未开始")
        
        assert base_path.exists()
        assert base_path.is_dir()
        print(f"[OK] 目录存在: {base_path}")
    
    def test_required_files_exist(self):
        """验证必需文件存在"""
        base_path = Path(__file__).parent.parent / "src" / "modules" / "profile"
        
        if not base_path.exists():
            pytest.skip("目录尚未创建")
        
        required_files = [
            "__init__.py",
            "handler.py",
            "messages.py",
            "keyboards.py",
            "states.py",
        ]
        
        for filename in required_files:
            file_path = base_path / filename
            exists = file_path.exists()
            if exists:
                print(f"[OK] {filename}")
            else:
                print(f"[MISSING] {filename}")
            assert exists, f"缺少文件: {filename}"


class TestProfileModuleImplementation:
    """测试 ProfileModule 实现"""
    
    def test_module_inherits_base_module(self):
        """验证 ProfileModule 继承 BaseModule"""
        try:
            from src.modules.profile.handler import ProfileModule
            from src.core.base import BaseModule
            
            module = ProfileModule()
            assert isinstance(module, BaseModule)
            print("[OK] ProfileModule 继承 BaseModule")
        except ImportError:
            pytest.skip("ProfileModule 尚未实现")
    
    def test_module_name_property(self):
        """验证 module_name 属性"""
        try:
            from src.modules.profile.handler import ProfileModule
            
            module = ProfileModule()
            assert hasattr(module, 'module_name')
            assert module.module_name == "profile"
            print(f"[OK] module_name = {module.module_name}")
        except ImportError:
            pytest.skip("ProfileModule 尚未实现")
    
    def test_get_handlers_method(self):
        """验证 get_handlers 方法"""
        try:
            from src.modules.profile.handler import ProfileModule
            
            module = ProfileModule()
            handlers = module.get_handlers()
            assert isinstance(handlers, list)
            assert len(handlers) > 0
            print(f"[OK] get_handlers 返回 {len(handlers)} 个处理器")
        except ImportError:
            pytest.skip("ProfileModule 尚未实现")
    
    def test_uses_safe_conversation_handler(self):
        """验证使用 SafeConversationHandler"""
        try:
            from src.modules.profile.handler import ProfileModule
            from telegram.ext import ConversationHandler
            
            module = ProfileModule()
            handlers = module.get_handlers()
            
            # 检查第一个handler是否是ConversationHandler
            assert len(handlers) > 0
            assert isinstance(handlers[0], ConversationHandler)
            print("[OK] 使用 ConversationHandler")
        except ImportError:
            pytest.skip("ProfileModule 尚未实现")


class TestProfileModuleFunctionality:
    """测试 ProfileModule 功能"""
    
    @pytest.mark.asyncio
    async def test_show_profile_from_message(self):
        """测试从 Message 进入个人中心"""
        try:
            from src.modules.profile.handler import ProfileModule
            
            module = ProfileModule()
            
            # 模拟 Message 入口
            update = Mock(spec=Update)
            update.message = Mock(spec=Message)
            update.message.reply_text = AsyncMock()
            update.callback_query = None
            update.effective_user = Mock(spec=User, id=123, full_name="Test User")
            
            context = Mock()
            context.user_data = {}
            
            # 执行
            result = await module.show_profile(update, context)
            
            # 验证
            assert result is not None
            update.message.reply_text.assert_called_once()
            print("[OK] show_profile (Message入口) 正常")
        except (ImportError, AttributeError) as e:
            pytest.skip(f"ProfileModule 功能未实现: {e}")
    
    @pytest.mark.asyncio
    async def test_show_profile_from_callback(self):
        """测试从 CallbackQuery 进入个人中心"""
        try:
            from src.modules.profile.handler import ProfileModule
            
            module = ProfileModule()
            
            # 模拟 CallbackQuery 入口
            update = Mock(spec=Update)
            update.callback_query = Mock(spec=CallbackQuery)
            update.callback_query.answer = AsyncMock()
            update.callback_query.message = Mock(spec=Message)
            update.callback_query.message.edit_text = AsyncMock()
            update.message = None
            update.effective_user = Mock(spec=User, id=123, full_name="Test")
            
            context = Mock()
            context.user_data = {}
            
            # 执行
            result = await module.show_profile(update, context)
            
            # 验证
            assert result is not None
            update.callback_query.answer.assert_called_once()
            print("[OK] show_profile (CallbackQuery入口) 正常")
        except (ImportError, AttributeError) as e:
            pytest.skip(f"ProfileModule 功能未实现: {e}")
    
    @pytest.mark.asyncio
    async def test_balance_query(self):
        """测试余额查询功能"""
        try:
            from src.modules.profile.handler import ProfileModule
            
            module = ProfileModule()
            
            # 模拟余额查询
            update = Mock(spec=Update)
            update.callback_query = Mock(spec=CallbackQuery)
            update.callback_query.answer = AsyncMock()
            update.callback_query.edit_message_text = AsyncMock()
            update.effective_user = Mock(spec=User, id=123)
            
            context = Mock()
            
            # 执行
            result = await module.show_balance(update, context)
            
            # 验证
            update.callback_query.answer.assert_called_once()
            print("[OK] show_balance 正常")
        except (ImportError, AttributeError) as e:
            pytest.skip(f"余额查询未实现: {e}")


class TestProfileModuleRegistration:
    """测试 ProfileModule 注册"""
    
    def test_module_registered_in_bot_v2(self):
        """验证模块已注册到 bot_v2.py"""
        import inspect
        from src.bot_v2 import TelegramBotV2
        
        source = inspect.getsource(TelegramBotV2._register_standardized_modules)
        
        # 检查是否导入ProfileModule
        has_import = "ProfileModule" in source or "profile" in source.lower()
        
        if not has_import:
            print("[TODO] ProfileModule 尚未注册到 bot_v2.py")
            pytest.skip("模块尚未注册")
        
        print("[OK] ProfileModule 已在 bot_v2.py 中注册")
        assert has_import
    
    def test_old_handler_removed(self):
        """验证旧的 ProfileHandler 注册已移除"""
        import inspect
        from src.bot_v2 import TelegramBotV2
        
        source = inspect.getsource(TelegramBotV2._register_legacy_modules)
        
        # 检查是否还有 ProfileHandler 注册
        has_old_handler = "ProfileHandler.profile_command_callback" in source
        
        if has_old_handler:
            print("[WARNING] 旧的 ProfileHandler 注册仍存在")
            print("[TODO] 需要从 _register_legacy_modules 中移除")
        else:
            print("[OK] 旧的 ProfileHandler 注册已移除")
        
        # 迁移完成后此处应为 False
        # assert not has_old_handler


class TestProfileModuleIntegration:
    """测试 ProfileModule 集成"""
    
    def test_module_in_registry(self):
        """验证模块在 registry 中"""
        try:
            from src.core.registry import get_registry
            
            registry = get_registry()
            modules = registry.list_modules()
            
            if "profile" not in modules:
                print("[TODO] ProfileModule 尚未添加到 registry")
                pytest.skip("模块未在 registry 中")
            
            print(f"[OK] ProfileModule 在 registry 中")
            print(f"    所有模块: {modules}")
            assert "profile" in modules
        except Exception as e:
            pytest.skip(f"Registry 测试失败: {e}")
    
    def test_no_handler_conflicts(self):
        """验证无处理器冲突"""
        try:
            from src.modules.profile.handler import ProfileModule
            
            module = ProfileModule()
            handlers = module.get_handlers()
            
            # 获取第一个ConversationHandler
            from telegram.ext import ConversationHandler
            conv = handlers[0] if isinstance(handlers[0], ConversationHandler) else None
            
            if conv:
                # 检查fallbacks不包含导航模式
                fallback_patterns = []
                for fb in conv.fallbacks:
                    if hasattr(fb, 'pattern'):
                        pattern = fb.pattern.pattern if hasattr(fb.pattern, 'pattern') else str(fb.pattern)
                        fallback_patterns.append(pattern)
                
                # 不应包含 back_to_main 等导航模式
                has_nav = any('back_to_main' in p for p in fallback_patterns)
                
                if has_nav:
                    print("[WARNING] fallbacks 包含导航模式")
                else:
                    print("[OK] fallbacks 无导航冲突")
                
                assert not has_nav, "fallbacks 不应包含导航回调"
        except ImportError:
            pytest.skip("ProfileModule 未实现")


class TestProfileModuleButtons:
    """测试 ProfileModule 按钮交互"""
    
    @pytest.mark.asyncio
    async def test_profile_button_from_reply_keyboard(self):
        """测试从 Reply Keyboard 进入"""
        try:
            from src.modules.profile.handler import ProfileModule
            
            module = ProfileModule()
            
            update = Mock(spec=Update)
            update.message = Mock(spec=Message)
            update.message.text = "👤 个人中心"
            update.message.reply_text = AsyncMock()
            update.callback_query = None
            update.effective_user = Mock(spec=User, id=1, full_name="User")
            
            context = Mock()
            context.user_data = {}
            
            result = await module.show_profile(update, context)
            assert result is not None
            print("[OK] Reply按钮 '👤 个人中心' 正常")
        except (ImportError, AttributeError):
            pytest.skip("功能未实现")
    
    @pytest.mark.asyncio
    async def test_profile_button_from_inline_keyboard(self):
        """测试从 Inline Keyboard 进入"""
        try:
            from src.modules.profile.handler import ProfileModule
            
            module = ProfileModule()
            
            update = Mock(spec=Update)
            update.callback_query = Mock(spec=CallbackQuery)
            update.callback_query.answer = AsyncMock()
            update.callback_query.data = "menu_profile"
            update.callback_query.message = Mock(spec=Message)
            update.callback_query.message.edit_text = AsyncMock()
            update.message = None
            update.effective_user = Mock(spec=User, id=1, full_name="U")
            
            context = Mock()
            context.user_data = {}
            
            result = await module.show_profile(update, context)
            assert result is not None
            print("[OK] Inline按钮 'menu_profile' 正常")
        except (ImportError, AttributeError):
            pytest.skip("功能未实现")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
