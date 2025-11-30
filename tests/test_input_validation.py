"""
用户输入验证测试
"""

import pytest


class TestAddressValidation:
    """地址验证测试"""
    
    def test_valid_tron_address(self):
        """测试有效波场地址"""
        from src.modules.address_query.validator import AddressValidator
        
        valid_addresses = [
            "TJCnKsPa7y5okkXvQAidZBzqx3QyQ6sxMW",  # Tronscan 示例
            "TN3W4H6rK2ce4vX9YnFQHwKENnHjoxb3m9",
            "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",  # USDT 合约
        ]
        
        for addr in valid_addresses:
            is_valid, error = AddressValidator.validate(addr)
            assert is_valid, f"地址 {addr} 应有效，但返回错误: {error}"
        
        print(f"✅ {len(valid_addresses)} 个有效地址验证通过")
    
    def test_invalid_address_empty(self):
        """测试空地址"""
        from src.modules.address_query.validator import AddressValidator
        
        is_valid, error = AddressValidator.validate("")
        assert not is_valid, "空地址应无效"
        assert "不能为空" in error
        
        print("✅ 空地址正确拒绝")
    
    def test_invalid_address_wrong_prefix(self):
        """测试错误前缀"""
        from src.modules.address_query.validator import AddressValidator
        
        invalid_addresses = [
            "0x742d35Cc6634C0532925a3b844Bc9e7595f",  # ETH 格式
            "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",  # BTC 格式
            "AJCnKsPa7y5okkXvQAidZBzqx3QyQ6sxMW",  # A 开头
        ]
        
        for addr in invalid_addresses:
            is_valid, error = AddressValidator.validate(addr)
            assert not is_valid, f"地址 {addr} 应无效"
        
        print(f"✅ {len(invalid_addresses)} 个错误前缀地址正确拒绝")
    
    def test_invalid_address_wrong_length(self):
        """测试错误长度"""
        from src.modules.address_query.validator import AddressValidator
        
        invalid_addresses = [
            "TJCnKsPa7y5",  # 太短
            "TJCnKsPa7y5okkXvQAidZBzqx3QyQ6sxMWxxxxxxxxxxx",  # 太长
        ]
        
        for addr in invalid_addresses:
            is_valid, error = AddressValidator.validate(addr)
            assert not is_valid, f"地址 {addr} 应无效"
            assert "长度" in error
        
        print("✅ 错误长度地址正确拒绝")
    
    def test_invalid_address_invalid_chars(self):
        """测试无效字符"""
        from src.modules.address_query.validator import AddressValidator
        
        # Base58 不包含 0OIl
        invalid_addresses = [
            "T0CnKsPa7y5okkXvQAidZBzqx3QyQ6sxMW",  # 包含 0
            "TOCnKsPa7y5okkXvQAidZBzqx3QyQ6sxMW",  # 包含 O
            "TICnKsPa7y5okkXvQAidZBzqx3QyQ6sxMW",  # 包含 I
            "TlCnKsPa7y5okkXvQAidZBzqx3QyQ6sxMW",  # 包含 l
        ]
        
        for addr in invalid_addresses:
            is_valid, error = AddressValidator.validate(addr)
            assert not is_valid, f"地址 {addr} 应无效"
        
        print("✅ 无效字符地址正确拒绝")


class TestTRXExchangeValidation:
    """TRX 兑换输入验证测试"""
    
    def test_trx_sender_address_validation(self):
        """测试 TRX 发送器地址验证"""
        from src.modules.trx_exchange.trx_sender import TRXSender
        
        sender = TRXSender()
        
        # 有效地址
        assert sender.validate_address("TJCnKsPa7y5okkXvQAidZBzqx3QyQ6sxMW")
        
        # 无效地址
        assert not sender.validate_address("")
        assert not sender.validate_address("invalid")
        assert not sender.validate_address("0x742d35Cc6634C0532925a3b844Bc9e7595f")
        
        print("✅ TRXSender 地址验证正常")


class TestAmountValidation:
    """金额验证测试"""
    
    def test_valid_amounts(self):
        """测试有效金额"""
        from decimal import Decimal
        
        valid_amounts = ["10", "5.5", "100.123", "0.001"]
        
        for amount_str in valid_amounts:
            try:
                amount = Decimal(amount_str)
                assert amount > 0, f"金额 {amount} 应为正数"
            except Exception as e:
                pytest.fail(f"有效金额 {amount_str} 解析失败: {e}")
        
        print(f"✅ {len(valid_amounts)} 个有效金额验证通过")
    
    def test_invalid_amounts(self):
        """测试无效金额"""
        from decimal import Decimal, InvalidOperation
        
        invalid_amounts = ["abc", "-10", "0", ""]
        
        for amount_str in invalid_amounts:
            try:
                if not amount_str:
                    continue
                amount = Decimal(amount_str)
                if amount <= 0:
                    continue  # 正确：检测到非正数
                pytest.fail(f"无效金额 {amount_str} 应被拒绝")
            except InvalidOperation:
                pass  # 正确：解析失败
        
        print("✅ 无效金额正确拒绝")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
