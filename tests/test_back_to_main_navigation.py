"""
返回主菜单导航测试：验证所有返回主菜单的回调都能正确处理
"""

import pytest
import re


class TestBackToMainNavigation:
    """返回主菜单导航测试"""
    
    def test_main_menu_handles_all_back_callbacks(self):
        """测试主菜单模块处理所有返回回调"""
        from src.modules.menu.handler import MainMenuModule
        
        module = MainMenuModule()
        handlers = module.get_handlers()
        
        # 查找处理 back_to_main 的 handler
        back_handler = None
        for h in handlers:
            if hasattr(h, 'pattern'):
                pattern = h.pattern.pattern if hasattr(h.pattern, 'pattern') else str(h.pattern)
                if 'back_to_main' in pattern:
                    back_handler = h
                    break
        
        assert back_handler is not None, "应有处理 back_to_main 的 handler"
        
        # 检查支持的回调
        pattern = back_handler.pattern.pattern if hasattr(back_handler.pattern, 'pattern') else str(back_handler.pattern)
        
        expected_callbacks = [
            "back_to_main",
            "nav_back_to_main", 
            "menu_back_to_main",
            "addrq_back_to_main"
        ]
        
        for callback in expected_callbacks:
            assert re.match(pattern, callback), \
                f"主菜单应处理 {callback} 回调"
        
        print(f"✅ 主菜单处理以下返回回调: {expected_callbacks}")
    
    def test_energy_has_back_button(self):
        """测试能量模块有返回主菜单按钮"""
        from src.modules.energy.keyboards import EnergyKeyboards
        
        keyboard = EnergyKeyboards.main_menu()
        
        has_back = False
        for row in keyboard.inline_keyboard:
            for btn in row:
                if btn.callback_data and 'back_to_main' in btn.callback_data:
                    has_back = True
                    break
        
        assert has_back, "能量类型选择键盘应有返回主菜单按钮"
        print("✅ 能量模块有返回主菜单按钮")
    
    def test_address_query_has_back_button(self):
        """测试地址查询模块有返回主菜单按钮"""
        from src.modules.address_query.keyboards import AddressQueryKeyboards
        
        keyboard = AddressQueryKeyboards.back_to_main_keyboard()
        
        has_back = False
        for row in keyboard.inline_keyboard:
            for btn in row:
                if btn.callback_data and 'back_to_main' in btn.callback_data:
                    has_back = True
                    break
        
        assert has_back, "地址查询键盘应有返回主菜单按钮"
        print("✅ 地址查询模块有返回主菜单按钮")
    
    def test_help_has_back_button(self):
        """测试帮助模块有返回主菜单按钮"""
        from src.modules.help.keyboards import HelpKeyboards
        
        keyboard = HelpKeyboards.main_menu()
        
        has_back = False
        for row in keyboard.inline_keyboard:
            for btn in row:
                if btn.callback_data and 'back_to_main' in btn.callback_data:
                    has_back = True
                    break
        
        assert has_back, "帮助键盘应有返回主菜单按钮"
        print("✅ 帮助模块有返回主菜单按钮")
    
    def test_premium_has_back_button(self):
        """测试 Premium 模块有返回主菜单按钮"""
        from src.modules.premium.keyboards import PremiumKeyboards
        
        keyboard = PremiumKeyboards.back_to_main_keyboard()
        
        has_back = False
        for row in keyboard.inline_keyboard:
            for btn in row:
                if btn.callback_data and 'back_to_main' in btn.callback_data:
                    has_back = True
                    break
        
        assert has_back, "Premium 键盘应有返回主菜单按钮"
        print("✅ Premium 模块有返回主菜单按钮")
    
    def test_trx_exchange_has_back_button(self):
        """测试 TRX 兑换模块有返回主菜单按钮"""
        from src.modules.trx_exchange.keyboards import TRXExchangeKeyboards
        
        keyboard = TRXExchangeKeyboards.back_to_main()
        
        has_back = False
        for row in keyboard.inline_keyboard:
            for btn in row:
                if btn.callback_data and 'back_to_main' in btn.callback_data:
                    has_back = True
                    break
        
        assert has_back, "TRX 兑换键盘应有返回主菜单按钮"
        print("✅ TRX 兑换模块有返回主菜单按钮")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
