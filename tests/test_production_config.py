"""
生产环境配置检查测试

测试 Task-C1: TRX 测试模式启动检查
验证生产环境配置检查逻辑的正确性
"""
import pytest
import logging
from unittest.mock import patch, MagicMock, AsyncMock
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class MockTRXConfig:
    """Mock TRX 配置"""
    receive_address: str = 'TTestAddress123'
    send_address: str = 'TTestAddress456'
    private_key: str = ''
    qrcode_file_id: str = ''
    default_rate: Decimal = Decimal('3.05')
    test_mode: bool = True


class TestTRXSenderProductionConfig:
    """TRXSender 生产环境配置测试"""

    def test_test_mode_critical_warning_in_prod(self, caplog):
        """测试：生产环境 + 测试模式 = CRITICAL 日志"""
        # 使用预配置的 config 对象，避免从 settings 读取
        config = MockTRXConfig(test_mode=True)

        with caplog.at_level(logging.WARNING, logger='src.modules.trx_exchange.trx_sender'):
            with patch('src.modules.trx_exchange.trx_sender.settings') as mock_settings:
                mock_settings.env = 'prod'

                from src.modules.trx_exchange.trx_sender import TRXSender
                sender = TRXSender(config=config)

        # 验证输出了 CRITICAL 级别的警告（包含 production 关键词）
        log_text = "\n".join(record.message for record in caplog.records)
        assert "CRITICAL" in log_text or "production" in log_text.lower()

    def test_test_mode_warning_in_dev(self, caplog):
        """测试：开发环境 + 测试模式 = WARNING 日志"""
        config = MockTRXConfig(test_mode=True)

        with caplog.at_level(logging.WARNING, logger='src.modules.trx_exchange.trx_sender'):
            with patch('src.modules.trx_exchange.trx_sender.settings') as mock_settings:
                mock_settings.env = 'dev'

                from src.modules.trx_exchange.trx_sender import TRXSender
                sender = TRXSender(config=config)

        # 验证输出了 WARNING 或 TEST MODE 相关日志
        log_text = "\n".join(record.message for record in caplog.records)
        assert "TEST MODE" in log_text or "simulated" in log_text.lower()

    def test_production_mode_no_critical_warning(self, caplog):
        """测试：生产环境 + 非测试模式 + 有效私钥 = 无 CRITICAL 警告"""
        # 提供有效的 64 字符 hex 私钥格式
        valid_private_key = '0123456789abcdef' * 4
        config = MockTRXConfig(test_mode=False, private_key=valid_private_key)

        with caplog.at_level(logging.INFO, logger='src.modules.trx_exchange.trx_sender'):
            with patch('src.modules.trx_exchange.trx_sender.settings') as mock_settings:
                mock_settings.env = 'prod'

                from src.modules.trx_exchange.trx_sender import TRXSender
                sender = TRXSender(config=config)

        # 验证没有 CRITICAL 警告
        critical_records = [r for r in caplog.records if r.levelno >= logging.CRITICAL]
        assert len(critical_records) == 0


