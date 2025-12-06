"""
订单生命周期端到端测试
测试订单从创建到完成/过期的完整流程
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from tests.factories.order_factory import (
    PremiumOrderFactory,
    EnergyOrderFactory,
    TRXExchangeOrderFactory,
)


class TestOrderStatusTransitions:
    """测试订单状态转换"""
    
    def test_pending_to_paid(self, full_test_db):
        """测试 PENDING → PAID 状态转换"""
        from src.database import PremiumOrder
        
        # 创建待支付订单
        order = PremiumOrderFactory.create_pending()
        full_test_db.add(order)
        full_test_db.commit()
        
        # 模拟支付确认
        order.status = "PAID"
        order.tx_hash = "tx_payment_confirmed"
        full_test_db.commit()
        
        # 验证状态
        saved_order = full_test_db.query(PremiumOrder).filter_by(
            order_id=order.order_id
        ).first()
        
        assert saved_order.status == "PAID"
        assert saved_order.tx_hash is not None
    
    def test_paid_to_completed(self, full_test_db):
        """测试 PAID → COMPLETED 状态转换"""
        from src.database import PremiumOrder
        
        # 创建已支付订单
        order = PremiumOrderFactory.create(status="PAID")
        full_test_db.add(order)
        full_test_db.commit()
        
        # 模拟处理完成
        order.status = "COMPLETED"
        order.completed_at = datetime.now()
        full_test_db.commit()
        
        # 验证状态
        saved_order = full_test_db.query(PremiumOrder).filter_by(
            order_id=order.order_id
        ).first()
        
        assert saved_order.status == "COMPLETED"
        assert saved_order.completed_at is not None
    
    def test_pending_to_expired(self, full_test_db):
        """测试 PENDING → EXPIRED 状态转换"""
        from src.database import PremiumOrder
        
        # 创建已过期的待支付订单
        order = PremiumOrderFactory.create(
            status="PENDING",
            created_at=datetime.now() - timedelta(hours=1),
        )
        order.expires_at = datetime.now() - timedelta(minutes=30)
        full_test_db.add(order)
        full_test_db.commit()
        
        # 模拟过期检查
        if order.expires_at < datetime.now():
            order.status = "EXPIRED"
        full_test_db.commit()
        
        # 验证状态
        saved_order = full_test_db.query(PremiumOrder).filter_by(
            order_id=order.order_id
        ).first()
        
        assert saved_order.status == "EXPIRED"


class TestOrderExpiryTask:
    """测试订单过期任务"""
    
    def test_expire_old_orders(self, full_test_db):
        """测试批量过期旧订单"""
        from src.database import PremiumOrder
        
        # 创建多个过期订单
        expired_orders = []
        for i in range(5):
            order = PremiumOrderFactory.create(
                status="PENDING",
                created_at=datetime.now() - timedelta(hours=2),
            )
            order.expires_at = datetime.now() - timedelta(hours=1)
            expired_orders.append(order)
            full_test_db.add(order)
        
        # 创建一个未过期订单
        active_order = PremiumOrderFactory.create(status="PENDING")
        active_order.expires_at = datetime.now() + timedelta(minutes=30)
        full_test_db.add(active_order)
        
        full_test_db.commit()
        
        # 模拟过期任务
        now = datetime.now()
        expired_count = full_test_db.query(PremiumOrder).filter(
            PremiumOrder.status == "PENDING",
            PremiumOrder.expires_at < now
        ).update({"status": "EXPIRED"})
        full_test_db.commit()
        
        # 验证
        assert expired_count == 5
        
        # 活跃订单应该仍然是 PENDING
        active = full_test_db.query(PremiumOrder).filter_by(
            order_id=active_order.order_id
        ).first()
        assert active.status == "PENDING"


class TestTRXExchangeOrderLifecycle:
    """测试 TRX 兑换订单生命周期"""
    
    def test_trx_order_full_lifecycle(self, full_test_db):
        """测试 TRX 订单完整生命周期"""
        from src.modules.trx_exchange.models import TRXExchangeOrder
        
        # 1. 创建订单
        order = TRXExchangeOrderFactory.create(status="PENDING")
        full_test_db.add(order)
        full_test_db.commit()
        
        assert order.status == "PENDING"
        
        # 2. 支付确认
        order.status = "PAID"
        order.receive_tx_hash = "tx_usdt_received"
        full_test_db.commit()
        
        # 3. 处理中
        order.status = "PROCESSING"
        full_test_db.commit()
        
        # 4. 完成
        order.status = "COMPLETED"
        order.send_tx_hash = "tx_trx_sent"
        order.completed_at = datetime.now()
        full_test_db.commit()
        
        # 验证最终状态
        final_order = full_test_db.query(TRXExchangeOrder).filter_by(
            order_id=order.order_id
        ).first()
        
        assert final_order.status == "COMPLETED"
        assert final_order.receive_tx_hash is not None
        assert final_order.send_tx_hash is not None

