"""
Energy 模块完整测试
测试能量兑换模块的所有功能，包括三种购买类型、API 模拟、地址验证
"""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from tests.utils.telegram_simulator import BotTestHelper
from tests.mocks.energy_api_responses import EnergyAPIMockResponses


class TestEnergyModuleImport:
    """测试 Energy 模块导入"""
    
    def test_import_handler(self):
        """测试 handler 导入"""
        from src.modules.energy.handler import EnergyModule
        assert EnergyModule is not None
    
    def test_import_client(self):
        """测试 client 导入"""
        from src.modules.energy.client import EnergyAPIClient
        assert EnergyAPIClient is not None
    
    def test_module_name(self):
        """测试模块名称"""
        from src.modules.energy.handler import EnergyModule
        module = EnergyModule()
        assert module.module_name == "energy"


class TestEnergyOrderTypes:
    """测试三种能量购买类型"""

    @pytest.fixture
    async def helper(self, bot_app_v2):
        """创建测试辅助类"""
        helper = BotTestHelper(bot_app_v2)
        await helper.initialize()
        yield helper

    @pytest.mark.asyncio
    async def test_energy_menu_entry(self, helper):
        """测试进入能量菜单"""
        await helper.send_command("start")
        await helper.click_button("menu_energy")

        message = helper.get_message_text()
        assert message is not None

    @pytest.mark.asyncio
    async def test_energy_hourly_type(self, helper):
        """测试时长能量类型"""
        await helper.send_command("start")
        await helper.click_button("menu_energy")
        await helper.click_button("energy_type_hourly")

        message = helper.get_message_text()
        assert message is not None

    @pytest.mark.asyncio
    async def test_energy_package_type(self, helper):
        """测试笔数套餐类型"""
        await helper.send_command("start")
        await helper.click_button("menu_energy")
        await helper.click_button("energy_type_package")

        message = helper.get_message_text()
        assert message is not None

    @pytest.mark.asyncio
    async def test_energy_flash_type(self, helper):
        """测试闪兑类型"""
        await helper.send_command("start")
        await helper.click_button("menu_energy")
        await helper.click_button("energy_type_flash")
        
        message = helper.get_message_text()
        assert message is not None


class TestEnergyAddressValidation:
    """测试能量模块地址验证"""

    def test_valid_tron_address(self):
        """测试有效的 TRON 地址"""
        from src.modules.address_query.validator import AddressValidator

        valid_addresses = [
            "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH",
            "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
        ]

        for addr in valid_addresses:
            is_valid, _ = AddressValidator.validate(addr)
            assert is_valid is True, f"{addr} should be valid"

    def test_invalid_tron_address(self):
        """测试无效的 TRON 地址"""
        from src.modules.address_query.validator import AddressValidator

        invalid_addresses = [
            "",
            "short",
            "0x1234567890abcdef",  # ETH 格式
            "ALyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH",  # 非 T 开头
            "TLyqzVGLV1srkB7dToTAEqgDSfPtXR",  # 太短
        ]

        for addr in invalid_addresses:
            is_valid, _ = AddressValidator.validate(addr)
            assert is_valid is False, f"{addr} should be invalid"


class TestEnergyAPIMock:
    """测试 Energy API Mock"""
    
    def test_account_info_mock(self):
        """测试账户信息 mock"""
        response = EnergyAPIMockResponses.account_info()
        
        assert response["code"] == 0
        assert "data" in response
        assert "balance_trx" in response["data"]
    
    def test_price_query_mock(self):
        """测试价格查询 mock"""
        response = EnergyAPIMockResponses.price_query()
        
        assert response["code"] == 0
        assert "data" in response
        assert "energy_65k_price" in response["data"]
    
    def test_error_response_mock(self):
        """测试错误响应 mock"""
        response = EnergyAPIMockResponses.insufficient_balance()
        
        assert response["code"] == 1002
        assert "Insufficient balance" in response["message"]


class TestEnergyOrderFactory:
    """测试 Energy 订单工厂"""
    
    def test_create_hourly_order(self):
        """测试创建时长订单"""
        from tests.factories.order_factory import EnergyOrderFactory
        
        order = EnergyOrderFactory.create(
            order_type="hourly",
            energy_amount=65000,
        )
        
        assert order.order_type == "hourly"
        assert order.energy_amount == 65000
        assert order.status == "PENDING"
    
    def test_create_package_order(self):
        """测试创建笔数订单"""
        from tests.factories.order_factory import EnergyOrderFactory
        
        order = EnergyOrderFactory.create(
            order_type="package",
            energy_amount=10,  # 10笔
        )
        
        assert order.order_type == "package"
    
    def test_create_flash_order(self):
        """测试创建闪兑订单"""
        from tests.factories.order_factory import EnergyOrderFactory
        
        order = EnergyOrderFactory.create(
            order_type="flash",
        )
        
        assert order.order_type == "flash"

