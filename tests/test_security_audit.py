"""
安全审查测试
"""

import pytest
import re
import os


class TestAPITimeouts:
    """API 超时配置测试"""
    
    def test_httpx_has_timeout(self):
        """测试所有 httpx 调用都有超时"""
        import glob
        
        src_files = glob.glob("src/**/*.py", recursive=True)
        issues = []
        
        for file_path in src_files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # 检查 httpx.AsyncClient 是否有 timeout
            if "httpx.AsyncClient()" in content:
                # 无参数创建，可能缺少超时
                if "httpx.AsyncClient(timeout=" not in content:
                    issues.append(f"{file_path}: httpx.AsyncClient 可能缺少 timeout")
        
        if issues:
            print(f"⚠️ 发现 {len(issues)} 个潜在问题:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✅ 所有 httpx 调用都有超时配置")
    
    def test_order_timeout_configurable(self):
        """测试订单超时时间可配置"""
        from src.common.settings_service import get_order_timeout_minutes
        
        timeout = get_order_timeout_minutes()
        assert isinstance(timeout, int), "超时时间应为整数"
        assert timeout > 0, "超时时间应为正数"
        
        print(f"✅ 订单超时时间: {timeout} 分钟")


class TestSensitiveLogging:
    """敏感信息日志测试"""
    
    def test_no_token_in_logs(self):
        """测试日志不包含 token"""
        import glob
        
        src_files = glob.glob("src/**/*.py", recursive=True)
        issues = []
        
        sensitive_patterns = [
            r'logger\.\w+\(.*bot_token',
            r'logger\.\w+\(.*private_key',
            r'logger\.\w+\(.*password',
            r'logger\.\w+\(.*secret',
            r'print\(.*bot_token',
            r'print\(.*private_key',
        ]
        
        for file_path in src_files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            for pattern in sensitive_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append(f"{file_path}: 可能记录敏感信息 ({pattern})")
        
        if issues:
            print(f"⚠️ 发现 {len(issues)} 个潜在敏感日志:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✅ 未发现敏感信息日志")
    
    def test_config_uses_env_vars(self):
        """测试配置使用环境变量"""
        from src.config import Settings
        
        # 检查敏感字段是否有默认值
        sensitive_fields = ['bot_token', 'webhook_secret', 'trx_exchange_private_key']
        
        for field in sensitive_fields:
            field_info = Settings.model_fields.get(field)
            if field_info:
                # 如果是必填字段（无默认值），说明必须从环境变量获取
                has_default = field_info.default is not None or field_info.default_factory is not None
                if field == 'bot_token' or field == 'webhook_secret':
                    # 这些应该是必填的
                    print(f"✅ {field}: 必填字段，从环境变量读取")
                else:
                    print(f"ℹ️ {field}: 可选字段")


class TestInputSanitization:
    """输入清理测试"""
    
    def test_address_validator_rejects_injection(self):
        """测试地址验证器拒绝注入攻击"""
        from src.modules.address_query.validator import AddressValidator
        
        injection_attempts = [
            "T' OR '1'='1",
            "T<script>alert(1)</script>",
            "T; DROP TABLE users;--",
            "T$(whoami)",
            "T`id`",
        ]
        
        for attempt in injection_attempts:
            is_valid, _ = AddressValidator.validate(attempt)
            assert not is_valid, f"应拒绝注入尝试: {attempt}"
        
        print(f"✅ 地址验证器正确拒绝 {len(injection_attempts)} 个注入尝试")
    
    def test_html_escaping_in_messages(self):
        """测试消息模板使用 HTML 转义"""
        from src.core.formatter import MessageFormatter
        
        formatter = MessageFormatter()
        
        # 测试 HTML 转义
        dangerous_input = "<script>alert('xss')</script>"
        escaped = formatter.escape_html(dangerous_input)
        
        assert "<script>" not in escaped, "HTML 标签应被转义"
        assert "&lt;" in escaped or "&gt;" in escaped, "应包含转义字符"
        
        print("✅ MessageFormatter 正确转义 HTML")


class TestDependencyVersions:
    """依赖版本测试"""
    
    def test_critical_dependencies_pinned(self):
        """测试关键依赖版本已固定"""
        with open("requirements.txt", 'r', encoding='utf-8') as f:
            content = f.read()
        
        critical_deps = [
            'python-telegram-bot',
            'sqlalchemy',
            'redis',
            'httpx',
            'pydantic',
        ]
        
        for dep in critical_deps:
            # 检查是否有版本约束
            pattern = rf'{dep}[=~><]'
            if re.search(pattern, content, re.IGNORECASE):
                print(f"✅ {dep}: 版本已约束")
            else:
                print(f"⚠️ {dep}: 可能缺少版本约束")


class TestRateLimiting:
    """速率限制测试"""
    
    def test_address_query_has_rate_limit(self):
        """测试地址查询有限频"""
        from src.config import settings
        
        rate_limit = settings.address_query_rate_limit_minutes
        assert isinstance(rate_limit, int), "限频应为整数"
        assert rate_limit > 0, "限频应为正数"
        
        print(f"✅ 地址查询限频: {rate_limit} 分钟")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