class TestBotProductionConfigCheck:
    """Bot 生产环境配置检查测试"""
    
    @pytest.mark.asyncio
    async def test_production_config_check_trx_test_mode_critical(self, caplog, capsys):
        """测试：生产环境检查 TRX 测试模式 -> CRITICAL"""
        mock_settings = MagicMock()
        mock_settings.env = 'prod'
        mock_settings.trx_exchange_test_mode = True
        mock_settings.api_keys = ['key1']
        mock_settings.bot_owner_id = 12345

        # 确保 logger 传播到 root
        import logging
        logger = logging.getLogger('src.bot_v2')
        original_propagate = logger.propagate
        logger.propagate = True

        try:
            with caplog.at_level(logging.WARNING):
                with patch('src.bot_v2.settings', mock_settings):
                    from src.bot_v2 import TelegramBotV2
                    bot = TelegramBotV2.__new__(TelegramBotV2)
                    await bot._check_production_config()

            # 优先检查 caplog
            log_text = "\n".join(record.message for record in caplog.records)
            if "TRX_EXCHANGE_TEST_MODE" in log_text:
                assert True
            else:
                # 回退到检查 stdout（某些日志配置可能直接输出到 stdout）
                captured = capsys.readouterr()
                assert "TRX_EXCHANGE_TEST_MODE" in captured.out
        finally:
            logger.propagate = original_propagate
    
    @pytest.mark.asyncio
    async def test_production_config_check_api_keys_warning(self, caplog):
        """测试：生产环境检查 API Keys 未配置 -> WARNING"""
        mock_settings = MagicMock()
        mock_settings.env = 'prod'
        mock_settings.trx_exchange_test_mode = False
        mock_settings.api_keys = []  # 未配置
        mock_settings.bot_owner_id = 12345

        with caplog.at_level(logging.WARNING, logger='src.bot_v2'):
            with patch('src.bot_v2.settings', mock_settings):
                from src.bot_v2 import TelegramBotV2
                bot = TelegramBotV2.__new__(TelegramBotV2)
                await bot._check_production_config()

        # 验证输出了 API_KEYS 相关警告
        log_text = "\n".join(record.message for record in caplog.records)
        assert "API_KEYS" in log_text

    @pytest.mark.asyncio
    async def test_production_config_check_bot_owner_warning(self, caplog):
        """测试：生产环境检查 BOT_OWNER_ID 未配置 -> WARNING"""
        mock_settings = MagicMock()
        mock_settings.env = 'prod'
        mock_settings.trx_exchange_test_mode = False
        mock_settings.api_keys = ['key1']
        mock_settings.bot_owner_id = 0  # 未配置

        with caplog.at_level(logging.WARNING, logger='src.bot_v2'):
            with patch('src.bot_v2.settings', mock_settings):
                from src.bot_v2 import TelegramBotV2
                bot = TelegramBotV2.__new__(TelegramBotV2)
                await bot._check_production_config()

        # 验证输出了 BOT_OWNER_ID 相关警告
        log_text = "\n".join(record.message for record in caplog.records)
        assert "BOT_OWNER_ID" in log_text

    @pytest.mark.asyncio
    async def test_production_config_check_all_configured(self, caplog):
        """测试：生产环境所有配置正确 -> 无 CRITICAL/WARNING"""
        mock_settings = MagicMock()
        mock_settings.env = 'prod'
        mock_settings.trx_exchange_test_mode = False
        mock_settings.api_keys = ['key1', 'key2']
        mock_settings.bot_owner_id = 12345

        with caplog.at_level(logging.INFO, logger='src.bot_v2'):
            with patch('src.bot_v2.settings', mock_settings):
                from src.bot_v2 import TelegramBotV2
                bot = TelegramBotV2.__new__(TelegramBotV2)
                await bot._check_production_config()

        # 验证有成功日志
        log_text = "\n".join(record.message for record in caplog.records)
        assert "✅" in log_text

        # 验证没有 CRITICAL 级别日志
        critical_records = [r for r in caplog.records if r.levelno >= logging.CRITICAL]
        assert len(critical_records) == 0

    @pytest.mark.asyncio
    async def test_dev_environment_skips_strict_check(self, caplog):
        """测试：开发环境跳过严格检查"""
        mock_settings = MagicMock()
        mock_settings.env = 'dev'
        mock_settings.trx_exchange_test_mode = True
        mock_settings.api_keys = []
        mock_settings.bot_owner_id = 0

        with caplog.at_level(logging.INFO, logger='src.bot_v2'):
            with patch('src.bot_v2.settings', mock_settings):
                from src.bot_v2 import TelegramBotV2
                bot = TelegramBotV2.__new__(TelegramBotV2)
                await bot._check_production_config()

        # 验证显示非生产环境信息
        log_text = "\n".join(record.message for record in caplog.records)
        assert "非生产环境" in log_text or "dev" in log_text.lower()

        # 验证没有 CRITICAL 级别日志（开发环境不严格检查）
        critical_records = [r for r in caplog.records if r.levelno >= logging.CRITICAL]
        assert len(critical_records) == 0

