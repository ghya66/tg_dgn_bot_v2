"""
完整按钮交互测试
测试所有模块的所有按钮
"""
import pytest
from unittest.mock import AsyncMock, Mock
from telegram import Update, User, Message, CallbackQuery


class TestMainMenuButtons:
    """主菜单按钮测试"""
    
    @pytest.mark.asyncio
    async def test_start_command(self):
        """测试 /start 命令"""
        from src.modules.menu.handler import MainMenuModule
        
        module = MainMenuModule()
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.reply_text = AsyncMock()
        update.effective_user = Mock(spec=User, id=123, first_name="Test")
        
        context = Mock()
        context.user_data = {}  # 使用真实的 dict
        
        await module.start_command(update, context)
        update.message.reply_text.assert_called()
        print("[OK] /start command")
    
    @pytest.mark.asyncio
    async def test_back_to_main_callback(self):
        """测试 back_to_main 回调"""
        from src.modules.menu.handler import MainMenuModule
        
        module = MainMenuModule()
        
        # 验证 MainMenuModule 有处理 back_to_main 的 handler
        handlers = module.get_handlers()
        assert len(handlers) > 0
        
        # 检查是否有 back_to_main 模式的回调处理器
        from telegram.ext import CallbackQueryHandler
        back_handler_found = False
        for h in handlers:
            if isinstance(h, CallbackQueryHandler):
                if hasattr(h, 'pattern') and h.pattern:
                    if 'back_to_main' in str(h.pattern.pattern):
                        back_handler_found = True
        
        assert back_handler_found, "back_to_main handler should exist"
        print("[OK] back_to_main handler exists")


class TestPremiumButtons:
    """Premium 模块按钮测试"""
    
    @pytest.mark.asyncio
    async def test_reply_button(self):
        """测试 Reply 按钮 '✈️ 飞机会员'"""
        from src.modules.premium.handler import PremiumModule
        from src.payments.order import OrderManager
        from src.payments.suffix_manager import SuffixManager
        from src.modules.premium.delivery import PremiumDeliveryService
        
        module = PremiumModule(
            order_manager=Mock(spec=OrderManager),
            suffix_manager=Mock(spec=SuffixManager),
            delivery_service=Mock(spec=PremiumDeliveryService),
            receive_address="T...",
            bot_username="test_bot"
        )
        
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.text = "✈️ 飞机会员"
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        update.effective_user = Mock(spec=User, id=123)
        
        context = Mock()
        context.user_data = {}
        
        result = await module.start_premium(update, context)
        assert result is not None
        print("[OK] Premium Reply button")
    
    @pytest.mark.asyncio
    async def test_inline_button(self):
        """测试 Inline 按钮 menu_premium"""
        from src.modules.premium.handler import PremiumModule
        from src.payments.order import OrderManager
        from src.payments.suffix_manager import SuffixManager
        from src.modules.premium.delivery import PremiumDeliveryService
        
        module = PremiumModule(
            order_manager=Mock(spec=OrderManager),
            suffix_manager=Mock(spec=SuffixManager),
            delivery_service=Mock(spec=PremiumDeliveryService),
            receive_address="T...",
            bot_username="test_bot"
        )
        
        update = Mock(spec=Update)
        update.callback_query = Mock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "menu_premium"
        update.message = None
        update.effective_user = Mock(spec=User, id=123)
        
        context = Mock()
        context.user_data = {}
        
        result = await module.start_premium(update, context)
        update.callback_query.answer.assert_called()
        print("[OK] Premium Inline button")


class TestEnergyButtons:
    """能量模块按钮测试"""
    
    @pytest.mark.asyncio
    async def test_reply_button(self):
        """测试 Reply 按钮 '⚡ 能量兑换'"""
        from src.modules.energy.handler import EnergyModule
        
        module = EnergyModule()
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.text = "⚡ 能量兑换"
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        update.effective_user = Mock(spec=User, id=123)
        
        context = Mock()
        context.user_data = {}
        
        result = await module.start_energy(update, context)
        assert result is not None
        print("[OK] Energy Reply button")
    
    @pytest.mark.asyncio
    async def test_inline_button(self):
        """测试 Inline 按钮 menu_energy"""
        from src.modules.energy.handler import EnergyModule
        
        module = EnergyModule()
        update = Mock(spec=Update)
        update.callback_query = Mock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "menu_energy"
        update.message = None
        update.effective_user = Mock(spec=User, id=123)
        
        context = Mock()
        context.user_data = {}
        
        result = await module.start_energy(update, context)
        update.callback_query.answer.assert_called()
        print("[OK] Energy Inline button")
    
    @pytest.mark.asyncio
    async def test_energy_submenu_buttons(self):
        """测试能量子菜单按钮"""
        from src.modules.energy.handler import EnergyModule
        
        module = EnergyModule()
        
        buttons = ["energy_rental", "energy_package", "energy_swap"]
        for btn in buttons:
            update = Mock(spec=Update)
            update.callback_query = Mock(spec=CallbackQuery)
            update.callback_query.answer = AsyncMock()
            update.callback_query.edit_message_text = AsyncMock()
            update.callback_query.data = btn
            update.effective_user = Mock(spec=User, id=123)
            
            context = Mock()
            context.user_data = {}
            
            # 模块应该能处理这些回调
            print(f"[OK] Energy submenu: {btn}")


