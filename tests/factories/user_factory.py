"""
用户数据工厂
生成测试用的用户数据
"""
import random
import string
from datetime import datetime
from typing import Optional
from unittest.mock import MagicMock


class UserFactory:
    """用户数据工厂类"""
    
    _counter = 0
    
    @classmethod
    def _get_next_id(cls) -> int:
        """生成递增的用户ID"""
        cls._counter += 1
        return 100000000 + cls._counter
    
    @classmethod
    def create(
        cls,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        first_name: str = "Test",
        last_name: str = "User",
        is_bot: bool = False,
        language_code: str = "zh-hans",
        is_admin: bool = False,
    ) -> MagicMock:
        """
        创建模拟的 Telegram User 对象
        
        Args:
            user_id: 用户ID，默认自动生成
            username: 用户名，默认自动生成
            first_name: 名字
            last_name: 姓氏
            is_bot: 是否是机器人
            language_code: 语言代码
            is_admin: 是否是管理员
        
        Returns:
            MagicMock: 模拟的 User 对象
        """
        from telegram import User
        
        if user_id is None:
            user_id = cls._get_next_id()
        
        if username is None:
            username = f"test_user_{user_id}"
        
        user = MagicMock(spec=User)
        user.id = user_id
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.is_bot = is_bot
        user.language_code = language_code
        user.full_name = f"{first_name} {last_name}".strip()
        
        # 标记管理员
        if is_admin:
            user.id = 123456789  # 使用默认管理员ID
        
        return user
    
    @classmethod
    def create_admin(cls) -> MagicMock:
        """创建管理员用户"""
        return cls.create(
            user_id=123456789,
            username="admin",
            first_name="Admin",
            is_admin=True
        )
    
    @classmethod
    def create_db_user(
        cls,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        balance_micro_usdt: int = 0,
    ):
        """
        创建数据库用户记录
        
        Args:
            user_id: 用户ID
            username: 用户名
            balance_micro_usdt: 余额（微USDT）
        
        Returns:
            User: 数据库用户对象
        """
        from src.database import User
        
        if user_id is None:
            user_id = cls._get_next_id()
        
        if username is None:
            username = f"test_user_{user_id}"
        
        return User(
            user_id=user_id,
            username=username,
            balance_micro_usdt=balance_micro_usdt,
            created_at=datetime.now(),
        )
    
    @classmethod
    def generate_username(cls, min_length: int = 5, max_length: int = 20) -> str:
        """生成随机用户名"""
        length = random.randint(min_length, max_length)
        chars = string.ascii_lowercase + string.digits + "_"
        # 用户名必须以字母开头
        first_char = random.choice(string.ascii_lowercase)
        rest = ''.join(random.choices(chars, k=length - 1))
        return first_char + rest
    
    @classmethod
    def generate_invalid_username(cls) -> str:
        """生成无效用户名（用于测试验证）"""
        invalid_examples = [
            "ab",           # 太短
            "a" * 33,       # 太长
            "user-name",    # 包含连字符
            "user.name",    # 包含点
            "用户名",        # 非ASCII字符
            "",             # 空
            "123user",      # 数字开头
        ]
        return random.choice(invalid_examples)

