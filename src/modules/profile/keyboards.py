"""
个人中心键盘布局
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class ProfileKeyboards:
    """个人中心键盘布局"""

    @staticmethod
    def main_menu():
        """主菜单键盘"""
        return InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("💰 余额查询", callback_data="profile_balance")],
                [InlineKeyboardButton("💵 充值 USDT", callback_data="profile_deposit")],
                [InlineKeyboardButton("📜 充值记录", callback_data="profile_history")],
            ]
        )

    @staticmethod
    def back_to_profile():
        """返回个人中心"""
        return InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔙 返回个人中心", callback_data="profile_back")],
                [InlineKeyboardButton("🏠 返回主菜单", callback_data="nav_back_to_main")],
            ]
        )
