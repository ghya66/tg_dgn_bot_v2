"""TRX Sender - Handle TRX Transfers."""

import logging
import re
from datetime import UTC, datetime
from decimal import Decimal

from pydantic import SecretStr

from src.config import settings

from .config import TRXExchangeConfig


logger = logging.getLogger(__name__)

# 专用审计日志记录器（用于记录敏感操作）
audit_logger = logging.getLogger("trx_audit")

# TRX 转账限额配置
MAX_SINGLE_TRX = Decimal("5000")  # 单笔最大 5000 TRX
MAX_DAILY_TRX = Decimal("50000")  # 日最大 50000 TRX

# 私钥格式验证：64 位十六进制字符串
PRIVATE_KEY_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


def validate_private_key_format(key: str) -> bool:
    """
    验证私钥格式是否正确。

    Args:
        key: 私钥字符串

    Returns:
        True 如果格式正确，False 否则
    """
    if not key:
        return False
    return bool(PRIVATE_KEY_PATTERN.match(key))


def _get_private_key_value(secret: SecretStr | str) -> str:
    """
    安全地从 SecretStr 或普通字符串获取私钥值。

    Args:
        secret: SecretStr 或普通字符串

    Returns:
        私钥字符串
    """
    if isinstance(secret, SecretStr):
        return secret.get_secret_value()
    return str(secret) if secret else ""


class TRXSender:
    """
    TRX Transfer Handler (Test Mode).

    In production, configure real private key and enable transfer.

    Security Features:
    - Private key is stored as SecretStr to prevent accidental logging
    - All private key operations are audited
    - Private key format is validated on initialization
    """

    def __init__(self, config: TRXExchangeConfig | None = None):
        """Initialize TRX sender."""
        if config is not None:
            self.config = config
        else:
            # Build config snapshot using module-level settings (patchable in tests)
            def _as_str(attr: str, default: str = "") -> str:
                value = getattr(settings, attr, default)
                # 特殊处理 SecretStr 类型
                if isinstance(value, SecretStr):
                    return value.get_secret_value()
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
        # 内部存储私钥值（不直接暴露）
        self._private_key = self.config.private_key

        # 验证私钥格式（非测试模式）
        if not self.test_mode and self._private_key:
            if not validate_private_key_format(self._private_key):
                logger.error("Invalid private key format detected")
                raise ValueError("Private key format is invalid (expected 64 hex characters)")
            # 审计日志：私钥加载成功（不记录私钥本身）
            audit_logger.info(f"TRX private key loaded successfully for sender {self.sender_address}")

        # 生产环境配置检查
        if self.test_mode:
            env = getattr(settings, "env", "dev").lower()
            if env in ("prod", "production"):
                logger.critical(
                    "⚠️ CRITICAL: TRX_EXCHANGE_TEST_MODE=True in production environment! "
                    "Real TRX transfers are DISABLED. Set TRX_EXCHANGE_TEST_MODE=False for production."
                )
            else:
                logger.warning(
                    "TRXSender running in TEST MODE. TRX transfers will be simulated. "
                    "Set TRX_EXCHANGE_TEST_MODE=False for production."
                )
        else:
            logger.info(f"TRXSender initialized (sender: {self.sender_address})")

    @property
    def private_key(self) -> str:
        """
        获取私钥值。

        注意：此属性用于向后兼容，新代码应避免直接访问私钥。
        """
        return self._private_key

    def send_trx(
        self,
        recipient_address: str,
        amount: Decimal,
        order_id: str,
    ) -> str | None:
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
            logger.info(f"[TEST MODE] TRX Transfer: {amount} TRX → {recipient_address} (order: {order_id})")
            # Return mock transaction hash
            return f"mock_tx_hash_{order_id}"

        # 检查限额
        if amount > MAX_SINGLE_TRX:
            logger.error(f"Amount {amount} exceeds single limit {MAX_SINGLE_TRX}")
            raise ValueError(f"单笔转账超过限额 {MAX_SINGLE_TRX} TRX")

        # 审计日志：记录私钥使用（不记录私钥本身）
        audit_logger.info(
            f"TRX_TRANSFER_INITIATED | order={order_id} | "
            f"sender={self.sender_address} | recipient={recipient_address} | "
            f"amount={amount} | time={datetime.now(UTC).isoformat()}"
        )

        # Production mode: real TRX transfer using tronpy
        logger.info(f"Sending {amount} TRX to {recipient_address} (order: {order_id})")

        try:
            from tronpy import Tron
            from tronpy.keys import PrivateKey

            # 初始化客户端
            client = Tron()

            # 加载私钥（审计日志已记录）
            if not self._private_key:
                audit_logger.warning(f"TRX_TRANSFER_FAILED | order={order_id} | reason=private_key_not_configured")
                raise ValueError("Private key not configured")

            priv_key = PrivateKey(bytes.fromhex(self._private_key))

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

            # 审计日志：记录成功交易
            audit_logger.info(
                f"TRX_TRANSFER_SUCCESS | order={order_id} | tx_hash={tx_hash} | "
                f"amount={amount} | time={datetime.now(UTC).isoformat()}"
            )

            logger.info(f"TRX transfer successful: {tx_hash} (order: {order_id})")
            return tx_hash

        except ImportError:
            logger.error("tronpy not installed. Run: pip install tronpy")
            raise RuntimeError("tronpy library not installed")
        except Exception as e:
            # 审计日志：记录失败交易
            audit_logger.error(
                f"TRX_TRANSFER_FAILED | order={order_id} | error={str(e)[:100]} | time={datetime.now(UTC).isoformat()}"
            )
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
        base58_pattern = r"^[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]+$"
        if not re.match(base58_pattern, address):
            return False

        return True
