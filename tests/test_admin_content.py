"""
管理面板文案编辑测试脚本

测试：
1. content_service 向后兼容层
2. content_helper 统一缓存机制
3. config_manager 文案保存
"""
import pytest
from unittest.mock import MagicMock, patch


class TestContentService:
    """测试文案服务（向后兼容层）"""

    def test_import(self):
        """测试导入（向后兼容接口）"""
        from src.common.content_service import (
            get_welcome_message,
            get_free_clone_message,
            get_support_contact,
            clear_content_cache,
        )
        assert get_welcome_message is not None
        assert get_free_clone_message is not None
        assert get_support_contact is not None
        assert clear_content_cache is not None

    def test_get_welcome_callable(self):
        """测试欢迎语函数可调用"""
        from src.common.content_service import get_welcome_message

        result = get_welcome_message()
        # 应返回字符串（数据库值或默认值）
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_free_clone_callable(self):
        """测试免费克隆函数可调用"""
        from src.common.content_service import get_free_clone_message

        result = get_free_clone_message()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_support_contact_callable(self):
        """测试客服联系方式函数可调用"""
        from src.common.content_service import get_support_contact

        result = get_support_contact()
        assert isinstance(result, str)
        assert len(result) > 0


class TestContentHelper:
    """测试统一的文案辅助模块"""

    def test_import(self):
        """测试导入"""
        from src.utils.content_helper import get_content, clear_content_cache
        assert get_content is not None
        assert clear_content_cache is not None

    def test_get_content_callable(self):
        """测试 get_content 函数可调用"""
        from src.utils.content_helper import get_content

        # 使用默认值测试
        result = get_content("test_key_not_exist", default="默认值")
        assert result == "默认值"

    def test_cache_clear_callable(self):
        """测试缓存清除函数可调用"""
        from src.utils.content_helper import clear_content_cache

        # 清除指定键（不应报错）
        clear_content_cache("some_key")

        # 清除所有（不应报错）
        clear_content_cache()


class TestConfigManager:
    """测试配置管理器"""
    
    def test_import(self):
        """测试导入"""
        from src.bot_admin.config_manager import config_manager
        assert config_manager is not None
    
    def test_content_config_model(self):
        """测试 ContentConfig 模型"""
        from src.bot_admin.config_manager import ContentConfig
        
        assert hasattr(ContentConfig, 'config_key')
        assert hasattr(ContentConfig, 'config_value')
        assert hasattr(ContentConfig, 'updated_by')


class TestAdminHandler:
    """测试管理员处理器"""
    
    def test_import(self):
        """测试导入"""
        from src.bot_admin.handler import AdminHandler, admin_handler
        assert AdminHandler is not None
        assert admin_handler is not None
    
    def test_handler_methods_exist(self):
        """测试处理方法存在"""
        from src.bot_admin.handler import admin_handler
        
        # 检查文案处理方法
        assert hasattr(admin_handler, 'handle_welcome_input')
        assert hasattr(admin_handler, 'handle_clone_input')
        assert hasattr(admin_handler, 'handle_support_input')
    
    def test_conversation_states(self):
        """测试对话状态定义"""
        from src.bot_admin.handler import (
            EDITING_WELCOME,
            EDITING_CLONE,
            EDITING_SUPPORT,
        )
        
        # 状态值应该是整数
        assert isinstance(EDITING_WELCOME, int)
        assert isinstance(EDITING_CLONE, int)
        assert isinstance(EDITING_SUPPORT, int)
        
        # 状态值应该不同
        states = [EDITING_WELCOME, EDITING_CLONE, EDITING_SUPPORT]
        assert len(states) == len(set(states))


class TestIntegration:
    """集成测试"""
    
    def test_conversation_handler_has_content_states(self):
        """测试 ConversationHandler 包含文案状态"""
        from src.bot_admin.handler import admin_handler, EDITING_WELCOME, EDITING_CLONE, EDITING_SUPPORT
        
        conv_handler = admin_handler.get_conversation_handler()
        
        # 检查 states 包含文案编辑状态
        assert EDITING_WELCOME in conv_handler.states
        assert EDITING_CLONE in conv_handler.states
        assert EDITING_SUPPORT in conv_handler.states
