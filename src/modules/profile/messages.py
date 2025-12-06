"""
个人中心消息模板
"""


class ProfileMessages:
    """个人中心消息模板"""

    PROFILE_MAIN = """<b>个人中心</b>

Name: <code>{name}</code>
UID: <code>{user_id}</code>
余额: <code>{balance:.3f}</code> USDT

请选择操作："""

    BALANCE_INFO = "当前余额: <code>{balance:.3f}</code> USDT"

    DEPOSIT_START = """💳 <b>充值 USDT</b>

请输入充值金额（USDT）：
最低充值：<code>1 USDT</code>

输入 /cancel 取消"""

    INVALID_AMOUNT = """金额无效，请重新输入

要求：
• 大于等于 1 USDT
• 最多3位小数

输入 /cancel 取消"""

    PAYMENT_INFO = """<b>充值信息</b>

金额: <code>{amount_with_suffix:.3f}</code> USDT
收款地址: <code>{receive_address}</code>

重要提示:
1. 请务必转账 <b>准确金额</b>
2. 网络: TRC20 (波场)
3. {timeout_minutes} 分钟内完成支付
4. 到账后自动入账

支付后系统会自动处理充值"""

    DEPOSIT_SUCCESS = """充值成功！

金额: <code>{amount:.3f}</code> USDT
当前余额: <code>{balance:.3f}</code> USDT"""

    DEPOSIT_HISTORY_EMPTY = "暂无充值记录"

    DEPOSIT_HISTORY = """<b>充值记录</b>

最近 {count} 条记录：
{records}"""

    DEPOSIT_RECORD_ITEM = """• {created_at}
  金额: {amount:.3f} USDT
  状态: {status}"""
