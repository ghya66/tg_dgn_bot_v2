"""
ConversationHandler包装器
确保所有对话处理器的一致性和隔离性
"""

import functools
import logging

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from .navigation_manager import NavigationManager


logger = logging.getLogger(__name__)


class ConversationTracker:
    """
    对话追踪器 - 追踪每个用户的活跃对话
    确保同一用户同一时间只有一个活跃对话
    """

    # 用户活跃对话: {user_id: handler_name}
    _active_conversations: dict[int, str] = {}

    # 已注册的所有 ConversationHandler 实例
    _registered_handlers: dict[str, ConversationHandler] = {}

    @classmethod
    def register_handler(cls, name: str, handler: ConversationHandler) -> None:
        """
        注册一个 ConversationHandler

        Args:
            name: 处理器名称
            handler: ConversationHandler 实例
        """
        cls._registered_handlers[name] = handler
        logger.debug(f"注册对话处理器: {name}")

    @classmethod
    def set_active(cls, user_id: int, handler_name: str) -> None:
        """
        设置用户的活跃对话

        Args:
            user_id: 用户ID
            handler_name: 处理器名称
        """
        old_handler = cls._active_conversations.get(user_id)
        if old_handler and old_handler != handler_name:
            logger.info(f"用户 {user_id} 从 {old_handler} 切换到 {handler_name}")

        cls._active_conversations[user_id] = handler_name

    @classmethod
    def clear_active(cls, user_id: int, handler_name: str | None = None) -> None:
        """
        清除用户的活跃对话

        Args:
            user_id: 用户ID
            handler_name: 如果指定，只有当前活跃对话匹配时才清除
        """
        if handler_name:
            if cls._active_conversations.get(user_id) == handler_name:
                cls._active_conversations.pop(user_id, None)
                logger.debug(f"用户 {user_id} 结束对话 {handler_name}")
        else:
            cls._active_conversations.pop(user_id, None)

    @classmethod
    def get_active(cls, user_id: int) -> str | None:
        """
        获取用户当前活跃的对话

        Args:
            user_id: 用户ID

        Returns:
            当前活跃的处理器名称，如果没有则返回 None
        """
        return cls._active_conversations.get(user_id)

    @classmethod
    def clear_all_for_user(cls, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        清除用户的所有活跃对话状态，包括 ConversationHandler 的内部状态

        Args:
            user_id: 用户ID
            context: Telegram 上下文
        """
        old_handler = cls._active_conversations.pop(user_id, None)
        if old_handler:
            logger.info(f"用户 {user_id} 清除所有活跃对话 (之前: {old_handler})")

        # 获取 chat_id
        chat_id = None
        if hasattr(context, "_chat_id"):
            chat_id = context._chat_id
        elif hasattr(context, "chat_data") and context._chat_id_and_data:
            chat_id = context._chat_id_and_data[0]

        # 清除所有已注册 ConversationHandler 的内部状态
        for handler_name, handler in cls._registered_handlers.items():
            cls._clear_handler_internal_state(handler, user_id, chat_id, handler_name)

        # 清理 context.user_data 中的对话相关数据
        NavigationManager._cleanup_conversation_data(context)

    @classmethod
    def _clear_handler_internal_state(
        cls, handler: ConversationHandler, user_id: int, chat_id: int | None, handler_name: str
    ) -> None:
        """
        清除单个 ConversationHandler 的内部对话状态

        Args:
            handler: ConversationHandler 实例
            user_id: 用户ID
            chat_id: 聊天ID
            handler_name: 处理器名称（用于日志）
        """
        if not hasattr(handler, "_conversations"):
            return

        # ConversationHandler 使用不同的键格式，取决于 per_chat 和 per_user 设置
        # 常见格式: (chat_id, user_id) 或 chat_id 或 user_id
        keys_to_remove = []

        for key in list(handler._conversations.keys()):
            should_remove = False

            if isinstance(key, tuple):
                # 格式: (chat_id, user_id) - 最常见
                if len(key) == 2:
                    key_chat_id, key_user_id = key
                    if key_user_id == user_id:
                        should_remove = True
                # 格式: (chat_id,) 或其他元组
                elif len(key) >= 1 and chat_id is not None and key[0] == chat_id:
                    should_remove = True
            elif key == user_id:
                # 格式: 直接是 user_id
                should_remove = True
            elif chat_id is not None and key == chat_id:
                # 格式: 直接是 chat_id
                should_remove = True

            if should_remove:
                keys_to_remove.append(key)

        # 删除找到的键
        for key in keys_to_remove:
            del handler._conversations[key]
            logger.debug(f"清除 {handler_name} 的内部对话状态: key={key}")


class SafeConversationHandler:
    """安全的对话处理器包装器"""

    # 全局导航模式列表
    NAVIGATION_PATTERNS = [
        r"^(back_to_main|nav_back_to_main|menu_back_to_main|addrq_back_to_main)$",  # 返回主菜单
        r"^admin_back$",  # 管理员面板返回
        r"^orders_back$",  # 订单管理返回
    ]

    # 菜单切换模式（需要结束当前对话）
    MENU_SWITCH_PATTERNS = [r"^menu_(profile|address_query|energy|trx_exchange|premium|support|clone|help|admin)$"]

    # 全局命令（始终可用）
    GLOBAL_COMMANDS = ["start", "help", "cancel"]

    @classmethod
    def create(
        cls,
        entry_points: list,
        states: dict,
        fallbacks: list,
        allow_reentry: bool = True,
        name: str | None = None,
        per_message: bool = False,
        per_chat: bool = True,
        per_user: bool = True,
        conversation_timeout: int | None = None,
    ) -> ConversationHandler:
        """
        创建安全的ConversationHandler

        Args:
            entry_points: 入口点列表
            states: 状态字典
            fallbacks: 回退处理器列表
            allow_reentry: 是否允许重入
            name: 处理器名称（用于日志）
            per_message: 是否为每条消息创建独立对话
            per_chat: 是否为每个聊天创建独立对话
            per_user: 是否为每个用户创建独立对话
            conversation_timeout: 对话超时时间（秒）

        Returns:
            配置好的ConversationHandler
        """
        name = name or "unnamed"
        logger.info(f"创建安全对话处理器: {name}")

        # 包装入口点处理函数，添加对话追踪
        wrapped_entry_points = cls._wrap_entry_points(entry_points, name)

        # 包装状态处理函数，确保对话结束时清理追踪
        wrapped_states = cls._wrap_states(states, name)

        # 构建安全的fallbacks
        safe_fallbacks = cls._build_safe_fallbacks(fallbacks, name)

        # 创建ConversationHandler
        handler = ConversationHandler(
            entry_points=wrapped_entry_points,
            states=wrapped_states,
            fallbacks=safe_fallbacks,
            allow_reentry=allow_reentry,
            name=name,
            per_message=per_message,
            per_chat=per_chat,
            per_user=per_user,
            conversation_timeout=conversation_timeout,
        )

        # 注册处理器到追踪器
        ConversationTracker.register_handler(name, handler)

        logger.info(f"✅ 安全对话处理器 '{name}' 创建成功")
        return handler

    @classmethod
    def _wrap_entry_points(cls, entry_points: list, handler_name: str) -> list:
        """
        包装入口点处理函数，在进入对话时清理其他活跃对话

        Args:
            entry_points: 原始入口点列表
            handler_name: 当前处理器名称

        Returns:
            包装后的入口点列表
        """
        wrapped = []
        for ep in entry_points:
            wrapped.append(cls._wrap_handler(ep, handler_name, is_entry=True))
        return wrapped

    @classmethod
    def _wrap_states(cls, states: dict, handler_name: str) -> dict:
        """
        包装状态处理函数

        Args:
            states: 原始状态字典
            handler_name: 当前处理器名称

        Returns:
            包装后的状态字典
        """
        wrapped_states = {}
        for state, handlers in states.items():
            wrapped_handlers = []
            for h in handlers:
                wrapped_handlers.append(cls._wrap_handler(h, handler_name, is_entry=False))
            wrapped_states[state] = wrapped_handlers
        return wrapped_states

    @classmethod
    def _wrap_handler(cls, handler, handler_name: str, is_entry: bool):
        """
        包装单个处理器

        Args:
            handler: 原始处理器
            handler_name: 当前处理器名称
            is_entry: 是否为入口点处理器

        Returns:
            包装后的处理器
        """
        original_callback = handler.callback

        @functools.wraps(original_callback)
        async def wrapped_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id if update.effective_user else None

            if user_id:
                if is_entry:
                    # 进入新对话时，清理用户之前的所有活跃对话
                    old_handler = ConversationTracker.get_active(user_id)
                    if old_handler and old_handler != handler_name:
                        logger.info(f"用户 {user_id} 进入 {handler_name}，自动结束之前的对话 {old_handler}")
                        ConversationTracker.clear_all_for_user(user_id, context)

                    # 设置当前对话为活跃
                    ConversationTracker.set_active(user_id, handler_name)

            # 调用原始处理函数
            result = await original_callback(update, context)

            # 如果对话结束，清理追踪
            if user_id and result == ConversationHandler.END:
                ConversationTracker.clear_active(user_id, handler_name)

            return result

        # 创建新的处理器实例
        handler.callback = wrapped_callback
        return handler

    @classmethod
    def _build_safe_fallbacks(cls, original_fallbacks: list, handler_name: str) -> list:
        """
        构建安全的fallback列表

        Args:
            original_fallbacks: 原始fallback列表
            handler_name: 处理器名称

        Returns:
            安全的fallback列表
        """
        safe_fallbacks = []

        # 1. 不在这里添加导航处理 - NavigationManager已在group=0全局注册
        # 由于NavigationManager在group=0（最高优先级）全局注册，
        # 所有导航回调都会被它拦截并处理
        # 如果在这里再添加，会导致重复处理
        logger.debug(f"SafeConversationHandler '{handler_name}': 导航由全局NavigationManager处理")

        # 2. 添加菜单切换处理 - 这些不会和全局导航冲突
        for pattern in cls.MENU_SWITCH_PATTERNS:
            safe_fallbacks.append(CallbackQueryHandler(cls._handle_menu_switch, pattern=pattern))

        # 3. 添加全局命令处理
        safe_fallbacks.append(CommandHandler("cancel", cls._handle_cancel))

        # 4. 过滤并添加原始fallbacks
        for fb in original_fallbacks:
            if cls._should_include_fallback(fb):
                safe_fallbacks.append(fb)
            else:
                logger.debug(f"过滤掉fallback: {fb}")

        # 5. 添加默认错误处理
        safe_fallbacks.append(
            MessageHandler(filters.ALL, lambda u, c: cls._handle_unexpected_input(u, c, handler_name))
        )

        return safe_fallbacks

    @classmethod
    def _should_include_fallback(cls, fallback) -> bool:
        """
        判断是否应该包含某个fallback

        Args:
            fallback: 原始fallback处理器

        Returns:
            是否包含
        """
        # 跳过会干扰导航的处理器
        if isinstance(fallback, CallbackQueryHandler):
            pattern = getattr(fallback.pattern, "pattern", None) if hasattr(fallback, "pattern") else None
            if pattern:
                pattern_str = str(pattern)
                # 检查是否包含导航相关模式
                skip_patterns = [
                    "back_to_main",
                    "nav_back_to_main",
                    "menu_back_to_main",
                    "addrq_back_to_main",
                    "admin_back",
                    "orders_back",
                ]
                for skip in skip_patterns:
                    if skip in pattern_str:
                        return False

        return True

    @staticmethod
    async def _handle_cancel(update, context) -> int:
        """处理取消命令"""
        user = update.effective_user
        logger.info(f"用户 {user.id} 取消当前对话")

        # 清理对话追踪
        ConversationTracker.clear_all_for_user(user.id, context)

        # 清理数据并返回主菜单
        NavigationManager._cleanup_conversation_data(context)
        await NavigationManager._show_main_menu(update, context)

        return ConversationHandler.END

    @staticmethod
    async def _handle_menu_switch(update, context) -> int:
        """处理菜单切换"""
        query = update.callback_query
        await query.answer()

        user = update.effective_user
        target = query.data
        logger.info(f"用户 {user.id} 切换到菜单: {target}")

        # 清理对话追踪
        ConversationTracker.clear_all_for_user(user.id, context)

        # 结束当前对话，让主处理器接管
        NavigationManager._cleanup_conversation_data(context)
        return ConversationHandler.END

    @staticmethod
    async def _handle_unexpected_input(update, context, handler_name: str):
        """处理意外输入 - 检查用户是否真的在这个对话中"""
        user = update.effective_user

        # 检查用户当前活跃的对话是否是这个处理器
        active_handler = ConversationTracker.get_active(user.id)

        if active_handler != handler_name:
            # 用户不在这个对话中，忽略此输入
            logger.debug(f"用户 {user.id} 不在 {handler_name} 中 (活跃: {active_handler})，忽略输入")
            return ConversationHandler.END

        logger.warning(f"用户 {user.id} 在 {handler_name} 中发送了意外输入")

        # 不做任何响应，保持在当前状态
        return None

    @classmethod
    def create_simple(
        cls, command: str, handler_func, states: dict | None = None, name: str | None = None
    ) -> ConversationHandler:
        """
        创建简单的对话处理器（单命令入口）

        Args:
            command: 命令名称
            handler_func: 处理函数
            states: 状态字典（可选）
            name: 处理器名称

        Returns:
            配置好的ConversationHandler
        """
        entry_points = [CommandHandler(command, handler_func)]
        states = states or {}
        fallbacks = []

        return cls.create(
            entry_points=entry_points, states=states, fallbacks=fallbacks, name=name or f"simple_{command}"
        )
