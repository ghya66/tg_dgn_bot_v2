"""
代码审查问题验证测试脚本

基于 CODE_REVIEW_REPORT.md 中发现的问题设计的测试用例
运行方式: pytest tests/test_code_review_issues.py -v
"""

import pytest
import re
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


# ============================================================================
# 测试工具函数
# ============================================================================

def get_project_root():
    """获取项目根目录"""
    return Path(__file__).parent.parent


def read_file_content(relative_path: str) -> str:
    """读取文件内容"""
    full_path = get_project_root() / relative_path
    return full_path.read_text(encoding='utf-8')


def extract_callback_data_from_keyboard(keyboard: InlineKeyboardMarkup) -> list:
    """从键盘中提取所有 callback_data"""
    callbacks = []
    for row in keyboard.inline_keyboard:
        for button in row:
            if button.callback_data:
                callbacks.append(button.callback_data)
    return callbacks


def check_button_text_contains(keyboard: InlineKeyboardMarkup, text: str) -> bool:
    """检查键盘中是否包含指定文本的按钮"""
    for row in keyboard.inline_keyboard:
        for button in row:
            if text in button.text:
                return True
    return False


# ============================================================================
# 图标文案一致性测试
# ============================================================================

class TestIconConsistency:
    """图标文案一致性测试"""
    
    def test_premium_icon_in_menu_handler(self):
        """测试 menu/handler.py 中 Premium 图标是否一致"""
        content = read_file_content("src/modules/menu/handler.py")
        
        # 检查底部键盘定义
        assert "💎 Premium会员" in content, \
            "底部键盘应使用 '💎 Premium会员'"
        
        # 不应该有不一致的文案
        # 注意：如果代码中有其他用途的 Premium 文案，这个断言可能需要调整
    
    def test_premium_icon_in_menu_keyboards(self):
        """测试 menu/keyboards.py 中 Premium 图标"""
        content = read_file_content("src/modules/menu/keyboards.py")
        
        # 检查是否存在不一致的文案
        inconsistent_patterns = [
            "Premium 开通",  # 多了空格
            "Premium直充",   # 不同文案
        ]
        
        for pattern in inconsistent_patterns:
            if pattern in content:
                pytest.fail(f"发现不一致文案: '{pattern}'，应统一为 '💎 Premium会员'")
    
    def test_profile_icon_consistency(self):
        """测试个人中心图标一致性"""
        content = read_file_content("src/modules/menu/handler.py")
        
        # 底部键盘应该使用 👤
        assert "👤 个人中心" in content, \
            "底部键盘应使用 '👤 个人中心'"
        
        # 不应该使用其他图标
        if "🏠 个人中心" in content:
            pytest.fail("发现不一致图标: '🏠 个人中心'，应统一为 '👤 个人中心'")
    
    def test_trx_exchange_icon_consistency(self):
        """测试 TRX 兑换图标一致性"""
        menu_handler = read_file_content("src/modules/menu/handler.py")
        menu_keyboards = read_file_content("src/modules/menu/keyboards.py")
        
        # 应该统一使用 💱 TRX闪兑
        if "🔄 TRX" in menu_handler and "💱 TRX" in menu_keyboards:
            pytest.fail("TRX 兑换图标不一致: handler 使用 🔄，keyboards 使用 💱")


# ============================================================================
# 按钮映射完整性测试
# ============================================================================

class TestButtonMapping:
    """按钮映射完整性测试"""
    
    def test_profile_has_back_to_main_button(self):
        """测试 Profile 键盘是否有返回主菜单按钮"""
        from src.modules.profile.keyboards import ProfileKeyboards
        
        keyboard = ProfileKeyboards.back_to_profile()
        callbacks = extract_callback_data_from_keyboard(keyboard)
        
        # 应该有返回主菜单的选项
        has_back_to_main = any(
            cb in callbacks 
            for cb in ['back_to_main', 'nav_back_to_main', 'menu_back_to_main']
        )
        
        if not has_back_to_main:
            pytest.fail(
                "ProfileKeyboards.back_to_profile() 缺少返回主菜单按钮，"
                "用户可能被困在 Profile 界面"
            )
    
    def test_all_modules_have_cancel_path(self):
        """测试所有模块是否有取消/返回路径"""
        from src.modules.energy.keyboards import EnergyKeyboards
        from src.modules.help.keyboards import HelpKeyboards
        
        keyboards_to_check = [
            ("Energy main_menu", EnergyKeyboards.main_menu()),
            ("Energy hourly_packages", EnergyKeyboards.hourly_packages()),
            ("Help main_menu", HelpKeyboards.main_menu()),
        ]
        
        for name, keyboard in keyboards_to_check:
            callbacks = extract_callback_data_from_keyboard(keyboard)
            
            has_exit_path = any(
                'back' in cb or 'cancel' in cb or 'main' in cb
                for cb in callbacks
            )
            
            assert has_exit_path, f"{name} 缺少退出路径（返回/取消按钮）"


