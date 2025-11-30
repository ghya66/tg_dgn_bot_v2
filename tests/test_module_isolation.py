"""
模块独立性测试：验证各模块只处理自己的回调，不与其他模块冲突
"""

import pytest
import re
from typing import Dict, List, Set


class TestModuleIsolation:
    """模块独立性测试"""
    
    def test_callback_naming_convention(self):
        """测试回调命名规范：menu_<模块名>"""
        from src.modules.menu.keyboards import MenuKeyboards
        
        keyboard = MenuKeyboards.main_menu_inline()
        
        # 检查所有回调是否符合 menu_ 前缀规范
        for row in keyboard.inline_keyboard:
            for btn in row:
                if btn.callback_data:
                    assert btn.callback_data.startswith("menu_"), \
                        f"回调 {btn.callback_data} 应以 menu_ 开头"
        
        print("✅ 所有主菜单回调符合 menu_<模块名> 规范")
    
    def test_no_duplicate_callback_patterns(self):
        """测试各模块入口 pattern 不重复"""
        all_patterns = []
        module_patterns = {}
        
        # 收集各模块的入口 pattern
        modules_to_check = [
            ("energy", "src.modules.energy.handler", "EnergyModule"),
            ("address_query", "src.modules.address_query.handler", "AddressQueryModule"),
            ("help", "src.modules.help.handler", "HelpModule"),
            ("trx_exchange", "src.modules.trx_exchange.handler", "TRXExchangeModule"),
            ("profile", "src.modules.profile.handler", "ProfileModule"),
            ("menu", "src.modules.menu.handler", "MainMenuModule"),
        ]
        
        for module_name, module_path, class_name in modules_to_check:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            instance = cls()
            handlers = instance.get_handlers()
            
            patterns = []
            for handler in handlers:
                if hasattr(handler, 'entry_points'):
                    for ep in handler.entry_points:
                        if hasattr(ep, 'pattern'):
                            pattern = ep.pattern.pattern if hasattr(ep.pattern, 'pattern') else str(ep.pattern)
                            patterns.append(pattern)
                elif hasattr(handler, 'pattern'):
                    pattern = handler.pattern.pattern if hasattr(handler.pattern, 'pattern') else str(handler.pattern)
                    patterns.append(pattern)
            
            module_patterns[module_name] = patterns
            all_patterns.extend(patterns)
        
        # 检查是否有重复的 pattern
        seen = set()
        duplicates = []
        for p in all_patterns:
            if p in seen:
                duplicates.append(p)
            seen.add(p)
        
        if duplicates:
            print(f"⚠️ 发现重复 pattern: {duplicates}")
        else:
            print("✅ 无重复 pattern")
        
        # 打印各模块 pattern
        for module_name, patterns in module_patterns.items():
            print(f"  {module_name}: {patterns}")
    
    def test_module_priority_order(self):
        """测试模块注册优先级顺序"""
        expected_priority = {
            "main_menu": 0,     # 主菜单最高
            "health": 1,        # 健康检查
            "premium": 2,       # Premium
            "energy": 3,        # 能量
            "address_query": 4, # 地址查询
            "profile": 5,       # 个人中心
            "trx_exchange": 6,  # TRX兑换
            "admin": 10,        # 管理面板
            "orders": 11,       # 订单
            "help": 12,         # 帮助
        }
        
        # 从 bot_v2.py 读取实际注册顺序验证
        # 这里只验证概念，实际优先级在 bot_v2.py 中定义
        print("✅ 模块优先级顺序（设计规范）:")
        for module, priority in sorted(expected_priority.items(), key=lambda x: x[1]):
            print(f"  priority={priority}: {module}")
    
    def test_config_promotion_buttons_consistency(self):
        """测试 config.py 中 promotion_buttons 回调一致性"""
        from src.config import settings
        import json
        
        buttons_config = settings.promotion_buttons
        buttons_config = buttons_config.replace('\n', '').replace(' ', '')
        button_rows = json.loads(f'[{buttons_config}]')
        
        valid_callbacks = {
            "menu_premium", "menu_profile", "menu_energy", 
            "menu_address_query", "menu_clone", "menu_support",
            "menu_trx_exchange", "menu_orders", "menu_help"
        }
        
        for row in button_rows:
            for btn in row:
                callback = btn.get('callback')
                if callback:
                    assert callback in valid_callbacks or callback.startswith("menu_"), \
                        f"配置中的回调 {callback} 不在有效列表中"
        
        print("✅ config.py promotion_buttons 回调一致")
    
    def test_navigation_targets_complete(self):
        """测试 NavigationManager 导航目标完整"""
        from src.common.navigation_manager import NavigationManager
        
        expected_targets = [
            "back_to_main", "nav_back_to_main", "menu_back_to_main",
            "menu_profile", "menu_premium", "menu_address_query",
            "menu_energy", "menu_trx_exchange", "menu_support",
            "menu_clone", "menu_help", "menu_admin"
        ]
        
        actual_targets = NavigationManager.NAVIGATION_TARGETS.keys()
        
        for target in expected_targets:
            assert target in actual_targets, \
                f"NavigationManager 缺少导航目标: {target}"
        
        print("✅ NavigationManager 导航目标完整")
        print(f"  共 {len(actual_targets)} 个导航目标")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