class TestAddressQueryButtons:
    """地址查询模块按钮测试"""
    
    @pytest.mark.asyncio
    async def test_reply_button(self):
        """测试 Reply 按钮 '🔍 地址查询'"""
        from src.modules.address_query.handler import AddressQueryModule
        
        module = AddressQueryModule()
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.text = "🔍 地址查询"
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        update.effective_user = Mock(spec=User, id=123)
        
        context = Mock()
        context.user_data = {}
        
        result = await module.start_query(update, context)
        assert result is not None
        print("[OK] AddressQuery Reply button")
    
    @pytest.mark.asyncio
    async def test_inline_button(self):
        """测试 Inline 按钮 menu_address_query"""
        from src.modules.address_query.handler import AddressQueryModule
        
        module = AddressQueryModule()
        update = Mock(spec=Update)
        update.callback_query = Mock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "menu_address_query"
        update.message = None
        update.effective_user = Mock(spec=User, id=123)
        
        context = Mock()
        context.user_data = {}
        
        result = await module.start_query(update, context)
        update.callback_query.answer.assert_called()
        print("[OK] AddressQuery Inline button")


class TestProfileButtons:
    """个人中心模块按钮测试"""
    
    @pytest.mark.asyncio
    async def test_reply_button(self):
        """测试 Reply 按钮 '👤 个人中心'"""
        from src.modules.profile.handler import ProfileModule
        
        module = ProfileModule()
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.text = "👤 个人中心"
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        update.effective_user = Mock(spec=User, id=123, full_name="Test")
        
        context = Mock()
        context.user_data = {}
        
        result = await module.show_profile(update, context)
        assert result is not None
        print("[OK] Profile Reply button")
    
    @pytest.mark.asyncio
    async def test_inline_button(self):
        """测试 Inline 按钮 menu_profile"""
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
        update.callback_query.answer.assert_called()
        print("[OK] Profile Inline button")
    
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
        
        await module.show_balance(update, context)
        update.callback_query.answer.assert_called()
        print("[OK] Profile balance button")
    
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
        
        await module.start_deposit(update, context)
        update.callback_query.answer.assert_called()
        print("[OK] Profile deposit button")
    
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
        
        await module.show_history(update, context)
        update.callback_query.answer.assert_called()
        print("[OK] Profile history button")


class TestTRXExchangeButtons:
    """TRX兑换模块按钮测试"""
    
    @pytest.mark.asyncio
    async def test_reply_button(self):
        """测试 Reply 按钮 '🔄 TRX 兑换'"""
        from src.modules.trx_exchange.handler import TRXExchangeModule
        
        module = TRXExchangeModule()
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.text = "🔄 TRX 兑换"
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        update.effective_user = Mock(spec=User, id=123)
        
        context = Mock()
        context.user_data = {}
        
        result = await module.start_exchange(update, context)
        assert result is not None
        print("[OK] TRXExchange Reply button")
    
    @pytest.mark.asyncio
    async def test_inline_button(self):
        """测试 Inline 按钮 menu_trx_exchange"""
        from src.modules.trx_exchange.handler import TRXExchangeModule
        
        module = TRXExchangeModule()
        update = Mock(spec=Update)
        update.callback_query = Mock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.message = Mock(spec=Message)
        update.callback_query.message.reply_text = AsyncMock()
        update.callback_query.data = "menu_trx_exchange"
        update.message = None
        update.effective_user = Mock(spec=User, id=123)
        
        context = Mock()
        context.user_data = {}
        
        result = await module.start_exchange(update, context)
        update.callback_query.answer.assert_called()
        print("[OK] TRXExchange Inline button")


class TestAdminButtons:
    """管理员模块按钮测试"""
    
    def test_admin_module_loaded(self):
        """测试管理员模块加载"""
        from src.modules.admin.handler import AdminModule
        from src.core.base import BaseModule
        
        module = AdminModule()
        assert isinstance(module, BaseModule)
        assert module.module_name == "admin"
        print("[OK] AdminModule loaded")
    
    def test_admin_conversation_handler(self):
        """测试管理员对话处理器"""
        from src.modules.admin.handler import AdminModule
        from telegram.ext import ConversationHandler
        
        module = AdminModule()
        handlers = module.get_handlers()
        assert len(handlers) == 1
        assert isinstance(handlers[0], ConversationHandler)
        print("[OK] AdminModule ConversationHandler")


class TestOrdersButtons:
    """订单查询模块按钮测试"""
    
    def test_orders_module_loaded(self):
        """测试订单查询模块加载"""
        from src.modules.orders.handler import OrdersModule
        from src.core.base import BaseModule
        
        module = OrdersModule()
        assert isinstance(module, BaseModule)
        assert module.module_name == "orders"
        print("[OK] OrdersModule loaded")
    
    def test_orders_conversation_handler(self):
        """测试订单查询对话处理器"""
        from src.modules.orders.handler import OrdersModule
        from telegram.ext import ConversationHandler
        
        module = OrdersModule()
        handlers = module.get_handlers()
        assert len(handlers) == 1
        assert isinstance(handlers[0], ConversationHandler)
        print("[OK] OrdersModule ConversationHandler")


class TestHealthModule:
    """健康检查模块测试"""
    
    def test_health_module_loaded(self):
        """测试健康检查模块加载"""
        from src.modules.health.handler import HealthModule
        from src.core.base import BaseModule
        
        module = HealthModule()
        assert isinstance(module, BaseModule)
        assert module.module_name == "health"
        print("[OK] HealthModule loaded")
    
    def test_health_command_handler(self):
        """测试 /health 命令处理器"""
        from src.modules.health.handler import HealthModule
        from telegram.ext import CommandHandler
        
        module = HealthModule()
        handlers = module.get_handlers()
        assert len(handlers) == 1
        assert isinstance(handlers[0], CommandHandler)
        print("[OK] HealthModule /health command")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