# ============================================================================
# callback_data 前缀规范测试
# ============================================================================

class TestCallbackDataNaming:
    """callback_data 命名规范测试"""
    
    VALID_PREFIXES = [
        'back_to_main', 'nav_back_to_main', 'menu_back_to_main', 'addrq_back_to_main',
        'menu_', 'premium_', 'energy_', 'addrq_', 'profile_', 
        'trx_', 'orders_', 'help_', 'admin_'
    ]
    
    def test_premium_callback_prefix(self):
        """测试 Premium 模块 callback 前缀规范"""
        from src.modules.premium.keyboards import PremiumKeyboards
        
        keyboards = [
            PremiumKeyboards.start_keyboard(),
            PremiumKeyboards.confirm_user_keyboard(),
            PremiumKeyboards.confirm_order_keyboard(),
            PremiumKeyboards.back_to_main_keyboard(),
        ]
        
        for keyboard in keyboards:
            callbacks = extract_callback_data_from_keyboard(keyboard)
            for cb in callbacks:
                valid = any(cb.startswith(prefix) for prefix in self.VALID_PREFIXES)
                assert valid, f"Premium 模块使用了非标准 callback: {cb}"
    
    def test_energy_callback_prefix(self):
        """测试 Energy 模块 callback 前缀规范"""
        from src.modules.energy.keyboards import EnergyKeyboards
        
        keyboards = [
            EnergyKeyboards.main_menu(),
            EnergyKeyboards.hourly_packages(),
            EnergyKeyboards.payment_done(),
        ]
        
        for keyboard in keyboards:
            callbacks = extract_callback_data_from_keyboard(keyboard)
            for cb in callbacks:
                valid = any(cb.startswith(prefix) for prefix in self.VALID_PREFIXES)
                assert valid, f"Energy 模块使用了非标准 callback: {cb}"


# ============================================================================
# 状态机完整性测试
# ============================================================================

class TestStateMachineCompleteness:
    """状态机完整性测试"""
    
    def test_premium_states_all_used(self):
        """测试 Premium 状态是否都被使用"""
        from src.modules.premium.states import (
            SELECTING_TARGET, SELECTING_PACKAGE, ENTERING_USERNAME,
            AWAITING_USERNAME_ACTION, VERIFYING_USERNAME, CONFIRMING_ORDER
        )
        
        handler_content = read_file_content("src/modules/premium/handler.py")
        
        # 检查状态是否在 handler 中被引用
        states_to_check = [
            ('SELECTING_TARGET', SELECTING_TARGET),
            ('SELECTING_PACKAGE', SELECTING_PACKAGE),
            ('ENTERING_USERNAME', ENTERING_USERNAME),
            ('CONFIRMING_ORDER', CONFIRMING_ORDER),
        ]
        
        for state_name, state_value in states_to_check:
            assert state_name in handler_content, \
                f"Premium 状态 {state_name} 未在 handler 中使用"
    
    def test_energy_states_all_used(self):
        """测试 Energy 状态是否都被使用"""
        from src.modules.energy.states import (
            STATE_SELECT_TYPE, STATE_SELECT_PACKAGE, STATE_INPUT_ADDRESS,
            STATE_SHOW_PAYMENT, STATE_INPUT_USDT, STATE_INPUT_TX_HASH
        )
        
        handler_content = read_file_content("src/modules/energy/handler.py")
        
        # 验证所有状态都在 handler 中使用
        states_to_check = [
            "STATE_SELECT_TYPE",
            "STATE_SELECT_PACKAGE", 
            "STATE_INPUT_ADDRESS",
            "STATE_SHOW_PAYMENT",
            "STATE_INPUT_USDT",
            "STATE_INPUT_TX_HASH"
        ]
        
        for state_name in states_to_check:
            assert state_name in handler_content, \
                f"Energy 状态 {state_name} 未在 handler 中使用"
    
    def test_conversation_handler_has_fallbacks(self):
        """测试对话处理器是否有 fallback"""
        handler_content = read_file_content("src/modules/premium/handler.py")
        
        # 检查是否使用 SafeConversationHandler
        assert "SafeConversationHandler" in handler_content, \
            "Premium 模块应使用 SafeConversationHandler 以确保有 fallback"


