"""
测试 Premium 交付服务 - 自动发货模式
"""
import pytest
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Bot, Chat
from telegram.error import TelegramError
from src.modules.premium.delivery import PremiumDeliveryService
from src.payments.order import order_manager


def create_mock_db_context(mock_db):
    """创建一个返回 mock db 的上下文管理器"""
    @contextmanager
    def mock_context():
        yield mock_db
    return mock_context


@pytest.fixture
def mock_bot():
    """创建模拟 Bot"""
    bot = AsyncMock(spec=Bot)
    
    # 模拟 Stars 交易记录
    mock_transactions = MagicMock()
    mock_transactions.transactions = []
    bot.get_star_transactions = AsyncMock(return_value=mock_transactions)
    
    # 模拟 get_chat
    mock_chat = MagicMock(spec=Chat)
    mock_chat.id = 123456
    mock_chat.first_name = "Alice"
    bot.get_chat = AsyncMock(return_value=mock_chat)
    
    # 模拟 gift_premium_subscription
    bot.gift_premium_subscription = AsyncMock()
    
    # 模拟 send_message
    bot.send_message = AsyncMock()
    
    return bot


@pytest.fixture
def delivery_service(mock_bot):
    """创建交付服务"""
    return PremiumDeliveryService(mock_bot, order_manager)


@pytest.mark.asyncio
async def test_stars_price_config(delivery_service):
    """测试 Stars 价格配置"""
    assert delivery_service.STARS_PRICE[3] == 1000
    assert delivery_service.STARS_PRICE[6] == 1750
    assert delivery_service.STARS_PRICE[12] == 3000


@pytest.mark.asyncio
async def test_check_stars_balance_empty(delivery_service, mock_bot):
    """测试检查 Stars 余额（空交易）"""
    balance = await delivery_service.check_stars_balance()
    assert balance == 0
    mock_bot.get_star_transactions.assert_called_once_with(limit=100)


@pytest.mark.asyncio
async def test_check_stars_balance_with_transactions(delivery_service, mock_bot):
    """测试检查 Stars 余额（有交易）"""
    # 模拟交易记录
    mock_tx1 = MagicMock()
    mock_tx1.source = True  # 收入
    mock_tx1.receiver = None
    mock_tx1.amount = 500
    
    mock_tx2 = MagicMock()
    mock_tx2.source = None
    mock_tx2.receiver = True  # 支出
    mock_tx2.amount = 200
    
    mock_transactions = MagicMock()
    mock_transactions.transactions = [mock_tx1, mock_tx2]
    mock_bot.get_star_transactions = AsyncMock(return_value=mock_transactions)
    
    balance = await delivery_service.check_stars_balance()
    assert balance == 300  # 500 - 200


@pytest.mark.asyncio
async def test_resolve_user_id_success(delivery_service, mock_bot):
    """测试解析用户名成功"""
    user_id = await delivery_service._resolve_user_id("alice")
    assert user_id == 123456
    mock_bot.get_chat.assert_called_once_with("@alice")


@pytest.mark.asyncio
async def test_resolve_user_id_not_found(delivery_service, mock_bot):
    """测试解析用户名失败"""
    mock_bot.get_chat = AsyncMock(side_effect=TelegramError("User not found"))
    
    user_id = await delivery_service._resolve_user_id("unknown_user")
    assert user_id is None


@pytest.mark.asyncio
async def test_deliver_premium_no_recipient_id(delivery_service, mock_bot):
    """测试发货时无 recipient_id，需要解析"""
    # 模拟足够的余额
    mock_tx = MagicMock()
    mock_tx.source = True
    mock_tx.receiver = None
    mock_tx.amount = 2000
    mock_transactions = MagicMock()
    mock_transactions.transactions = [mock_tx]
    mock_bot.get_star_transactions = AsyncMock(return_value=mock_transactions)
    
    # 使用 patch 模拟数据库上下文管理器
    mock_db = MagicMock()
    mock_order = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_order

    with patch('src.modules.premium.delivery.get_db_context', return_value=create_mock_db_context(mock_db)()):
        result = await delivery_service.deliver_premium(
            order_id="test-order-123",
            buyer_id=999,
            recipient_username="alice",
            recipient_id=None,  # 无 ID，需要解析
            premium_months=3
        )

        assert result["success"] is True
        assert result["recipient_id"] == 123456
        mock_bot.gift_premium_subscription.assert_called_once()


@pytest.mark.asyncio
async def test_deliver_premium_insufficient_balance(delivery_service, mock_bot):
    """测试发货时余额不足"""
    # 模拟余额不足
    mock_transactions = MagicMock()
    mock_transactions.transactions = []
    mock_bot.get_star_transactions = AsyncMock(return_value=mock_transactions)

    # 使用 patch 模拟数据库上下文管理器
    mock_db = MagicMock()
    mock_order = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_order

    with patch('src.modules.premium.delivery.get_db_context', return_value=create_mock_db_context(mock_db)()):
        result = await delivery_service.deliver_premium(
            order_id="test-order-123",
            buyer_id=999,
            recipient_username="alice",
            recipient_id=123456,
            premium_months=3
        )

        assert result["success"] is False
        assert "余额不足" in result["message"]
