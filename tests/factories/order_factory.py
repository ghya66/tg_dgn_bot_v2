"""
订单数据工厂
生成测试用的各类订单数据
"""
import uuid
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional


class OrderFactory:
    """通用订单工厂基类"""
    
    @staticmethod
    def generate_order_id(prefix: str = "ORD") -> str:
        """生成订单ID"""
        return f"{prefix}_{uuid.uuid4().hex[:16].upper()}"
    
    @staticmethod
    def generate_suffix() -> int:
        """生成3位数后缀（1-999）"""
        return random.randint(1, 999)


class PremiumOrderFactory(OrderFactory):
    """Premium 订单工厂"""
    
    # 套餐价格（USDT）
    PACKAGES = {
        3: Decimal("17.00"),
        6: Decimal("25.00"),
        12: Decimal("40.00"),
    }
    
    @classmethod
    def create(
        cls,
        buyer_id: int = 123456789,
        recipient_id: Optional[int] = None,
        recipient_username: str = "recipient_user",
        recipient_type: str = "self",
        premium_months: int = 3,
        status: str = "PENDING",
        tx_hash: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        """
        创建 Premium 订单
        
        Args:
            buyer_id: 购买者ID
            recipient_id: 接收者ID（默认与购买者相同）
            recipient_username: 接收者用户名
            recipient_type: 接收者类型 (self/other)
            premium_months: 会员月数 (3/6/12)
            status: 订单状态
            tx_hash: 交易哈希
            created_at: 创建时间
        
        Returns:
            PremiumOrder: 订单对象
        """
        from src.database import PremiumOrder
        
        if recipient_id is None:
            recipient_id = buyer_id if recipient_type == "self" else cls.generate_order_id("USER")
        
        base_amount = cls.PACKAGES.get(premium_months, Decimal("17.00"))
        suffix = cls.generate_suffix()
        total_amount = base_amount + Decimal(f"0.{suffix:03d}")
        
        return PremiumOrder(
            order_id=cls.generate_order_id("PREM"),
            buyer_id=buyer_id,
            recipient_id=recipient_id,
            recipient_username=recipient_username,
            recipient_type=recipient_type,
            premium_months=premium_months,
            amount_usdt=int(total_amount * 1_000_000),  # 转换为微USDT
            status=status,
            tx_hash=tx_hash,
            created_at=created_at or datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=30),
        )
    
    @classmethod
    def create_pending(cls, **kwargs):
        """创建待支付订单"""
        return cls.create(status="PENDING", **kwargs)
    
    @classmethod
    def create_completed(cls, **kwargs):
        """创建已完成订单"""
        return cls.create(
            status="COMPLETED",
            tx_hash=f"tx_{uuid.uuid4().hex[:32]}",
            **kwargs
        )
    
    @classmethod
    def create_expired(cls, **kwargs):
        """创建已过期订单"""
        return cls.create(
            status="EXPIRED",
            created_at=datetime.now() - timedelta(hours=1),
            **kwargs
        )


class EnergyOrderFactory(OrderFactory):
    """Energy 订单工厂"""
    
    ORDER_TYPES = ["hourly", "package", "flash"]
    
    @classmethod
    def create(
        cls,
        user_id: int = 123456789,
        order_type: str = "hourly",
        energy_amount: int = 65000,
        receive_address: str = "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH",
        status: str = "PENDING",
        created_at: Optional[datetime] = None,
    ):
        """创建 Energy 订单"""
        from src.database import EnergyOrder
        
        return EnergyOrder(
            order_id=cls.generate_order_id("ENGY"),
            user_id=user_id,
            order_type=order_type,
            energy_amount=energy_amount,
            receive_address=receive_address,
            status=status,
            created_at=created_at or datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=30),
        )


class TRXExchangeOrderFactory(OrderFactory):
    """TRX 兑换订单工厂"""

    DEFAULT_RATE = Decimal("7.14")  # 1 USDT = 7.14 TRX
    DEFAULT_PAYMENT_ADDRESS = "TPaymentAddress123456789012345678"

    @classmethod
    def create(
        cls,
        user_id: int = 123456789,
        usdt_amount: Decimal = Decimal("100.00"),
        exchange_rate: Optional[Decimal] = None,
        recipient_address: str = "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH",
        payment_address: Optional[str] = None,
        status: str = "PENDING",
        created_at: Optional[datetime] = None,
    ):
        """创建 TRX 兑换订单"""
        from src.modules.trx_exchange.models import TRXExchangeOrder

        rate = exchange_rate or cls.DEFAULT_RATE
        suffix = cls.generate_suffix()
        unique_usdt = usdt_amount + Decimal(f"0.{suffix:03d}")
        trx_amount = unique_usdt * rate

        return TRXExchangeOrder(
            order_id=cls.generate_order_id("TRX"),
            user_id=user_id,
            usdt_amount=unique_usdt,
            trx_amount=trx_amount.quantize(Decimal("0.000001")),
            exchange_rate=rate,
            recipient_address=recipient_address,
            payment_address=payment_address or cls.DEFAULT_PAYMENT_ADDRESS,
            status=status,
            created_at=created_at or datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=30),
        )