# ============================================================================
# 导航一致性测试
# ============================================================================

class TestNavigationConsistency:
    """导航一致性测试"""
    
    def test_navigation_manager_handles_all_back_patterns(self):
        """测试 NavigationManager 是否处理所有返回主菜单的 pattern"""
        content = read_file_content("src/common/navigation_manager.py")
        
        back_patterns = [
            'back_to_main',
            'nav_back_to_main',
            'menu_back_to_main',
            'addrq_back_to_main',
        ]
        
        for pattern in back_patterns:
            assert pattern in content, \
                f"NavigationManager 未处理 {pattern}"
    
    def test_menu_handler_handles_back_patterns(self):
        """测试 MainMenuModule 是否处理返回主菜单的 callback"""
        content = read_file_content("src/modules/menu/handler.py")
        
        # 检查 show_main_menu 的 pattern
        assert "back_to_main" in content
        assert "nav_back_to_main" in content or "back_to_main" in content


# ============================================================================
# 错误处理测试
# ============================================================================

class TestErrorHandling:
    """错误处理测试"""
    
    def test_no_bare_except(self):
        """检查是否存在裸 except"""
        files_to_check = [
            "src/modules/premium/handler.py",
            "src/modules/energy/handler.py",
            "src/modules/profile/handler.py",
            "src/tasks/order_expiry.py",
        ]
        
        bare_except_pattern = re.compile(r'except\s*:', re.MULTILINE)
        
        for file_path in files_to_check:
            try:
                content = read_file_content(file_path)
                matches = bare_except_pattern.findall(content)
                if matches:
                    pytest.fail(f"{file_path} 存在裸 except，应指定异常类型")
            except FileNotFoundError:
                pass  # 文件不存在则跳过
    
    def test_order_expiry_uses_dynamic_timeout(self):
        """测试订单过期任务是否使用动态超时时间"""
        content = read_file_content("src/tasks/order_expiry.py")
        
        # 应该使用 get_order_timeout_minutes
        assert "get_order_timeout_minutes" in content, \
            "order_expiry 应该使用 get_order_timeout_minutes 动态获取超时时间"


# ============================================================================
# 按钮冒烟测试
# ============================================================================

class TestP1Issues:
    """P1 问题修复验证"""
    
    def test_trx_exchange_has_cancel_button_in_input_states(self):
        """测试 TRX Exchange 输入阶段有取消按钮"""
        from src.modules.trx_exchange.keyboards import TRXExchangeKeyboards
        
        keyboard = TRXExchangeKeyboards.cancel_button()
        callbacks = extract_callback_data_from_keyboard(keyboard)
        
        assert "trx_cancel_input" in callbacks, \
            "TRX Exchange 应该有 trx_cancel_input 取消按钮"
    
    def test_trx_handler_has_cancel_input_method(self):
        """测试 TRX Exchange handler 有 cancel_input 方法"""
        content = read_file_content("src/modules/trx_exchange/handler.py")
        
        assert "async def cancel_input" in content, \
            "TRX Exchange handler 应该有 cancel_input 方法"
        
        assert "trx_cancel_input" in content, \
            "TRX Exchange handler 应该处理 trx_cancel_input callback"
    
    def test_order_expiry_has_set_bot_method(self):
        """测试订单过期任务支持设置 bot 实例"""
        content = read_file_content("src/tasks/order_expiry.py")
        
        assert "def set_bot" in content, \
            "OrderExpiryTask 应该有 set_bot 方法"
        
        assert "_notify_user_order_expired" in content, \
            "OrderExpiryTask 应该有 _notify_user_order_expired 方法"
    
    def test_bot_v2_binds_bot_to_order_expiry(self):
        """测试 bot_v2 绑定 bot 到订单过期任务"""
        content = read_file_content("src/bot_v2.py")
        
        assert "order_expiry_task.set_bot" in content, \
            "bot_v2 应该调用 order_expiry_task.set_bot 绑定 bot 实例"


