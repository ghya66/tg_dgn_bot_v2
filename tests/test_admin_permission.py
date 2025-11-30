"""
管理员权限控制测试
"""

import pytest
import inspect


class TestAdminPermission:
    """管理员权限控制测试"""
    
    def test_owner_only_decorator_exists(self):
        """测试 owner_only 装饰器存在"""
        from src.bot_admin.middleware import owner_only
        
        assert callable(owner_only), "owner_only 应是可调用的装饰器"
        print("✅ owner_only 装饰器存在")
    
    def test_owner_only_checks_user_id(self):
        """测试 owner_only 检查用户 ID"""
        from src.bot_admin.middleware import owner_only
        
        source = inspect.getsource(owner_only)
        
        assert "user_id" in source, "应检查 user_id"
        assert "owner_id" in source or "bot_owner_id" in source, "应检查 owner_id"
        assert "user_id != owner_id" in source, "应比较用户ID与管理员ID"
        
        print("✅ owner_only 装饰器检查用户 ID")
    
    def test_owner_only_logs_unauthorized(self):
        """测试 owner_only 记录未授权访问"""
        from src.bot_admin.middleware import owner_only
        
        source = inspect.getsource(owner_only)
        
        assert "logger.warning" in source or "logger.info" in source, "应记录访问日志"
        assert "Unauthorized" in source or "权限" in source, "应记录未授权访问"
        
        print("✅ owner_only 装饰器记录未授权访问日志")
    
    def test_owner_only_returns_error_message(self):
        """测试 owner_only 返回错误消息"""
        from src.bot_admin.middleware import owner_only
        
        source = inspect.getsource(owner_only)
        
        assert "reply_text" in source, "应发送回复消息"
        assert "权限不足" in source or "Unauthorized" in source, "应包含权限不足提示"
        
        print("✅ owner_only 装饰器返回友好错误消息")
    
    def test_admin_handler_uses_owner_only(self):
        """测试管理处理器使用 owner_only 装饰器"""
        from src.bot_admin.handler import AdminHandler
        
        source = inspect.getsource(AdminHandler.admin_command)
        
        # 检查方法定义是否有装饰器（通过类源码检查）
        class_source = inspect.getsource(AdminHandler)
        
        assert "@owner_only" in class_source, "AdminHandler.admin_command 应使用 @owner_only"
        
        print("✅ AdminHandler.admin_command 使用 @owner_only 装饰器")
    
    def test_is_owner_helper_function(self):
        """测试 is_owner 辅助函数"""
        from src.bot_admin.middleware import is_owner
        
        assert callable(is_owner), "is_owner 应是可调用函数"
        
        # 测试返回 bool
        result = is_owner(12345)
        assert isinstance(result, bool), "is_owner 应返回 bool"
        
        print("✅ is_owner 辅助函数正常工作")
    
    def test_get_owner_id_function(self):
        """测试 get_owner_id 函数"""
        from src.bot_admin.middleware import get_owner_id
        
        owner_id = get_owner_id()
        assert isinstance(owner_id, int), "get_owner_id 应返回 int"
        
        print(f"✅ get_owner_id 返回: {owner_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
