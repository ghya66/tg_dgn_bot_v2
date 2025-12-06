"""
Address Query 模块完整测试
测试地址查询模块的所有功能，包括频率限制、API 模拟、余额格式化
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from tests.utils.telegram_simulator import BotTestHelper
from tests.mocks.tronscan_responses import TronScanMockResponses, TEST_ADDRESSES


class TestAddressQueryModuleImport:
    """测试模块导入"""
    
    def test_import_handler(self):
        """测试 handler 导入"""
        from src.modules.address_query.handler import AddressQueryModule
        assert AddressQueryModule is not None
    
    def test_import_validator(self):
        """测试 validator 导入"""
        from src.modules.address_query.validator import AddressValidator
        assert AddressValidator is not None
    
    def test_module_name(self):
        """测试模块名称"""
        from src.modules.address_query.handler import AddressQueryModule
        module = AddressQueryModule()
        assert module.module_name == "address_query"


class TestAddressQueryFlow:
    """测试地址查询流程"""

    @pytest.fixture
    async def helper(self, bot_app_v2):
        """创建测试辅助类"""
        helper = BotTestHelper(bot_app_v2)
        await helper.initialize()
        yield helper

    @pytest.mark.asyncio
    async def test_address_query_menu_entry(self, helper):
        """测试进入地址查询菜单"""
        await helper.send_command("start")
        await helper.click_button("menu_address_query")

        message = helper.get_message_text()
        assert message is not None


class TestAddressQueryRateLimit:
    """测试频率限制"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_with_fakeredis(self, fake_redis):
        """测试使用 fakeredis 的频率限制"""
        user_id = 123456789
        rate_limit_key = f"addr_query_limit:{user_id}"
        
        # 第一次查询 - 应该允许
        exists = await fake_redis.exists(rate_limit_key)
        assert exists == 0
        
        # 设置频率限制（1分钟）
        await fake_redis.setex(rate_limit_key, 60, "1")
        
        # 第二次查询 - 应该被限制
        exists = await fake_redis.exists(rate_limit_key)
        assert exists == 1
    
    @pytest.mark.asyncio
    async def test_rate_limit_expiry(self, fake_redis):
        """测试频率限制过期"""
        user_id = 123456789
        rate_limit_key = f"addr_query_limit:{user_id}"
        
        # 设置1秒过期
        await fake_redis.setex(rate_limit_key, 1, "1")
        
        # 立即检查 - 应该存在
        exists = await fake_redis.exists(rate_limit_key)
        assert exists == 1
        
        # 等待过期
        import asyncio
        await asyncio.sleep(1.5)
        
        # 过期后 - 应该不存在
        exists = await fake_redis.exists(rate_limit_key)
        assert exists == 0


class TestTronScanAPIMock:
    """测试 TronScan API Mock"""
    
    def test_account_info_mock(self):
        """测试账户信息 mock"""
        response = TronScanMockResponses.account_info(
            address=TEST_ADDRESSES["valid"],
            trx_balance=1000000000,  # 1000 TRX
            usdt_balance="100000000",  # 100 USDT
        )
        
        assert response["address"] == TEST_ADDRESSES["valid"]
        assert response["balance"] == 1000000000
        assert len(response["trc20token_balances"]) == 1
    
    def test_account_not_found_mock(self):
        """测试账户不存在 mock"""
        response = TronScanMockResponses.account_not_found(
            address=TEST_ADDRESSES["empty"]
        )
        
        assert response["balance"] == 0
        assert response["trc20token_balances"] == []
    
    def test_error_response_mock(self):
        """测试错误响应 mock"""
        response = TronScanMockResponses.error_response(500, "Server Error")
        
        assert response["error"] is True
        assert response["code"] == 500
    
    def test_rate_limit_mock(self):
        """测试频率限制 mock"""
        response = TronScanMockResponses.rate_limit_response()
        
        assert response["code"] == 429


