"""
TRX兑换键盘布局
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class TRXExchangeKeyboards:
    """TRX兑换键盘布局"""

    @staticmethod
    def payment_buttons(order_id: str):
        """支付确认键盘"""
        return InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✅ 已支付", callback_data=f"trx_paid_{order_id}")],
                [InlineKeyboardButton("❌ 取消", callback_data=f"trx_cancel_{order_id}")],
            ]
        )

    @staticmethod
    def skip_tx_hash():
        """跳过交易哈希键盘"""
        return InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("⏭️ 跳过", callback_data="trx_skip_hash")],
            ]
        )

    @staticmethod
    def back_to_main():
        """返回主菜单"""
        return InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔙 返回主菜单", callback_data="nav_back_to_main")],
            ]
        )

    @staticmethod
    def cancel_button():
        """取消按钮（用于输入阶段）"""
        return InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("❌ 取消", callback_data="trx_cancel_input")],
            ]
        )
