"""TRX Exchange Order Models."""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DECIMAL, DateTime

from src.database import Base


class TRXExchangeOrder(Base):
    """TRX Exchange Order Model."""

    __tablename__ = "trx_exchange_orders"

    order_id = Column(String(32), primary_key=True, comment="Order ID")
    user_id = Column(Integer, nullable=False, index=True, comment="Telegram User ID")
    usdt_amount = Column(DECIMAL(10, 3), nullable=False, comment="USDT Amount (with 3-decimal suffix)")
    trx_amount = Column(DECIMAL(20, 6), nullable=False, comment="TRX Amount to Transfer")
    exchange_rate = Column(DECIMAL(10, 6), nullable=False, comment="TRX/USDT Rate (locked)")
    recipient_address = Column(String(64), nullable=False, comment="User's TRX Receiving Address")
    payment_address = Column(String(64), nullable=False, comment="Bot's USDT Receiving Address")
    status = Column(
        String(20),
        nullable=False,
        default="PENDING",
        comment="Order Status: PENDING/PAID/PROCESSING/COMPLETED/SEND_FAILED/EXPIRED",
    )
    tx_hash = Column(String(128), nullable=True, comment="User's USDT Payment Transaction Hash")
    send_tx_hash = Column(String(128), nullable=True, comment="Bot's TRX Transfer Transaction Hash")
    error_message = Column(String(512), nullable=True, comment="Error message if failed")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    paid_at = Column(DateTime, nullable=True, comment="Payment Received Time")
    completed_at = Column(DateTime, nullable=True, comment="TRX Sent Time")
    expires_at = Column(DateTime, nullable=True, comment="Order expiration timestamp (UTC)")

    def __repr__(self):
        return (
            f"<TRXExchangeOrder(order_id={self.order_id}, "
            f"user_id={self.user_id}, "
            f"usdt={self.usdt_amount}, "
            f"trx={self.trx_amount}, "
            f"status={self.status})>"
        )
