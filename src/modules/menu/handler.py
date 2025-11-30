"""
主菜单模块主处理器 - 标准化版本
解决了返回主菜单重复提示的问题
"""

import logging
import json
from typing import List, Optional
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ContextTypes,
    BaseHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from src.core.base import BaseModule
from src.core.formatter import MessageFormatter
from src.core.state_manager import ModuleStateManager
from src.utils.content_helper import get_content

from .messages import MainMenuMessages


logger = logging.getLogger(__name__)


class MainMenuModule(BaseModule):
    """标准化的主菜单模块"""
    
    MAX_MERCHANT_ROWS = 10
    CHANNEL_TITLES = {
        "all": "✅ 全部渠道报价",
        "bank": "🏦 银行卡渠道",
        "alipay": "💴 支付宝渠道",
        "wechat": "🟢 微信渠道",
    }
    CHANNEL_ICONS = {
        "bank": "🏦",
        "alipay": "💴",
        "wechat": "🟢",
    }
    
    def __init__(self):
        """初始化主菜单模块"""
        self.formatter = MessageFormatter()
        self.state_manager = ModuleStateManager()
        self.keyboard_shown_key = "main_menu_keyboard_shown"
    
    @property
    def module_name(self) -> str:
        """模块名称"""
        return "main_menu"
    
    def get_handlers(self) -> List[BaseHandler]:
        """获取模块处理器"""
        return [
            CommandHandler("start", self.start_command),
            CallbackQueryHandler(self.show_main_menu, pattern=r"^(back_to_main|nav_back_to_main|menu_back_to_main|addrq_back_to_main)$"),
            CallbackQueryHandler(self.handle_free_clone, pattern=r"^menu_clone$"),
            CallbackQueryHandler(self.handle_support, pattern=r"^menu_support$"),
            CallbackQueryHandler(self.handle_orders, pattern=r"^menu_orders$"),
            # 底部键盘按钮处理器
            MessageHandler(filters.Regex(r"^💱 实时汇率$"), self.show_rates),
            MessageHandler(filters.Regex(r"^🎁 免费克隆$"), self.show_clone_message),
            MessageHandler(filters.Regex(r"^👨‍💼 联系客服$"), self.show_support_message),
        ]
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理 /start 命令"""
        from src.config import settings
        
        user = update.effective_user
        
        # 重要：重置键盘显示标志，因为/start是新的会话开始
        context.user_data[self.keyboard_shown_key] = False
        
        # 从数据库读取欢迎语（支持热更新）
        text = get_content("welcome_message", default=settings.welcome_message)
        text = text.replace("{first_name}", self.formatter.escape_html(user.first_name or "朋友"))
        
        # 构建引流按钮（InlineKeyboard）
        inline_keyboard = self._build_promotion_buttons()
        inline_markup = InlineKeyboardMarkup(inline_keyboard)
        
        # 构建底部键盘（ReplyKeyboard）
        reply_markup = self._build_reply_keyboard()
        
        # 先发送带InlineKeyboard的欢迎消息
        await update.message.reply_text(
            text, 
            parse_mode="HTML", 
            reply_markup=inline_markup
        )
        
        # 然后设置底部键盘并发送提示
        # 注意：只在/start命令时发送键盘提示
        await update.message.reply_text(
            MainMenuMessages.KEYBOARD_HINT,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        context.user_data[self.keyboard_shown_key] = True
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        显示主菜单（从回调返回）
        关键修复：从回调返回时不再重复发送键盘提示
        """
        # 清理可能的临时状态（如地址查询等待状态）
        context.user_data.pop("awaiting_address", None)
        
        # 构建菜单
        keyboard = self._build_promotion_buttons()
        inline_reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = MainMenuMessages.MAIN_MENU
        
        query = update.callback_query
        if query:
            await query.answer()
            try:
                # 只更新消息内容，不发送新消息
                await query.edit_message_text(
                    text, 
                    parse_mode="HTML", 
                    reply_markup=inline_reply_markup
                )
            except Exception as e:
                # 如果编辑失败（比如消息太旧），发送新消息
                logger.warning(f"编辑消息失败: {e}")
                await query.message.reply_text(
                    text, 
                    parse_mode="HTML", 
                    reply_markup=inline_reply_markup
                )
            
            # 关键：从回调返回主菜单时，不再发送键盘提示
            # 因为ReplyKeyboard是持久的，用户已经有了
            # 这就解决了重复提示的问题
        else:
            # 如果不是从回调触发（比如直接调用）
            message = update.message or update.effective_message
            if not message:
                return
            
            await message.reply_text(
                text, 
                parse_mode="HTML", 
                reply_markup=inline_reply_markup
            )
            
            # 只有在用户没有键盘时才显示
            # 比如新用户或者bot重启后的第一次
            if not context.user_data.get(self.keyboard_shown_key):
                reply_markup = self._build_reply_keyboard()
                await message.reply_text(
                    MainMenuMessages.KEYBOARD_HINT,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
                context.user_data[self.keyboard_shown_key] = True
    
    async def handle_free_clone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理免费克隆功能"""
        from src.config import settings
        
        query = update.callback_query
        await query.answer()
        
        # 从数据库读取免费克隆文案（支持热更新）
        text = get_content("free_clone_message", default=settings.free_clone_message)
        
        keyboard = [
            [InlineKeyboardButton("👨‍💼 联系客服", callback_data="menu_support")],
            [InlineKeyboardButton("🔙 返回主菜单", callback_data="nav_back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text, 
            parse_mode="HTML", 
            reply_markup=reply_markup
        )
    
    def _build_promotion_buttons(self) -> List[List[InlineKeyboardButton]]:
        """构建引流按钮（从配置读取）"""
        from src.config import settings
        
        try:
            # 解析配置的按钮
            buttons_config = settings.promotion_buttons
            # 移除换行和多余空格
            buttons_config = buttons_config.replace('\n', '').replace(' ', '')
            # 解析为列表（安全地使用JSON）
            button_rows = json.loads(f'[{buttons_config}]')
            
            keyboard = []
            for row in button_rows:
                button_row = []
                for btn in row:
                    text = btn.get('text', '')
                    url = btn.get('url')
                    callback = btn.get('callback')
                    
                    if url:
                        # 外部链接按钮
                        button_row.append(InlineKeyboardButton(text, url=url))
                    elif callback:
                        # 回调按钮
                        button_row.append(InlineKeyboardButton(text, callback_data=callback))
                
                if button_row:
                    keyboard.append(button_row)
            
            return keyboard
        except Exception as e:
            logger.error(f"解析引流按钮配置失败: {e}")
            # 返回默认按钮
            return [
                [
                    InlineKeyboardButton("💎 Premium会员", callback_data="menu_premium"),
                    InlineKeyboardButton("👤 个人中心", callback_data="menu_profile")
                ],
                [
                    InlineKeyboardButton("🔍 地址查询", callback_data="menu_address_query"),
                    InlineKeyboardButton("⚡ 能量兑换", callback_data="menu_energy")
                ],
                [
                    InlineKeyboardButton("🎁 免费克隆", callback_data="menu_clone"),
                    InlineKeyboardButton("👨‍💼 联系客服", callback_data="menu_support")
                ]
            ]
    
    def _build_reply_keyboard(self) -> ReplyKeyboardMarkup:
        """构建底部回复键盘"""
        reply_keyboard = [
            [KeyboardButton("💎 Premium会员"), KeyboardButton("⚡ 能量兑换")],
            [KeyboardButton("🔍 地址查询"), KeyboardButton("👤 个人中心")],
            [KeyboardButton("💱 TRX闪兑"), KeyboardButton("👨‍💼 联系客服")],
            [KeyboardButton("💱 实时汇率"), KeyboardButton("🎁 免费克隆")],
        ]
        return ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
            one_time_keyboard=False,
        )
    
    async def handle_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理联系客服按钮"""
        from src.config import settings
        
        query = update.callback_query
        await query.answer()
        
        # 从配置获取客服联系方式
        support_contact = getattr(settings, 'support_contact', '@your_support_bot')
        
        text = (
            "📞 <b>联系客服</b>\n\n"
            f"如有任何问题，请联系客服：\n\n"
            f"👨‍💼 {support_contact}\n\n"
            "客服在线时间：09:00 - 23:00"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 返回主菜单", callback_data="nav_back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    
    async def handle_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理我的订单按钮"""
        from src.config import settings
        
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        is_admin = user_id == getattr(settings, 'bot_owner_id', 0)
        
        if is_admin:
            # 管理员：提示使用 /orders 命令
            text = (
                "📋 <b>订单管理</b>\n\n"
                "请使用 /orders 命令进入订单管理系统。\n\n"
                "您可以查看、筛选和管理所有订单。"
            )
        else:
            # 普通用户：显示订单查询说明
            text = (
                "📋 <b>我的订单</b>\n\n"
                "暂不支持用户自助查询订单。\n\n"
                "如需查询订单状态，请联系客服提供订单号。"
            )
        
        keyboard = [
            [InlineKeyboardButton("📞 联系客服", callback_data="menu_support")],
            [InlineKeyboardButton("🔙 返回主菜单", callback_data="nav_back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    
    async def show_rates(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        显示实时U价（底部键盘按钮）
        调用 rates 服务获取 OKX C2C 汇率
        """
        from src.rates.service import fetch_usdt_cny_from_okx
        
        # 发送"正在获取"提示
        processing_msg = await update.message.reply_text("🔄 正在获取实时汇率...")
        
        try:
            # 获取汇率数据
            channel_prices = await fetch_usdt_cny_from_okx()
            
            # 构建显示文本
            lines = ["💵 <b>实时 USDT-CNY 汇率</b>\n"]
            lines.append("数据来源: OKX C2C\n")
            
            for channel, data in channel_prices.items():
                min_price = data.get("min_price")
                merchants = data.get("merchants", [])
                
                channel_name = self.CHANNEL_TITLES.get(channel, channel)
                icon = self.CHANNEL_ICONS.get(channel, "💰")
                
                if min_price:
                    lines.append(f"\n{icon} <b>{channel_name}</b>")
                    lines.append(f"最低价: <code>{min_price:.4f}</code> CNY")
                    
                    # 显示前几个商家
                    if merchants:
                        lines.append("商家报价:")
                        for i, m in enumerate(merchants[:self.MAX_MERCHANT_ROWS]):
                            nick = m.get("nickname", "商家")[:10]
                            price = m.get("price", 0)
                            lines.append(f"  {i+1}. {nick}: {price:.4f}")
                else:
                    lines.append(f"\n{icon} <b>{channel_name}</b>: 暂无数据")
            
            lines.append("\n\n⏰ 数据实时更新，仅供参考")
            
            text = "\n".join(lines)
            
        except Exception as e:
            logger.error(f"获取汇率失败: {e}", exc_info=True)
            text = "❌ <b>获取汇率失败</b>\n\n请稍后重试。"
        
        # 删除"正在获取"提示
        try:
            await processing_msg.delete()
        except Exception:
            pass
        
        # 发送结果
        keyboard = [[InlineKeyboardButton("🔙 返回主菜单", callback_data="nav_back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    
    async def show_clone_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        显示免费克隆信息（底部键盘按钮）
        """
        text = get_content("clone_message", default=(
            "🎁 <b>免费克隆</b>\n\n"
            "本功能暂未开放，敬请期待！\n\n"
            "如有需求，请联系客服咨询。"
        ))
        
        keyboard = [
            [InlineKeyboardButton("📞 联系客服", callback_data="menu_support")],
            [InlineKeyboardButton("🔙 返回主菜单", callback_data="nav_back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    
    async def show_support_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        显示联系客服信息（底部键盘按钮）
        """
        from src.config import settings
        
        # 从配置获取客服联系方式
        support_contact = getattr(settings, 'support_contact', '@your_support_bot')
        
        text = (
            "📞 <b>联系客服</b>\n\n"
            f"如有任何问题，请联系客服：\n\n"
            f"👨‍💼 {support_contact}\n\n"
            "客服在线时间：09:00 - 23:00"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 返回主菜单", callback_data="nav_back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
