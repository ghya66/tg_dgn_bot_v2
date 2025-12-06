"""
能量兑换数据模型
定义订单类型、套餐、订单状态等数据结构
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EnergyOrderType(str, Enum):
    """能量订单类型"""

    HOURLY = "hourly"  # 时长能量（1小时）
    PACKAGE = "package"  # 笔数套餐
    FLASH = "flash"  # 闪兑


class EnergyPackage(str, Enum):
    """能量套餐类型"""

    SMALL = "65000"  # 6.5万能量
    LARGE = "131000"  # 13.1万能量


class EnergyOrderStatus(str, Enum):
    """订单状态"""

    PENDING = "pending"  # 待支付
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    EXPIRED = "expired"  # 已过期


class EnergyPriceConfig(BaseModel):
    """能量价格配置"""

    model_config = ConfigDict(from_attributes=True)

    small_energy_price: float = Field(3.0, description="6.5万能量价格(TRX)")
    large_energy_price: float = Field(6.0, description="13.1万能量价格(TRX)")
    package_price_per_tx: float = Field(3.6, description="笔数套餐每笔价格(TRX)")
    package_min_usdt: float = Field(5.0, description="笔数套餐最低USDT购买金额")
    max_purchases: int = Field(20, description="一次最大购买笔数")


class EnergyOrder(BaseModel):
    """能量订单模型"""

    model_config = ConfigDict(from_attributes=True)

    order_id: str = Field(..., description="订单ID")
    user_id: int = Field(..., description="用户TG ID")
    order_type: EnergyOrderType = Field(..., description="订单类型")

    # 时长能量字段
    energy_amount: int | None = Field(None, description="能量数量(65000/131000)")
    purchase_count: int | None = Field(None, description="购买笔数(1-20)")

    # 笔数套餐字段
    package_count: int | None = Field(None, description="套餐笔数")

    # 闪兑字段
    usdt_amount: float | None = Field(None, description="USDT金额")

    # 通用字段
    receive_address: str = Field(..., description="接收地址")
    total_price_trx: float | None = Field(None, description="总价(TRX)")
    total_price_usdt: float | None = Field(None, description="总价(USDT)")

    status: EnergyOrderStatus = Field(EnergyOrderStatus.PENDING, description="订单状态")
    api_order_id: str | None = Field(None, description="API订单ID")
    error_message: str | None = Field(None, description="错误信息")

    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: datetime | None = Field(None, description="完成时间")


class APIAccountInfo(BaseModel):
    """API账号信息"""

    model_config = ConfigDict(from_attributes=True)

    username: str = Field(..., description="用户名")
    balance_trx: float = Field(..., description="TRX余额")
    balance_usdt: float = Field(0.0, description="USDT余额")
    frozen_balance: float = Field(0.0, description="冻结余额")


class APIPriceQuery(BaseModel):
    """API价格查询响应"""

    model_config = ConfigDict(from_attributes=True)

    energy_65k_price: float = Field(..., description="6.5万能量价格(TRX)")
    energy_131k_price: float = Field(..., description="13.1万能量价格(TRX)")
    package_price: float = Field(..., description="笔数套餐价格(TRX)")


class APIOrderResponse(BaseModel):
    """API订单响应"""

    model_config = ConfigDict(from_attributes=True)

    code: int = Field(..., description="状态码")
    msg: str = Field(..., description="消息")
    data: dict | None = Field(None, description="数据")
    order_id: str | None = Field(None, description="订单ID")
