"""TRX Sender - Handle TRX Transfers."""

import logging
import re
from decimal import Decimal
from typing import Optional

from .config import TRXExchangeConfig
from src.config import settings

logger = logging.getLogger(__name__)

# TRX 转账限额配置
MAX_SINGLE_TRX = Decimal("5000")    # 单笔最大 5000 TRX
MAX_DAILY_TRX = Decimal("50000")    # 日最大 50000 TRX


class TRXSender:
    """
    TRX Transfer Handler (Test Mode).

    In production, configure real private key and enable transfer.
    """

    def __init__(self, config: Optional[TRXExchangeConfig] = None):
        """Initialize TRX sender."""
        if config is not None:
            self.config = config
        else:
            # Build config snapshot using module-level settings (patchable in tests)
            def _as_str(attr: str, default: str = "") -> str:
                value = getattr(settings, attr, default)
                return str(value) if value is not None else default

            def _as_decimal(attr: str, default: Decimal = Decimal("0")) -> Decimal:
                value = getattr(settings, attr, default)
                try:
                    return Decimal(str(value))
                except Exception:
                    return default

            self.config = TRXExchangeConfig(
                receive_address=_as_str("trx_exchange_receive_address"),
                send_address=_as_str("trx_exchange_send_address"),
                private_key=_as_str("trx_exchange_private_key"),
                qrcode_file_id=_as_str("trx_exchange_qrcode_file_id"),
                default_rate=_as_decimal("trx_exchange_default_rate"),
                test_mode=bool(getattr(settings, "trx_exchange_test_mode", True)),
            )
        self.test_mode = self.config.test_mode
        self.sender_address = self.config.send_address
        self.private_key = self.config.private_key

        if self.test_mode:
            logger.info("TRXSender initialized in TEST MODE (no real transfers)")
        else:
            logger.info(f"TRXSender initialized (sender: {self.sender_address})")

    def send_trx(
        self,
        recipient_address: str,
        amount: Decimal,
        order_id: str,
    ) -> Optional[str]:
        """
        Send TRX to recipient address.

        Args:
            recipient_address: User's TRX receiving address
            amount: TRX amount to send (e.g., Decimal('30.500000'))
            order_id: Order ID for logging

        Returns:
            Transaction hash if successful, None if failed

        Raises:
            Exception: If transfer fails (network error, insufficient balance, etc.)
        """
        if self.test_mode:
            logger.info(
                f"[TEST MODE] TRX Transfer: {amount} TRX → {recipient_address} (order: {order_id})"
            )
            # Return mock transaction hash
            return f"mock_tx_hash_{order_id}"

        # 检查限额
        if amount > MAX_SINGLE_TRX:
            logger.error(f"Amount {amount} exceeds single limit {MAX_SINGLE_TRX}")
            raise ValueError(f"单笔转账超过限额 {MAX_SINGLE_TRX} TRX")
        
        # Production mode: real TRX transfer using tronpy
        logger.info(f"Sending {amount} TRX to {recipient_address} (order: {order_id})")

        try:
            from tronpy import Tron
            from tronpy.keys import PrivateKey
            
            # 初始化客户端
            client = Tron()
            
            # 加载私钥
            if not self.private_key:
                raise ValueError("Private key not configured")
            
            priv_key = PrivateKey(bytes.fromhex(self.private_key))
            
            # 构建交易（金额单位：sun，1 TRX = 1,000,000 sun）
            amount_sun = int(amount * Decimal("1000000"))
            
            txn = (
                client.trx.transfer(self.sender_address, recipient_address, amount_sun)
                .memo(f"TRX Exchange Order: {order_id}")
                .build()
                .sign(priv_key)
            )
            
            # 广播交易
            result = txn.broadcast().wait()
            tx_hash = result.get("id") or result.get("txid")
            
            logger.info(f"TRX transfer successful: {tx_hash} (order: {order_id})")
            return tx_hash

        except ImportError:
            logger.error("tronpy not installed. Run: pip install tronpy")
            raise RuntimeError("tronpy library not installed")
        except Exception as e:
            logger.error(f"TRX transfer failed (order: {order_id}): {e}", exc_info=True)
            raise

    def validate_address(self, address: str) -> bool:
        """
        Validate TRX address format.

        Args:
            address: TRX address to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation: T prefix + 34 characters
        if not address or len(address) != 34 or not address.startswith("T"):
            return False

        # Check Base58 character set
        base58_pattern = r'^[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]+$'
        if not re.match(base58_pattern, address):
            return False

        return True
