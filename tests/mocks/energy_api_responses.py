"""
Energy API (trxfast.com) 模拟响应
用于测试能量兑换功能
"""
from typing import Dict, Any, Optional
from decimal import Decimal


class EnergyAPIMockResponses:
    """Energy API 模拟响应类"""
    
    @classmethod
    def account_info(
        cls,
        username: str = "test_user",
        balance_trx: Decimal = Decimal("1000.00"),
        balance_usdt: Decimal = Decimal("500.00"),
        frozen_balance: Decimal = Decimal("0.00"),
    ) -> Dict[str, Any]:
        """
        模拟账户信息响应
        
        Args:
            username: 用户名
            balance_trx: TRX 余额
            balance_usdt: USDT 余额
            frozen_balance: 冻结余额
        """
        return {
            "code": 0,
            "message": "success",
            "data": {
                "username": username,
                "balance_trx": str(balance_trx),
                "balance_usdt": str(balance_usdt),
                "frozen_balance": str(frozen_balance),
                "vip_level": 1,
            }
        }
    
    @classmethod
    def price_query(
        cls,
        energy_65k_price: Decimal = Decimal("3.00"),
        energy_131k_price: Decimal = Decimal("6.00"),
        package_price: Decimal = Decimal("3.60"),
    ) -> Dict[str, Any]:
        """
        模拟价格查询响应
        
        Args:
            energy_65k_price: 6.5万能量价格（TRX）
            energy_131k_price: 13.1万能量价格（TRX）
            package_price: 笔数套餐单价（TRX/笔）
        """
        return {
            "code": 0,
            "message": "success",
            "data": {
                "energy_65k_price": str(energy_65k_price),
                "energy_131k_price": str(energy_131k_price),
                "package_price": str(package_price),
                "min_package_amount": 5,
                "max_package_amount": 1000,
            }
        }
    
    @classmethod
    def order_create_success(
        cls,
        order_id: str,
        energy_amount: int = 65000,
        price: Decimal = Decimal("3.00"),
    ) -> Dict[str, Any]:
        """模拟订单创建成功响应"""
        return {
            "code": 0,
            "message": "success",
            "data": {
                "order_id": order_id,
                "energy_amount": energy_amount,
                "price": str(price),
                "status": "processing",
                "estimated_time": 60,  # 预计完成时间（秒）
            }
        }
    
    @classmethod
    def order_status(
        cls,
        order_id: str,
        status: str = "completed",
        tx_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """模拟订单状态查询响应"""
        return {
            "code": 0,
            "message": "success",
            "data": {
                "order_id": order_id,
                "status": status,
                "tx_hash": tx_hash or f"tx_{order_id}",
                "completed_at": "2024-01-01T12:00:00Z" if status == "completed" else None,
            }
        }
    
    @classmethod
    def error_response(
        cls,
        code: int = 1001,
        message: str = "API Error",
    ) -> Dict[str, Any]:
        """模拟错误响应"""
        return {
            "code": code,
            "message": message,
            "data": None,
        }
    
    @classmethod
    def insufficient_balance(cls) -> Dict[str, Any]:
        """模拟余额不足响应"""
        return cls.error_response(1002, "Insufficient balance")
    
    @classmethod
    def invalid_address(cls) -> Dict[str, Any]:
        """模拟无效地址响应"""
        return cls.error_response(1003, "Invalid address format")
    
    @classmethod
    def rate_limit(cls) -> Dict[str, Any]:
        """模拟频率限制响应"""
        return cls.error_response(1004, "Rate limit exceeded")
    
    @classmethod
    def server_error(cls) -> Dict[str, Any]:
        """模拟服务器错误响应"""
        return cls.error_response(5000, "Internal server error")
    
    @classmethod
    def network_timeout(cls) -> Dict[str, Any]:
        """模拟网络超时响应"""
        return cls.error_response(5001, "Network timeout")


# 预定义的测试场景
TEST_SCENARIOS = {
    "success": {
        "account": EnergyAPIMockResponses.account_info(),
        "price": EnergyAPIMockResponses.price_query(),
    },
    "low_balance": {
        "account": EnergyAPIMockResponses.account_info(
            balance_trx=Decimal("1.00"),
            balance_usdt=Decimal("0.50"),
        ),
    },
    "error": {
        "server_error": EnergyAPIMockResponses.server_error(),
        "rate_limit": EnergyAPIMockResponses.rate_limit(),
    },
}

