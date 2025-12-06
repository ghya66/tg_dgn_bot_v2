"""
TronScan API 模拟响应
用于测试地址查询和交易验证功能
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal


class TronScanMockResponses:
    """TronScan API 模拟响应类"""
    
    # USDT 合约地址
    USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    
    @classmethod
    def account_info(
        cls,
        address: str = "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH",
        trx_balance: int = 1000000000,  # 1000 TRX (in sun)
        usdt_balance: str = "100000000",  # 100 USDT
    ) -> Dict[str, Any]:
        """
        模拟账户信息响应
        
        Args:
            address: 钱包地址
            trx_balance: TRX 余额（sun 单位，1 TRX = 1,000,000 sun）
            usdt_balance: USDT 余额（最小单位）
        
        Returns:
            账户信息字典
        """
        return {
            "address": address,
            "balance": trx_balance,
            "bandwidth": {
                "freeNetLimit": 600,
                "freeNetUsed": 100,
                "netLimit": 0,
                "netUsed": 0,
            },
            "trc20token_balances": [
                {
                    "tokenId": cls.USDT_CONTRACT,
                    "tokenName": "Tether USD",
                    "tokenAbbr": "USDT",
                    "tokenDecimal": 6,
                    "balance": usdt_balance,
                }
            ],
            "transactions": 150,
            "date_created": 1609459200000,  # 2021-01-01
        }
    
    @classmethod
    def account_not_found(cls, address: str) -> Dict[str, Any]:
        """模拟账户不存在的响应"""
        return {
            "address": address,
            "balance": 0,
            "bandwidth": {},
            "trc20token_balances": [],
            "transactions": 0,
        }
    
    @classmethod
    def transaction_list(
        cls,
        address: str,
        transactions: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        模拟交易列表响应
        
        Args:
            address: 钱包地址
            transactions: 交易列表，默认生成5条模拟交易
        """
        if transactions is None:
            transactions = [
                {
                    "hash": f"tx_hash_{i}",
                    "timestamp": 1700000000000 + i * 3600000,
                    "ownerAddress": address if i % 2 == 0 else "TSenderAddress123",
                    "toAddress": "TReceiverAddress123" if i % 2 == 0 else address,
                    "amount": 1000000 * (i + 1),  # TRX amount in sun
                    "confirmed": True,
                    "result": "SUCCESS",
                }
                for i in range(5)
            ]
        
        return {
            "total": len(transactions),
            "data": transactions,
        }
    
    @classmethod
    def trc20_transfer(
        cls,
        tx_hash: str,
        from_address: str,
        to_address: str,
        amount: str = "100000000",  # 100 USDT
        confirmed: bool = True,
    ) -> Dict[str, Any]:
        """模拟 TRC20 转账记录"""
        return {
            "transaction_id": tx_hash,
            "token_info": {
                "symbol": "USDT",
                "address": cls.USDT_CONTRACT,
                "decimals": 6,
            },
            "from": from_address,
            "to": to_address,
            "value": amount,
            "confirmed": confirmed,
            "block_timestamp": 1700000000000,
        }
    
    @classmethod
    def error_response(cls, code: int = 500, message: str = "Internal Server Error") -> Dict[str, Any]:
        """模拟错误响应"""
        return {
            "error": True,
            "code": code,
            "message": message,
        }
    
    @classmethod
    def rate_limit_response(cls) -> Dict[str, Any]:
        """模拟频率限制响应"""
        return cls.error_response(429, "Too Many Requests")
    
    @classmethod
    def invalid_address_response(cls) -> Dict[str, Any]:
        """模拟无效地址响应"""
        return cls.error_response(400, "Invalid address format")


# 预定义的测试地址
TEST_ADDRESSES = {
    "valid": "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH",
    "valid_2": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    "empty": "TEmptyWallet00000000000000000001",
    "invalid": "InvalidAddress123",
    "short": "TShort",
    "not_t_prefix": "ALyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH",
}