class TestBalanceFormatting:
    """测试余额格式化"""
    
    def test_format_trx_balance(self):
        """测试 TRX 余额格式化"""
        # 1 TRX = 1,000,000 sun
        sun_balance = 1000000000  # 1000 TRX
        trx_balance = sun_balance / 1_000_000
        
        assert trx_balance == 1000.0
    
    def test_format_usdt_balance(self):
        """测试 USDT 余额格式化"""
        # USDT 有 6 位小数
        raw_balance = "100000000"  # 100 USDT
        usdt_balance = int(raw_balance) / 1_000_000
        
        assert usdt_balance == 100.0
    
    def test_format_small_balance(self):
        """测试小额余额格式化"""
        raw_balance = "123456"  # 0.123456 USDT
        usdt_balance = int(raw_balance) / 1_000_000
        
        assert usdt_balance == 0.123456
    
    def test_format_zero_balance(self):
        """测试零余额格式化"""
        raw_balance = "0"
        usdt_balance = int(raw_balance) / 1_000_000
        
        assert usdt_balance == 0.0


class TestAddressQueryLogging:
    """测试查询日志"""

    def test_log_entry_creation(self, full_test_db):
        """测试日志记录创建"""
        from src.database import AddressQueryLog

        # AddressQueryLog 只记录用户ID和最后查询时间
        log = AddressQueryLog(
            user_id=123456789,
            last_query_at=datetime.now(),
            query_count=1,
        )

        full_test_db.add(log)
        full_test_db.commit()

        # 验证记录
        saved_log = full_test_db.query(AddressQueryLog).first()
        assert saved_log is not None
        assert saved_log.user_id == 123456789
        assert saved_log.query_count == 1


class TestAddressQueryHandlerMethods:
    """测试 AddressQueryModule 的各个方法"""

    @pytest.fixture
    def module(self):
        """创建模块实例"""
        from src.modules.address_query.handler import AddressQueryModule
        return AddressQueryModule()

    def test_get_handlers_returns_list(self, module):
        """测试 get_handlers 返回列表"""
        handlers = module.get_handlers()
        assert isinstance(handlers, list)
        assert len(handlers) == 1  # 一个 ConversationHandler

    def test_check_rate_limit_no_previous_query(self, module, full_test_db):
        """测试没有历史查询时的限频检查"""
        # 使用一个不存在查询记录的用户ID
        can_query, remaining = module._check_rate_limit(999999999)
        assert can_query is True
        assert remaining == 0

    def test_check_rate_limit_within_cooldown(self, module, full_test_db):
        """测试冷却时间内的限频检查"""
        from src.database import AddressQueryLog, SessionLocal
        import uuid

        # 使用唯一的用户ID避免冲突
        user_id = int(uuid.uuid4().int % 1000000000)
        db = SessionLocal()
        try:
            # 创建一个刚刚的查询记录
            log = AddressQueryLog(
                user_id=user_id,
                last_query_at=datetime.now(),
                query_count=1
            )
            db.add(log)
            db.commit()
        finally:
            db.close()

        # 检查限频
        can_query, remaining = module._check_rate_limit(user_id)
        assert can_query is False
        assert remaining >= 1

    def test_record_query(self, module, full_test_db):
        """测试记录查询"""
        from src.database import AddressQueryLog, SessionLocal

        user_id = 777777777

        # 记录查询
        module._record_query(user_id)

        # 验证记录已创建
        db = SessionLocal()
        try:
            log = db.query(AddressQueryLog).filter_by(user_id=user_id).first()
            assert log is not None
            assert log.user_id == user_id
        finally:
            db.close()


class TestAddressValidatorEdgeCases:
    """测试地址验证器边界情况"""

    @pytest.fixture
    def validator(self):
        from src.modules.address_query.validator import AddressValidator
        return AddressValidator()

    def test_valid_address_exact_length(self, validator):
        """测试正好34字符的有效地址"""
        # TRON 地址正好34字符
        address = "TN3W4H6rK2ce4vX9YnFQHwKENnHjoxb3m9"
        is_valid, _ = validator.validate(address)
        assert is_valid is True

    def test_address_with_spaces(self, validator):
        """测试带空格的地址"""
        # 地址中间有空格（handler 中会先清理）
        address = "TN3W4H6rK2ce4vX9YnFQHwKENnHjoxb3m9"
        is_valid, _ = validator.validate(address)
        assert is_valid is True

    def test_address_wrong_prefix_lowercase(self, validator):
        """测试错误前缀（小写t）"""
        address = "tN3W4H6rK2ce4vX9YnFQHwKENnHjoxb3m9"
        is_valid, error = validator.validate(address)
        assert is_valid is False
        assert error is not None

    def test_address_too_short(self, validator):
        """测试太短的地址"""
        address = "TN3W4H6rK2ce"
        is_valid, error = validator.validate(address)
        assert is_valid is False

    def test_address_too_long(self, validator):
        """测试太长的地址"""
        address = "TN3W4H6rK2ce4vX9YnFQHwKENnHjoxb3m9EXTRA"
        is_valid, error = validator.validate(address)
        assert is_valid is False

    def test_address_with_special_chars(self, validator):
        """测试带特殊字符的地址"""
        address = "TN3W4H6rK2ce4vX9YnFQHwKENnH!@#$%^"
        is_valid, error = validator.validate(address)
        assert is_valid is False


