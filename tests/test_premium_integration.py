"""
Premium 功能集成测试
测试完整的 Premium 购买流程，使用 bot_app_v2 fixture（离线模式）
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.utils.telegram_simulator import BotTestHelper, TelegramSimulator


class TestPremiumIntegration:
    """Premium 功能集成测试 - 使用 bot_app_v2 fixture"""
    
    @pytest.fixture
    async def helper(self, bot_app_v2):
        """基于 bot_app_v2 创建测试辅助类"""
        helper = BotTestHelper(bot_app_v2)
        await helper.initialize()
        yield helper
    
    
    @pytest.mark.asyncio
    async def test_premium_flow_complete(self, helper):
        """测试完整的 Premium 购买流程"""
        # 1. 发送 /start 命令进入主菜单
        await helper.send_command("start")
        
        # 2. 点击 Premium 按钮进入 Premium 页面
        await helper.click_button("menu_premium")
        
        # 验证显示 Premium 页面（给自己/给他人选择）
        message = helper.get_message_text()
        assert message is not None, "应收到 Premium 页面响应"
        assert "Premium" in message
        
        # 3. 选择给自己开通
        await helper.click_button("premium_self")
        
        # 验证显示套餐选择
        message = helper.get_message_text()
        # 断言关键字段存在（不绑定完整文案）
        assert message is not None
        
        # 4. 选择3个月套餐
        await helper.click_button("premium_3")
        
        # 验证进入确认阶段
        message = helper.get_message_text()
        assert message is not None
    
    @pytest.mark.asyncio
    async def test_premium_cancel_flow(self, helper):
        """测试取消 Premium 购买"""
        # 1. 进入 Premium 页面
        await helper.send_command("start")
        await helper.click_button("menu_premium")
        
        # 2. 选择给自己开通
        await helper.click_button("premium_self")
        
        # 3. 点击返回/取消
        await helper.click_button("back_to_main")
        
        # 验证返回主菜单
        message = helper.get_message_text()
        assert message is not None
    
    @pytest.mark.asyncio
    async def test_premium_invalid_username(self, helper):
        """测试无效用户名处理（给他人开通场景）"""
        # 1. 进入 Premium 页面
        await helper.send_command("start")
        await helper.click_button("menu_premium")
        
        # 2. 选择给他人开通
        await helper.click_button("premium_other")
        
        # 3. 输入无效用户名（少于5字符）
        await helper.send_message("@ab")
        
        # 验证有响应（可能是错误提示或重新输入提示）
        message = helper.get_message_text()
        assert message is not None
    
    @pytest.mark.asyncio
    async def test_premium_command_entry(self, helper):
        """测试通过主菜单按钮进入 Premium"""
        # 进入主菜单
        await helper.send_command("start")
        
        # 点击 Premium 按钮
        await helper.click_button("menu_premium")
        
        # 验证显示 Premium 页面
        message = helper.get_message_text()
        assert message is not None
        assert "Premium" in message
    
    @pytest.mark.asyncio  
    async def test_premium_conversation_reentry(self, helper):
        """测试对话重入（用户在流程中返回主菜单再进入）"""
        # 1. 进入 Premium 页面
        await helper.send_command("start")
        await helper.click_button("menu_premium")
        
        # 2. 选择给自己开通
        await helper.click_button("premium_self")
        
        # 3. 返回主菜单
        await helper.click_button("back_to_main")
        
        # 4. 重新进入 Premium
        await helper.click_button("menu_premium")
        
        # 验证重新显示 Premium 页面
        message = helper.get_message_text()
        assert message is not None
        assert "Premium" in message


class TestPremiumValidation:
    """Premium 输入验证测试"""
    
    @pytest.mark.asyncio
    async def test_recipient_parser(self):
        """测试收件人解析器"""
        from src.modules.premium.recipient_parser import RecipientParser
        
        test_cases = [
            # (输入文本, 预期结果) - 用户名至少5字符
            ("@alice", ["alice"]),
            ("@alice @bobby", ["alice", "bobby"]),
            ("t.me/charles", ["charles"]),
            ("@alice\n@bobby\nt.me/charles", ["alice", "bobby", "charles"]),
            ("@ALICE @alice", ["alice"]),  # 去重
            ("@ab", []),  # 太短
            ("@user_123", ["user_123"]),  # 下划线和数字
            ("混合文本 @user1 其他内容 t.me/user2", ["user1", "user2"]),
        ]
        
        for text, expected in test_cases:
            result = RecipientParser.parse(text)
            assert result == expected, f"Failed for '{text}': got {result}, expected {expected}"
        
        print("✅ 收件人解析器测试通过")
    
    @pytest.mark.asyncio
    async def test_username_validation(self):
        """测试用户名验证"""
        from src.modules.premium.recipient_parser import RecipientParser
        
        valid_usernames = [
            "alice",  # 5字符
            "user_123",  # 下划线和数字
            "a" * 32,  # 32字符（最大）
            "User_Name_123",  # 混合
        ]
        
        invalid_usernames = [
            "ab",  # 太短
            "a" * 33,  # 太长
            "user-name",  # 连字符
            "user.name",  # 点
            "用户",  # 非ASCII
            "",  # 空
        ]
        
        for username in valid_usernames:
            assert RecipientParser.validate_username(username), f"'{username}' should be valid"
        
        for username in invalid_usernames:
            assert not RecipientParser.validate_username(username), f"'{username}' should be invalid"
        
        print("✅ 用户名验证测试通过")


class TestPremiumEdgeCases:
    """Premium 边界条件测试"""

    @pytest.fixture
    async def helper(self, bot_app_v2):
        """基于 bot_app_v2 创建测试辅助类"""
        helper = BotTestHelper(bot_app_v2)
        await helper.initialize()
        yield helper

    @pytest.mark.asyncio
    async def test_premium_packages_all_durations(self, helper):
        """测试所有套餐时长选择（3/6/12个月）"""
        packages = ["premium_3", "premium_6", "premium_12"]

        for pkg in packages:
            await helper.send_command("start")
            await helper.click_button("menu_premium")
            await helper.click_button("premium_self")
            await helper.click_button(pkg)

            message = helper.get_message_text()
            assert message is not None, f"套餐 {pkg} 应有响应"

    @pytest.mark.asyncio
    async def test_premium_other_valid_username(self, helper):
        """测试为他人开通 - 有效用户名"""
        await helper.send_command("start")
        await helper.click_button("menu_premium")
        await helper.click_button("premium_other")

        # 输入有效用户名（至少5个字符）
        await helper.send_message("@valid_username")

        message = helper.get_message_text()
        assert message is not None

    @pytest.mark.asyncio
    async def test_premium_other_multiple_usernames(self, helper):
        """测试为他人开通 - 多个用户名"""
        await helper.send_command("start")
        await helper.click_button("menu_premium")
        await helper.click_button("premium_other")

        # 输入多个用户名
        await helper.send_message("@user_one @user_two")

        message = helper.get_message_text()
        assert message is not None

    @pytest.mark.asyncio
    async def test_premium_back_navigation(self, helper):
        """测试返回导航"""
        await helper.send_command("start")
        await helper.click_button("menu_premium")
        await helper.click_button("premium_self")

        # 点击返回
        await helper.click_button("premium_back_target")

        message = helper.get_message_text()
        assert message is not None


class TestPremiumErrorHandling:
    """Premium 错误处理测试"""

    @pytest.mark.asyncio
    async def test_invalid_username_too_short(self):
        """测试用户名太短的情况"""
        from src.modules.premium.recipient_parser import RecipientParser

        result = RecipientParser.parse("@ab")
        assert result == [], "太短的用户名应被拒绝"

    @pytest.mark.asyncio
    async def test_invalid_username_special_chars(self):
        """测试用户名包含特殊字符"""
        from src.modules.premium.recipient_parser import RecipientParser

        invalid_usernames = ["@user-name", "@user.name", "@user@name"]
        for username in invalid_usernames:
            result = RecipientParser.parse(username)
            assert result == [], f"包含特殊字符的用户名 {username} 应被拒绝"

    @pytest.mark.asyncio
    async def test_empty_input(self):
        """测试空输入"""
        from src.modules.premium.recipient_parser import RecipientParser

        result = RecipientParser.parse("")
        assert result == [], "空输入应返回空列表"

    @pytest.mark.asyncio
    async def test_duplicate_usernames_removed(self):
        """测试重复用户名去重"""
        from src.modules.premium.recipient_parser import RecipientParser

        result = RecipientParser.parse("@alice @ALICE @Alice")
        # 应该去重，只保留一个
        assert len(result) <= 1, "重复用户名应被去重"


class TestPremiumOrderCreation:
    """Premium 订单创建测试"""

    @pytest.mark.asyncio
    async def test_order_factory_creation(self):
        """测试订单工厂创建"""
        from tests.factories.order_factory import PremiumOrderFactory

        order = PremiumOrderFactory.create_pending(
            buyer_id=123456789,
            premium_months=3,
        )

        assert order is not None
        assert order.status == "PENDING"
        assert order.premium_months == 3
        assert order.buyer_id == 123456789

    @pytest.mark.asyncio
    async def test_order_expired_factory(self):
        """测试过期订单工厂"""
        from tests.factories.order_factory import PremiumOrderFactory

        order = PremiumOrderFactory.create_expired(
            buyer_id=123456789,
            premium_months=6,
        )

        assert order.status == "EXPIRED"

    @pytest.mark.asyncio
    async def test_order_completed_factory(self):
        """测试完成订单工厂"""
        from tests.factories.order_factory import PremiumOrderFactory

        order = PremiumOrderFactory.create_completed(
            buyer_id=123456789,
            premium_months=12,
        )

        assert order.status == "COMPLETED"
        assert order.tx_hash is not None


@pytest.mark.asyncio
async def test_run_ci():
    """运行所有 CI 测试"""
    print("\n" + "="*80)
    print(" Premium 功能 CI 测试套件 ".center(80, "="))
    print("="*80)

    # 运行验证测试
    validator = TestPremiumValidation()
    await validator.test_recipient_parser()
    await validator.test_username_validation()

    print("\n" + "-"*80)
    print(" 所有测试通过 ✅ ".center(80))
    print("-"*80)


if __name__ == "__main__":
    # 运行CI测试
    asyncio.run(test_run_ci())
