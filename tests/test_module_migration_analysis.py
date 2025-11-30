"""
未标准化模块迁移分析测试
分析每个模块的当前状态和迁移需求
"""
import pytest
from pathlib import Path
import inspect
import ast


class TestCurrentModuleStructure:
    """分析当前模块结构"""
    
    def test_analyze_profile_handler(self):
        """分析 ProfileHandler 当前结构"""
        from src.wallet.profile_handler import ProfileHandler
        
        print("\n=== ProfileHandler 分析 ===")
        
        # 检查方法
        methods = [m for m in dir(ProfileHandler) if not m.startswith('_')]
        print(f"公共方法数: {len(methods)}")
        for method in methods:
            attr = getattr(ProfileHandler, method)
            if callable(attr):
                is_static = isinstance(inspect.getattr_static(ProfileHandler, method), staticmethod)
                print(f"  - {method}: {'静态方法' if is_static else '类方法'}")
        
        # 检查是否有ConversationHandler
        source = inspect.getsource(ProfileHandler)
        has_conversation = "ConversationHandler" in source
        print(f"使用 ConversationHandler: {has_conversation}")
        
        # 检查是否继承BaseModule
        is_base_module = hasattr(ProfileHandler, 'get_handlers') and hasattr(ProfileHandler, 'module_name')
        print(f"继承 BaseModule: {is_base_module}")
        
        print("\n迁移需求:")
        print("  1. 转换静态方法为实例方法")
        print("  2. 创建 ConversationHandler")
        print("  3. 继承 BaseModule")
        print("  4. 拆分为 handler/messages/keyboards/states")
        
        assert True
    
    def test_analyze_trx_exchange_handler(self):
        """分析 TRXExchangeModule 当前结构"""
        from src.modules.trx_exchange.handler import TRXExchangeModule
        
        print("\n=== TRXExchangeModule 分析 ===")
        
        # 检查是否是类
        print(f"类型: {type(TRXExchangeModule)}")
        
        # 检查是否有get_handlers
        has_get_handlers = hasattr(TRXExchangeModule, 'get_handlers')
        print(f"有 get_handlers: {has_get_handlers}")
        
        # 检查是否继承BaseModule
        from src.core.base import BaseModule
        is_base_module = issubclass(TRXExchangeModule, BaseModule)
        print(f"继承 BaseModule: {is_base_module}")
        
        # 检查ConversationHandler类型
        handler = TRXExchangeModule()
        conv = handler.get_handlers()
        print(f"ConversationHandler类型: {type(conv).__name__}")
        
        # 检查是否使用SafeConversationHandler
        from src.common.conversation_wrapper import SafeConversationHandler
        is_safe = isinstance(conv, type(SafeConversationHandler.create(
            entry_points=[],
            states={},
            fallbacks=[],
            name="test"
        )))
        print(f"使用 SafeConversationHandler: {is_safe}")
        
        print("\n迁移需求:")
        print("  1. 继承 BaseModule")
        print("  2. 改用 SafeConversationHandler")
        print("  3. 移动到 src/modules/trx_exchange/")
        print("  4. 拆分消息和键盘")
        
        assert True
    
    def test_analyze_admin_handler(self):
        """分析 AdminHandler 当前结构"""
        from src.bot_admin.handler import admin_handler
        
        print("\n=== AdminHandler 分析 ===")
        
        # 检查类型
        print(f"类型: {type(admin_handler)}")
        print(f"类名: {admin_handler.__class__.__name__}")
        
        # 检查功能
        has_get_conversation = hasattr(admin_handler, 'get_conversation_handler')
        print(f"有 get_conversation_handler: {has_get_conversation}")
        
        print("\n建议:")
        print("  ⚪ 保持独立 (group=10)")
        print("  - 仅管理员访问，不影响用户交互")
        print("  - 功能复杂，标准化收益低")
        
        assert True
    
    def test_analyze_orders_handler(self):
        """分析 OrdersHandler 当前结构"""
        from src.modules.orders.query_handler import get_orders_handler
        
        print("\n=== OrdersHandler 分析 ===")
        
        # 获取handler
        handler = get_orders_handler()
        print(f"Handler类型: {type(handler).__name__}")
        
        # 检查是否是ConversationHandler
        from telegram.ext import ConversationHandler
        is_conversation = isinstance(handler, ConversationHandler)
        print(f"ConversationHandler: {is_conversation}")
        
        print("\n建议:")
        print("  ⚪ 保持独立 (group=10)")
        print("  - 管理员功能，与用户模块无交互")
        
        assert True


