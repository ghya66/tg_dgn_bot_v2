"""
模块入口完整性测试：验证每个模块同时有命令入口和回调入口
"""

import pytest
import re
from typing import List, Dict, Tuple
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler


class TestModuleEntryCompleteness:
    """模块入口完整性测试"""
    
    def _extract_entry_points(self, handlers) -> Dict[str, List[str]]:
        """提取所有入口点类型"""
        result = {
            "commands": [],
            "callbacks": [],
            "messages": []
        }
        
        for handler in handlers:
            if hasattr(handler, 'entry_points'):
                for ep in handler.entry_points:
                    if isinstance(ep, CommandHandler):
                        for cmd in ep.commands:
                            result["commands"].append(cmd)
                    elif isinstance(ep, CallbackQueryHandler):
                        pattern = ep.pattern.pattern if hasattr(ep.pattern, 'pattern') else str(ep.pattern)
                        result["callbacks"].append(pattern)
                    elif isinstance(ep, MessageHandler):
                        result["messages"].append("MessageHandler")
            elif isinstance(handler, CommandHandler):
                for cmd in handler.commands:
                    result["commands"].append(cmd)
            elif isinstance(handler, CallbackQueryHandler):
                pattern = handler.pattern.pattern if hasattr(handler.pattern, 'pattern') else str(handler.pattern)
                result["callbacks"].append(pattern)
        
        return result
    
    def test_energy_module_entries(self):
        """测试能量模块入口完整性"""
        from src.modules.energy.handler import EnergyModule
        
        module = EnergyModule()
        handlers = module.get_handlers()
        entries = self._extract_entry_points(handlers)
        
        assert "energy" in entries["commands"], "能量模块应有 /energy 命令入口"
        assert any("menu_energy" in p for p in entries["callbacks"]), "能量模块应有 menu_energy 回调入口"
        
        print(f"✅ 能量模块入口: commands={entries['commands']}, callbacks={entries['callbacks']}")
    
    def test_address_query_module_entries(self):
        """测试地址查询模块入口完整性"""
        from src.modules.address_query.handler import AddressQueryModule
        
        module = AddressQueryModule()
        handlers = module.get_handlers()
        entries = self._extract_entry_points(handlers)
        
        assert "query" in entries["commands"], "地址查询模块应有 /query 命令入口"
        assert any("menu_address_query" in p for p in entries["callbacks"]), "地址查询模块应有 menu_address_query 回调入口"
        
        print(f"✅ 地址查询模块入口: commands={entries['commands']}, callbacks={entries['callbacks']}")
    
    def test_help_module_entries(self):
        """测试帮助模块入口完整性"""
        from src.modules.help.handler import HelpModule
        
        module = HelpModule()
        handlers = module.get_handlers()
        entries = self._extract_entry_points(handlers)
        
        assert "help" in entries["commands"], "帮助模块应有 /help 命令入口"
        assert any("menu_help" in p for p in entries["callbacks"]), "帮助模块应有 menu_help 回调入口"
        
        print(f"✅ 帮助模块入口: commands={entries['commands']}, callbacks={entries['callbacks']}")
    
    def test_profile_module_entries(self):
        """测试个人中心模块入口完整性"""
        from src.modules.profile.handler import ProfileModule
        
        module = ProfileModule()
        handlers = module.get_handlers()
        entries = self._extract_entry_points(handlers)
        
        assert "profile" in entries["commands"], "个人中心模块应有 /profile 命令入口"
        assert any("menu_profile" in p for p in entries["callbacks"]), "个人中心模块应有 menu_profile 回调入口"
        
        print(f"✅ 个人中心模块入口: commands={entries['commands']}, callbacks={entries['callbacks']}")
    
    def test_trx_exchange_module_entries(self):
        """测试TRX兑换模块入口完整性"""
        from src.modules.trx_exchange.handler import TRXExchangeModule
        
        module = TRXExchangeModule()
        handlers = module.get_handlers()
        entries = self._extract_entry_points(handlers)
        
        # TRX兑换模块可能没有命令入口，只有回调和消息入口
        assert any("menu_trx_exchange" in p for p in entries["callbacks"]), "TRX兑换模块应有 menu_trx_exchange 回调入口"
        
        print(f"✅ TRX兑换模块入口: commands={entries['commands']}, callbacks={entries['callbacks']}")
    
    def test_main_menu_module_entries(self):
        """测试主菜单模块入口完整性"""
        from src.modules.menu.handler import MainMenuModule
        
        module = MainMenuModule()
        handlers = module.get_handlers()
        entries = self._extract_entry_points(handlers)
        
        assert "start" in entries["commands"], "主菜单模块应有 /start 命令入口"
        assert any("back_to_main" in p for p in entries["callbacks"]), "主菜单模块应有 back_to_main 回调入口"
        assert any("menu_support" in p for p in entries["callbacks"]), "主菜单模块应有 menu_support 回调入口"
        assert any("menu_orders" in p for p in entries["callbacks"]), "主菜单模块应有 menu_orders 回调入口"
        
        print(f"✅ 主菜单模块入口: commands={entries['commands']}, callbacks={entries['callbacks']}")
    
    def test_all_modules_summary(self):
        """汇总所有模块入口"""
        modules_config = [
            ("energy", "src.modules.energy.handler", "EnergyModule"),
            ("address_query", "src.modules.address_query.handler", "AddressQueryModule"),
            ("help", "src.modules.help.handler", "HelpModule"),
            ("profile", "src.modules.profile.handler", "ProfileModule"),
            ("trx_exchange", "src.modules.trx_exchange.handler", "TRXExchangeModule"),
            ("menu", "src.modules.menu.handler", "MainMenuModule"),
        ]
        
        print("\n" + "="*60)
        print("📊 模块入口完整性汇总")
        print("="*60)
        
        for module_name, module_path, class_name in modules_config:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            instance = cls()
            handlers = instance.get_handlers()
            entries = self._extract_entry_points(handlers)
            
            cmd_status = "✅" if entries["commands"] else "⚠️"
            cb_status = "✅" if entries["callbacks"] else "⚠️"
            
            print(f"{module_name:15} | 命令{cmd_status} {entries['commands']} | 回调{cb_status} {len(entries['callbacks'])}个")
        
        print("="*60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