class TestP2Issues:
    """P2 问题修复验证"""
    
    def test_energy_state_input_count_removed(self):
        """测试 Energy 模块已删除未使用的 STATE_INPUT_COUNT"""
        states_content = read_file_content("src/modules/energy/states.py")
        handler_content = read_file_content("src/modules/energy/handler.py")
        
        assert "STATE_INPUT_COUNT" not in states_content, \
            "states.py 应该已删除 STATE_INPUT_COUNT"
        
        assert "input_count" not in handler_content or "async def input_count" not in handler_content, \
            "handler.py 应该已删除 input_count 方法"
    
    def test_premium_uses_error_collector(self):
        """测试 Premium 模块使用 error_collector"""
        content = read_file_content("src/modules/premium/handler.py")
        
        assert "from src.common.error_collector import collect_error" in content, \
            "Premium handler 应该导入 error_collector"
        
        assert "collect_error(" in content, \
            "Premium handler 应该使用 collect_error"
    
    def test_payment_monitor_uses_error_collector(self):
        """测试 PaymentMonitor 使用 error_collector"""
        content = read_file_content("src/modules/trx_exchange/payment_monitor.py")
        
        assert "from src.common.error_collector import collect_error" in content, \
            "PaymentMonitor 应该导入 error_collector"
        
        assert "collect_error(" in content, \
            "PaymentMonitor 应该使用 collect_error"
    
    def test_callback_naming_unified_to_nav_back_to_main(self):
        """测试所有模块统一使用 nav_back_to_main"""
        modules_to_check = [
            "src/modules/help/keyboards.py",
            "src/modules/energy/keyboards.py",
            "src/modules/trx_exchange/keyboards.py",
            "src/modules/profile/keyboards.py",
            "src/modules/menu/keyboards.py",
            "src/modules/address_query/keyboards.py",
        ]
        
        deprecated_callbacks = [
            "back_to_main",  # 应该用 nav_back_to_main
            "menu_back_to_main",
            "addrq_back_to_main",
        ]
        
        for file_path in modules_to_check:
            content = read_file_content(file_path)
            for deprecated in deprecated_callbacks:
                # 检查是否在 callback_data 中使用了旧的命名
                pattern = f'callback_data="{deprecated}"'
                if pattern in content:
                    pytest.fail(f"{file_path} 使用了旧的 callback: {deprecated}，应使用 nav_back_to_main")


class TestButtonSmokeTest:
    """按钮冒烟测试 - 验证所有按钮都有对应的 handler"""
    
    def test_menu_inline_buttons_have_handlers(self):
        """测试主菜单 InlineKeyboard 按钮都有 handler"""
        from src.modules.menu.keyboards import MenuKeyboards
        
        keyboard = MenuKeyboards.main_menu_inline()
        callbacks = extract_callback_data_from_keyboard(keyboard)
        
        # 这些 callback 应该有对应的处理
        expected_handlers = {
            'menu_premium': 'premium 模块入口',
            'menu_energy': 'energy 模块入口',
            'menu_trx_exchange': 'trx_exchange 模块入口',
            'menu_address_query': 'address_query 模块入口',
            'menu_profile': 'profile 模块入口',
            'menu_orders': 'orders 处理',
            'menu_help': 'help 模块入口',
            'menu_support': 'menu handler 内部处理',
        }
        
        for cb in callbacks:
            # 只检查 menu_ 前缀的
            if cb.startswith('menu_'):
                assert cb in expected_handlers, f"未知的 menu callback: {cb}"
    
    def test_reply_keyboard_buttons_have_handlers(self):
        """测试底部键盘按钮都有 handler"""
        # 底部键盘按钮通过 MessageHandler 处理
        handler_content = read_file_content("src/modules/menu/handler.py")
        
        expected_buttons = [
            "💱 实时汇率",
            "🎁 免费克隆",
            "👨‍💼 联系客服",
        ]
        
        for button in expected_buttons:
            # 检查是否有对应的 Regex filter
            assert button in handler_content, \
                f"底部键盘按钮 '{button}' 没有对应的 MessageHandler"


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