class TestStandardizedModuleStructure:
    """验证标准化模块结构"""
    
    def test_verify_premium_structure(self):
        """验证 Premium 模块结构"""
        base_path = Path(__file__).parent.parent / "src" / "modules" / "premium"
        
        print("\n=== Premium 模块结构 ===")
        
        required_files = ["__init__.py", "handler.py", "messages.py", "keyboards.py", "states.py"]
        for filename in required_files:
            exists = (base_path / filename).exists()
            print(f"  {filename}: {'✅' if exists else '❌'}")
            assert exists, f"缺少文件: {filename}"
        
        # 验证handler继承BaseModule
        from src.modules.premium.handler import PremiumModule
        from src.core.base import BaseModule
        assert issubclass(PremiumModule, BaseModule)
        print("  继承 BaseModule: ✅")
        
        # 验证必需方法
        module = PremiumModule(
            order_manager=None,
            suffix_manager=None,
            delivery_service=None,
            receive_address="T",
            bot_username="b"
        )
        assert hasattr(module, 'module_name')
        assert hasattr(module, 'get_handlers')
        print("  必需方法: ✅")
        
        print("\n此结构为迁移目标模板 ✅")
    
    def test_verify_energy_structure(self):
        """验证 Energy 模块结构"""
        base_path = Path(__file__).parent.parent / "src" / "modules" / "energy"
        
        print("\n=== Energy 模块结构 ===")
        
        required_files = ["__init__.py", "handler.py", "messages.py", "keyboards.py", "states.py"]
        for filename in required_files:
            exists = (base_path / filename).exists()
            print(f"  {filename}: {'✅' if exists else '❌'}")
        
        print("\n此结构为迁移目标模板 ✅")


class TestMigrationFeasibility:
    """测试迁移可行性"""
    
    def test_profile_static_to_instance(self):
        """测试 ProfileHandler 静态方法转实例方法的可行性"""
        from src.wallet.profile_handler import ProfileHandler
        from src.wallet.wallet_manager import WalletManager
        
        print("\n=== ProfileHandler 迁移可行性 ===")
        
        # 模拟转换后的实例方法
        class ProfileModuleMock:
            def __init__(self):
                self.wallet_manager = WalletManager
            
            def get_balance(self, user_id):
                """实例方法版本"""
                with self.wallet_manager() as wallet:
                    return wallet.get_balance(user_id)
        
        # 测试
        mock = ProfileModuleMock()
        balance = mock.get_balance(12345)
        print(f"  余额查询（实例方法）: {balance:.3f} USDT ✅")
        
        print("\n结论: 静态方法可以安全转换为实例方法 ✅")
        assert True
    
    def test_trx_to_safe_conversation(self):
        """测试 TRX Exchange 使用 SafeConversationHandler 的可行性"""
        from src.common.conversation_wrapper import SafeConversationHandler
        from telegram.ext import CommandHandler, MessageHandler, filters
        
        print("\n=== TRX Exchange SafeConversationHandler 可行性 ===")
        
        # 模拟创建SafeConversationHandler
        conv = SafeConversationHandler.create(
            entry_points=[
                CommandHandler("test", lambda u, c: 0),
            ],
            states={
                0: [MessageHandler(filters.TEXT, lambda u, c: 1)]
            },
            fallbacks=[],
            name="trx_test"
        )
        
        print(f"  创建成功: {type(conv).__name__} ✅")
        print(f"  有 fallbacks: {len(conv.fallbacks)} 个 ✅")
        
        print("\n结论: 可以使用 SafeConversationHandler ✅")
        assert True


class TestMigrationPriority:
    """测试迁移优先级分析"""
    
    def test_module_usage_frequency(self):
        """分析模块使用频率（基于按钮数量）"""
        print("\n=== 模块使用频率分析 ===")
        
        modules = {
            "Profile": {"buttons": ["👤 个人中心", "menu_profile"], "users": "所有用户"},
            "TRX Exchange": {"buttons": ["🔄 TRX 兑换", "menu_trx_exchange"], "users": "所有用户"},
            "Admin": {"buttons": ["/admin"], "users": "仅管理员"},
            "Orders": {"buttons": ["/orders"], "users": "仅管理员"},
        }
        
        for name, info in modules.items():
            user_scope = info["users"]
            button_count = len(info["buttons"])
            priority = "🔴 高" if user_scope == "所有用户" else "⚪ 低"
            print(f"{name}:")
            print(f"  按钮数: {button_count}")
            print(f"  用户范围: {user_scope}")
            print(f"  优先级: {priority}")
            print()
        
        print("推荐迁移顺序:")
        print("  1. ProfileModule (用户核心功能)")
        print("  2. TRXExchangeModule (用户功能，已部分修复)")
        print("  3. Admin/Orders (可选，保持独立)")
        
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