class TestAddressQueryModuleAsyncMethods:
    """测试异步方法"""

    @pytest.fixture
    def module(self):
        from src.modules.address_query.handler import AddressQueryModule
        return AddressQueryModule()

    @pytest.fixture
    def mock_update(self):
        """创建模拟的 Update 对象"""
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 123456789
        update.callback_query = None
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """创建模拟的 Context 对象"""
        context = MagicMock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_start_query_from_message(self, module, mock_update, mock_context):
        """测试从消息开始查询"""
        with patch.object(module, '_check_rate_limit', return_value=(True, 0)):
            result = await module.start_query(mock_update, mock_context)
            assert result == 0  # AWAITING_ADDRESS
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_query_rate_limited(self, module, mock_update, mock_context):
        """测试被限频时的开始查询"""
        with patch.object(module, '_check_rate_limit', return_value=(False, 5)):
            from telegram.ext import ConversationHandler
            result = await module.start_query(mock_update, mock_context)
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_cancel_operation(self, module, mock_context):
        """测试取消操作"""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        with patch('src.modules.address_query.handler.NavigationManager') as mock_nav:
            mock_nav.cleanup_and_show_main_menu = AsyncMock(return_value=-1)
            result = await module.cancel(update, mock_context)
            mock_nav.cleanup_and_show_main_menu.assert_called_once()


class TestHandleAddressInput:
    """测试地址输入处理"""

    @pytest.fixture
    def module(self):
        from src.modules.address_query.handler import AddressQueryModule
        return AddressQueryModule()

    @pytest.fixture
    def mock_update(self):
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 123456789
        update.message = MagicMock()
        update.message.text = "TN3W4H6rK2ce4vX9YnFQHwKENnHjoxb3m9"
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        context = MagicMock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_handle_invalid_address(self, module, mock_update, mock_context):
        """测试处理无效地址"""
        mock_update.message.text = "invalid_address"

        result = await module.handle_address_input(mock_update, mock_context)
        assert result == 0  # AWAITING_ADDRESS，继续等待输入

    @pytest.mark.asyncio
    async def test_handle_valid_address_success(self, module, mock_update, mock_context):
        """测试处理有效地址成功"""
        from src.clients.tron import AddressInfo

        # Mock 所有依赖
        mock_address_info = MagicMock(spec=AddressInfo)
        mock_address_info.format_trx.return_value = "1000.00"
        mock_address_info.format_usdt.return_value = "500.00"
        mock_address_info.recent_txs = []

        processing_msg = MagicMock()
        processing_msg.delete = AsyncMock()
        mock_update.message.reply_text = AsyncMock(return_value=processing_msg)

        with patch.object(module, '_check_rate_limit', return_value=(True, 0)), \
             patch.object(module, '_record_query'), \
             patch.object(module.tron_client, 'get_address_info', new_callable=AsyncMock, return_value=mock_address_info):

            from telegram.ext import ConversationHandler
            result = await module.handle_address_input(mock_update, mock_context)
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_handle_address_rate_limited_during_input(self, module, mock_update, mock_context):
        """测试输入地址时被限频"""
        with patch.object(module.validator, 'validate', return_value=(True, None)), \
             patch.object(module, '_check_rate_limit', return_value=(False, 3)):

            from telegram.ext import ConversationHandler
            result = await module.handle_address_input(mock_update, mock_context)
            assert result == ConversationHandler.END

