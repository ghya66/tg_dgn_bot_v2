"""
TRC20 Webhook 回调处理器
路由：POST /webhook/trc20
验证 HMAC 签名、解析 JSON、金额匹配后更新订单状态
支持 Premium 订单的自动交付

安全特性：
- HMAC 签名验证
- 时间戳窗口验证（60秒）
- 交易哈希防重放（Redis 缓存）
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import time
import re
import hashlib

from ..models import PaymentCallback, OrderStatus, OrderType
from ..signature import signature_validator
from ..payments.order import order_manager
from ..payments.amount_calculator import AmountCalculator
from ..config import settings
from ..common.redis_helper import create_redis_client

# 配置日志
logger = logging.getLogger(__name__)

# 安全配置
WEBHOOK_TIMESTAMP_WINDOW_SECONDS = 60  # 时间戳验证窗口（秒）
WEBHOOK_NONCE_TTL_SECONDS = 300  # nonce 缓存 TTL（秒），防止重放
WEBHOOK_NONCE_PREFIX = "webhook_nonce:"  # Redis key 前缀


class TRC20Handler:
    """TRC20回调处理器"""

    def __init__(self, delivery_service=None, db_session=None):
        """
        初始化处理器

        Args:
            delivery_service: Premium 交付服务实例（可选）
            db_session: 数据库会话（可选，用于测试）
        """
        self.delivery_service = delivery_service
        self.db_session = db_session
        self._redis_client = None

    async def _get_redis_client(self):
        """获取或创建 Redis 客户端"""
        if self._redis_client is None:
            self._redis_client = create_redis_client()
        return self._redis_client

    async def _check_and_set_nonce(self, txid: str, order_id: str) -> bool:
        """
        检查并设置 nonce（防重放）

        使用 txid + order_id 的组合作为 nonce，确保同一交易不会被重复处理。

        Args:
            txid: 交易哈希
            order_id: 订单 ID

        Returns:
            True 如果是新的 nonce（可以处理），False 如果已存在（重放攻击）
        """
        try:
            redis = await self._get_redis_client()
            # 使用 txid 和 order_id 的组合作为 nonce
            nonce = hashlib.sha256(f"{txid}:{order_id}".encode()).hexdigest()[:32]
            key = f"{WEBHOOK_NONCE_PREFIX}{nonce}"

            # 使用 SETNX（SET if Not eXists）+ EXPIRE 原子操作
            # 如果 key 不存在，设置成功返回 True；如果已存在，返回 False
            result = await redis.set(
                key,
                f"{txid}:{order_id}:{int(time.time())}",
                nx=True,  # 只在 key 不存在时设置
                ex=WEBHOOK_NONCE_TTL_SECONDS  # 设置过期时间
            )

            if result:
                logger.debug(f"Nonce 设置成功: {nonce[:8]}... (txid={txid[:16]}...)")
                return True
            else:
                logger.warning(f"检测到重放攻击: nonce={nonce[:8]}... txid={txid[:16]}... order={order_id}")
                return False

        except Exception as e:
            # Redis 不可用时，记录警告但允许请求通过（降级策略）
            logger.warning(f"Nonce 检查失败，降级放行: {e}")
            return True

    @staticmethod
    def validate_tron_address(address: str) -> bool:
        """
        验证波场地址格式
        
        Args:
            address: 波场地址
            
        Returns:
            是否为有效的波场地址
        """
        # 波场地址以T开头，长度为34位，包含Base58字符
        tron_pattern = r'^T[A-HJ-NP-Z1-9a-km-z]{33}$'
        return bool(re.match(tron_pattern, address))
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理TRC20支付回调

        安全验证流程：
        1. 验证必需字段
        2. 验证时间戳窗口（60秒）
        3. 验证签名
        4. 检查 nonce 防重放
        5. 处理支付

        Args:
            payload: 回调数据

        Returns:
            处理结果
        """
        try:
            # 验证必需字段
            required_fields = ["order_id", "amount", "txid", "timestamp", "signature"]
            for field in required_fields:
                if field not in payload:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }

            # 验证时间戳窗口（在签名验证之前，减少计算开销）
            timestamp = payload.get("timestamp")
            if isinstance(timestamp, int):
                current_time = int(time.time())
                time_diff = abs(current_time - timestamp)
                if time_diff > WEBHOOK_TIMESTAMP_WINDOW_SECONDS:
                    logger.warning(
                        f"时间戳超出窗口: order={payload.get('order_id')}, "
                        f"timestamp={timestamp}, current={current_time}, diff={time_diff}s"
                    )
                    return {
                        "success": False,
                        "error": f"Timestamp out of valid window ({WEBHOOK_TIMESTAMP_WINDOW_SECONDS}s)"
                    }

            # 提取签名
            signature = payload.pop("signature")

            # 验证签名
            if not signature_validator.verify_signature(payload, signature):
                logger.warning(f"Invalid signature for order {payload.get('order_id')}")
                return {
                    "success": False,
                    "error": "Invalid signature"
                }

            # 检查 nonce 防重放（签名验证通过后再检查，避免无效请求消耗 Redis 资源）
            txid = payload["txid"]
            order_id = payload["order_id"]
            if not await self._check_and_set_nonce(txid, order_id):
                return {
                    "success": False,
                    "error": "Duplicate callback detected (replay attack prevention)"
                }

            # 创建回调对象
            callback = PaymentCallback(
                order_id=order_id,
                amount=payload["amount"],
                tx_hash=txid,
                block_number=payload.get("block_number", 0),
                timestamp=timestamp,
                signature=signature,
                order_type=payload.get("order_type")
            )

            # 处理支付确认
            result = await self._process_payment(callback)
            
            logger.info(f"Processed payment callback for order {callback.order_id}: {result}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return {
                "success": False,
                "error": "Internal server error"
            }
    
    async def _process_payment(self, callback: PaymentCallback) -> Dict[str, Any]:
        """
        处理支付确认
        
        Args:
            callback: 支付回调数据
            
        Returns:
            处理结果
        """
        try:
            # 检查订单类型：如果是 deposit，走充值流程
            if callback.order_type == "deposit":
                return await self._process_deposit_payment(callback)
            
            # 否则走普通订单流程（Premium等）
            # 查找匹配的订单
            order = await order_manager.find_order_by_amount(callback.amount)
            
            if not order:
                return {
                    "success": False,
                    "error": "Order not found for amount",
                    "order_id": callback.order_id
                }
            
            # 验证订单ID是否匹配
            if order.order_id != callback.order_id:
                return {
                    "success": False,
                    "error": "Order ID mismatch",
                    "expected": order.order_id,
                    "received": callback.order_id
                }
            
            # 验证金额是否精确匹配
            if not AmountCalculator.verify_amount(order.total_amount, callback.amount):
                return {
                    "success": False,
                    "error": "Amount mismatch",
                    "expected": order.total_amount,
                    "received": callback.amount
                }
            
            # 检查订单是否已过期
            if order.is_expired:
                await order_manager.update_order_status(order.order_id, OrderStatus.EXPIRED)
                return {
                    "success": False,
                    "error": "Order expired",
                    "order_id": order.order_id
                }
            
            # 更新订单状态为已支付（幂等操作）
            success = await order_manager.update_order_status(
                order.order_id, 
                OrderStatus.PAID,
                callback.tx_hash
            )
            
            if not success:
                return {
                    "success": False,
                    "error": "Failed to update order status",
                    "order_id": order.order_id
                }
            
            # 如果是 Premium 订单，自动触发交付
            delivery_result = None
            if order.order_type == OrderType.PREMIUM and self.delivery_service:
                try:
                    # 获取 Premium 订单详情
                    from src.database import PremiumOrder
                    from src.common.db_manager import get_db_context

                    with get_db_context() as db:
                        premium_order = db.query(PremiumOrder).filter(
                            PremiumOrder.order_id == order.order_id
                        ).first()

                        if premium_order:
                            # 更新状态为已支付
                            premium_order.status = 'PAID'
                            premium_order.paid_at = datetime.now()
                            premium_order.tx_hash = callback.tx_hash
                            db.commit()

                            # 自动发货
                            delivery_result = await self.delivery_service.deliver_premium(
                                order_id=order.order_id,
                                buyer_id=premium_order.buyer_id,
                                recipient_username=premium_order.recipient_username,
                                recipient_id=premium_order.recipient_id,
                                premium_months=premium_order.premium_months
                            )
                            logger.info(f"Premium delivery result for order {order.order_id}: {delivery_result}")
                        else:
                            logger.error(f"Premium order not found: {order.order_id}")
                except Exception as e:
                    logger.error(f"Failed to deliver premium for order {order.order_id}: {e}")
            
            return {
                "success": True,
                "message": "Payment processed successfully",
                "order_id": order.order_id,
                "tx_hash": callback.tx_hash,
                "delivery_result": delivery_result
            }
        
        except Exception as e:
            logger.error(f"Error processing payment for order {callback.order_id}: {str(e)}")
            return {
                "success": False,
                "error": f"Processing error: {str(e)}",
                "order_id": callback.order_id
            }
    
    async def _process_deposit_payment(self, callback: PaymentCallback) -> Dict[str, Any]:
        """
        处理充值订单支付

        Args:
            callback: 支付回调数据

        Returns:
            处理结果
        """
        try:
            from ..wallet.wallet_manager import WalletManager
            from src.common.db_manager import get_db_context

            # 使用注入的数据库会话或创建新的
            if self.db_session:
                wallet = WalletManager(db=self.db_session)
                success, message = wallet.process_deposit_callback(
                    order_id=callback.order_id,
                    amount=callback.amount,
                    tx_hash=callback.tx_hash
                )
            else:
                with get_db_context() as db:
                    wallet = WalletManager(db=db)
                    success, message = wallet.process_deposit_callback(
                        order_id=callback.order_id,
                        amount=callback.amount,
                        tx_hash=callback.tx_hash
                    )
            
            if success:
                return {
                    "success": True,
                    "message": message,
                    "order_id": callback.order_id,
                    "tx_hash": callback.tx_hash,
                    "order_type": "deposit"
                }
            else:
                return {
                    "success": False,
                    "error": message,
                    "order_id": callback.order_id,
                    "order_type": "deposit"
                }
        
        except Exception as e:
            logger.error(f"Error processing deposit payment for order {callback.order_id}: {str(e)}")
            return {
                "success": False,
                "error": f"Deposit processing error: {str(e)}",
                "order_id": callback.order_id,
                "order_type": "deposit"
            }
    
    async def simulate_payment(self, order_id: str, tx_hash: str = None) -> Dict[str, Any]:
        """
        模拟支付回调（用于测试）
        
        Args:
            order_id: 订单ID
            tx_hash: 交易哈希（可选）
            
        Returns:
            模拟结果
        """
        try:
            # 获取订单信息
            order = await order_manager.get_order(order_id)
            if not order:
                return {
                    "success": False,
                    "error": "Order not found",
                    "order_id": order_id
                }
            
            # 生成模拟交易哈希
            if not tx_hash:
                tx_hash = f"test_tx_{int(time.time())}_{order_id[:8]}"
            
            # 创建签名的回调数据
            callback_data = signature_validator.create_signed_callback(
                order_id=order_id,
                amount=order.total_amount,
                tx_hash=tx_hash,
                block_number=int(time.time()),  # 使用时间戳作为块号
                timestamp=int(time.time())
            )
            
            # 处理回调
            result = await self.handle_webhook(callback_data)
            
            result["simulation"] = True
            result["callback_data"] = callback_data
            
            return result
        
        except Exception as e:
            logger.error(f"Error simulating payment: {str(e)}")
            return {
                "success": False,
                "error": f"Simulation error: {str(e)}",
                "order_id": order_id
            }
    
    @staticmethod
    def validate_webhook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证webhook载荷格式
        
        Args:
            payload: 载荷数据
            
        Returns:
            验证结果
        """
        errors = []
        
        # 检查必需字段
        required_fields = {
            "order_id": str,
            "amount": (int, float),
            "txid": str,
            "timestamp": int,
            "signature": str
        }
        
        for field, expected_type in required_fields.items():
            if field not in payload:
                errors.append(f"Missing field: {field}")
            elif not isinstance(payload[field], expected_type):
                # 处理元组类型（如 (int, float)）的显示
                if isinstance(expected_type, tuple):
                    type_names = " or ".join(t.__name__ for t in expected_type)
                    errors.append(f"Invalid type for {field}: expected {type_names}")
                else:
                    errors.append(f"Invalid type for {field}: expected {expected_type.__name__}")
        
        # 验证金额范围
        if "amount" in payload:
            amount = payload["amount"]
            # 只有在类型正确时才验证金额范围
            if isinstance(amount, (int, float)):
                if not AmountCalculator.is_valid_payment_amount(amount):
                    errors.append(f"Invalid payment amount: {amount}")
        
        # 验证交易哈希格式
        if "txid" in payload:
            txid = payload["txid"]
            if not isinstance(txid, str) or len(txid) < 10:
                errors.append(f"Invalid transaction hash: {txid}")
        
        # 验证时间戳（使用配置的时间窗口）
        if "timestamp" in payload:
            timestamp = payload["timestamp"]
            # 只有在类型正确时才验证时间戳
            if isinstance(timestamp, int):
                current_time = int(time.time())
                time_diff = abs(current_time - timestamp)
                # 使用配置的时间窗口（默认60秒）
                if time_diff > WEBHOOK_TIMESTAMP_WINDOW_SECONDS:
                    errors.append(
                        f"Timestamp out of valid window: diff={time_diff}s, "
                        f"max={WEBHOOK_TIMESTAMP_WINDOW_SECONDS}s"
                    )
        
        if errors:
            return {
                "valid": False,
                "errors": errors
            }
        
        return {
            "valid": True,
            "errors": []
        }


# 创建全局实例（需要在初始化时传入 delivery_service）
_handler_instance = None

def get_trc20_handler(delivery_service=None):
    """获取或创建全局 TRC20 处理器实例"""
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = TRC20Handler(delivery_service)
    return _handler_instance