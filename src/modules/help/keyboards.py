"""
帮助键盘布局
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class HelpKeyboards:
    """帮助键盘布局"""

    @staticmethod
    def main_menu():
        """帮助主菜单"""
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📖 基础功能", callback_data="help_basic"),
                    InlineKeyboardButton("💳 支付充值", callback_data="help_payment"),
                ],
                [
                    InlineKeyboardButton("🎁 服务使用", callback_data="help_services"),
                    InlineKeyboardButton("🔍 查询功能", callback_data="help_query"),
                ],
                [
                    InlineKeyboardButton("❓ 常见问题", callback_data="help_faq"),
                    InlineKeyboardButton("🚀 快速开始", callback_data="help_quick"),
                ],
                [InlineKeyboardButton("🏠 返回主菜单", callback_data="nav_back_to_main")],
            ]
        )

    @staticmethod
    def back_buttons():
        """返回按钮"""
        return InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔙 返回帮助", callback_data="help_back")],
                [InlineKeyboardButton("🏠 返回主菜单", callback_data="nav_back_to_main")],
            ]
        )
