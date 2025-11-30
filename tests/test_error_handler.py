"""
全局错误处理器测试
"""

import pytest


class TestGlobalErrorHandler:
    """全局错误处理器测试"""
    
    def test_bot_has_error_handler_method(self):
        """测试 Bot 类有全局错误处理方法"""
        from src.bot_v2 import TelegramBotV2
        
        bot = TelegramBotV2()
        
        # 检查错误处理方法存在
        assert hasattr(bot, '_global_error_handler'), "TelegramBotV2 应有 _global_error_handler 方法"
        assert callable(bot._global_error_handler), "_global_error_handler 应是可调用的"
        
        print("✅ TelegramBotV2 有全局错误处理方法")
    
    def test_bootstrap_registers_error_handler(self):
        """测试 _bootstrap_application 注册错误处理器"""
        import inspect
        from src.bot_v2 import TelegramBotV2
        
        # 检查 _bootstrap_application 方法源码中包含 add_error_handler
        source = inspect.getsource(TelegramBotV2._bootstrap_application)
        
        assert "add_error_handler" in source, "_bootstrap_application 应调用 add_error_handler"
        assert "_global_error_handler" in source, "_bootstrap_application 应注册 _global_error_handler"
        
        print("✅ _bootstrap_application 注册全局错误处理器")
    
    def test_error_handler_logs_error(self):
        """测试错误处理器记录日志"""
        import inspect
        from src.bot_v2 import TelegramBotV2
        
        source = inspect.getsource(TelegramBotV2._global_error_handler)
        
        assert "logger.error" in source, "错误处理器应记录错误日志"
        assert "context.error" in source, "错误处理器应记录 context.error"
        
        print("✅ 错误处理器包含日志记录")
    
    def test_error_handler_notifies_user(self):
        """测试错误处理器通知用户"""
        import inspect
        from src.bot_v2 import TelegramBotV2
        
        source = inspect.getsource(TelegramBotV2._global_error_handler)
        
        assert "send_message" in source, "错误处理器应尝试发送消息给用户"
        assert "发生错误" in source, "错误消息应包含友好提示"
        
        print("✅ 错误处理器包含用户通知逻辑")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
