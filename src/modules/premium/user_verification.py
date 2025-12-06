"""
用户身份验证服务
处理用户名验证、绑定和查询

方案A：直接信任用户名格式（不通过 Telegram API 验证）
- 原因：Telegram Bot API 的 get_chat() 只能查询已与 Bot 交互过的用户
- 安全性：发货时如果用户名无效会失败，有完善的失败处理和通知机制
"""

import logging
import re
from datetime import datetime
from typing import Any

from telegram import Bot, User

from src.common.db_manager import get_db_context
from src.database import UserBinding


logger = logging.getLogger(__name__)

# 用户名格式正则：5-32个字符，只能包含字母、数字和下划线
USERNAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{4,31}$")


class UserVerificationService:
    """用户身份验证服务"""

    def __init__(self, bot_username: str = None):
        """
        初始化服务

        Args:
            bot_username: Bot的用户名，用于生成绑定链接
        """
        self.bot_username = bot_username or "premium_bot"

    def _is_valid_username_format(self, username: str) -> bool:
        """
        验证用户名格式是否有效

        Telegram 用户名规则：
        - 5-32 个字符
        - 以字母开头
        - 只能包含字母、数字和下划线

        Args:
            username: 用户名（不含@）

        Returns:
            是否格式有效
        """
        if not username:
            return False
        return bool(USERNAME_PATTERN.match(username))

    async def verify_user_exists(self, username: str, bot: Bot = None) -> dict[str, Any]:
        """
        验证用户是否存在

        方案A逻辑：
        1. 先检查本地数据库是否有已验证的绑定
        2. 如果本地没有，验证用户名格式是否正确
        3. 格式正确则直接信任，允许进入套餐选择
        4. 实际发货时如果用户名无效，会有失败处理机制

        Args:
            username: Telegram用户名（不含@）
            bot: Telegram Bot 实例（方案A中不再使用，保留参数以兼容调用）

        Returns:
            {
                "exists": bool,
                "user_id": Optional[int],
                "nickname": Optional[str],
                "is_verified": bool,
                "binding_url": Optional[str],
                "error": Optional[str]
            }
        """
        # 第一步：检查本地数据库（优先使用已验证的绑定信息）
        try:
            with get_db_context() as db:
                binding = db.query(UserBinding).filter(UserBinding.username == username.lower()).first()

                if binding and binding.is_verified:
                    # 本地已有已验证用户，直接返回
                    logger.info(f"User @{username} found in local database (verified)")
                    return {
                        "exists": True,
                        "user_id": binding.user_id,
                        "nickname": binding.nickname,
                        "is_verified": True,
                        "binding_url": None,
                        "error": None,
                    }
        except Exception as e:
            logger.error(f"Database error checking user {username}: {e}")

        # 第二步：验证用户名格式（方案A：直接信任格式正确的用户名）
        if self._is_valid_username_format(username):
            logger.info(f"User @{username} format valid, trusting username (Plan A)")
            return {
                "exists": True,
                "user_id": None,  # 暂无 user_id，发货时再解析
                "nickname": username,  # 使用用户名作为昵称
                "is_verified": False,  # 标记为未本地验证
                "binding_url": None,
                "error": None,
            }
        else:
            # 用户名格式无效
            logger.info(f"User @{username} format invalid")
            return {
                "exists": False,
                "user_id": None,
                "nickname": None,
                "is_verified": False,
                "binding_url": None,
                "error": "用户名格式无效，请检查：以字母开头，5-32个字符，只能包含字母、数字和下划线",
            }

    async def bind_user(self, user: User, force_update: bool = False) -> bool:
        """
        绑定用户信息

        Args:
            user: Telegram User 对象
            force_update: 是否强制更新已存在的绑定

        Returns:
            是否绑定成功
        """
        if not user.username:
            logger.warning(f"User {user.id} has no username, cannot bind")
            return False

        try:
            with get_db_context() as db:
                # 查询现有绑定
                existing = (
                    db.query(UserBinding)
                    .filter((UserBinding.user_id == user.id) | (UserBinding.username == user.username.lower()))
                    .first()
                )

                if existing:
                    if not force_update:
                        logger.info(f"User {user.id} already bound")
                        return True

                    # 更新绑定信息
                    existing.user_id = user.id
                    existing.username = user.username.lower()
                    existing.nickname = user.first_name
                    existing.is_verified = True
                    existing.updated_at = datetime.now()
                else:
                    # 创建新绑定
                    binding = UserBinding(
                        user_id=user.id, username=user.username.lower(), nickname=user.first_name, is_verified=True
                    )
                    db.add(binding)

                # 上下文管理器会自动commit
                logger.info(f"Successfully bound user {user.id} (@{user.username})")
            return True
        except Exception as e:
            logger.error(f"Failed to bind user {user.id}: {e}", exc_info=True)
            return False

    async def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """
        通过user_id获取用户信息

        Args:
            user_id: Telegram用户ID

        Returns:
            用户信息字典或None
        """
        with get_db_context() as db:
            binding = db.query(UserBinding).filter(UserBinding.user_id == user_id).first()

            if binding:
                return {
                    "user_id": binding.user_id,
                    "username": binding.username,
                    "nickname": binding.nickname,
                    "is_verified": binding.is_verified,
                }
            return None

    async def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """
        通过用户名获取用户信息

        Args:
            username: Telegram用户名（不含@）

        Returns:
            用户信息字典或None
        """
        with get_db_context() as db:
            binding = db.query(UserBinding).filter(UserBinding.username == username.lower()).first()

            if binding:
                return {
                    "user_id": binding.user_id,
                    "username": binding.username,
                    "nickname": binding.nickname,
                    "is_verified": binding.is_verified,
                }
            return None

    def _generate_binding_url(self, username: str) -> str:
        """
        生成用户绑定链接

        Args:
            username: 要绑定的用户名

        Returns:
            深链接URL
        """
        return f"https://t.me/{self.bot_username}?start=bind_{username}"

    async def auto_bind_on_interaction(self, user: User) -> bool:
        """
        用户与bot交互时自动绑定（如果有用户名）

        Args:
            user: Telegram User 对象

        Returns:
            是否绑定成功
        """
        if not user or not user.username:
            return False

        try:
            # 使用上下文管理器确保连接正确关闭
            with get_db_context() as db:
                # 检查是否已绑定
                existing = db.query(UserBinding).filter(UserBinding.user_id == user.id).first()

                if existing:
                    if existing.is_verified:
                        # 已验证
                        return True
                    else:
                        # 存在但未验证，更新验证状态
                        existing.is_verified = True
                        existing.updated_at = datetime.now()
                        # 事务会自动提交
                        logger.info(f"Verified existing user {user.id}")
                        return True
                else:
                    # 新用户，创建绑定
                    binding = UserBinding(
                        user_id=user.id,
                        username=user.username.lower(),
                        nickname=user.first_name or user.username,
                        is_verified=True,
                        created_at=datetime.now(),
                    )
                    db.add(binding)
                    # 事务会自动提交
                    logger.info(f"Created binding for user {user.id}")
                    return True

        except Exception as e:
            logger.error(f"Auto-bind failed for user {user.id}: {e}")
            # 不要抛出异常，避免影响主流程
            return False


# 全局实例（延迟初始化）
user_verification_service: UserVerificationService | None = None


def get_user_verification_service(bot_username: str = None) -> UserVerificationService:
    """获取用户验证服务实例"""
    global user_verification_service
    if user_verification_service is None:
        user_verification_service = UserVerificationService(bot_username)
    return user_verification_service
