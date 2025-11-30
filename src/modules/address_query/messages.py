"""
地址查询模块消息模板
使用HTML格式
"""


class AddressQueryMessages:
    """地址查询的所有消息模板"""
    
    # 开始查询
    START_QUERY = """🔍 <b>地址查询</b>

请输入 TRC20 地址，查询地址详情

示例: <code>TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH</code>"""

    # 限频提示
    RATE_LIMIT = """💡 您的查询过于频繁，请在 <b>{remaining_minutes}</b> 分钟后再试"""

    # 地址格式错误
    INVALID_ADDRESS = """❌ <b>地址无效</b>

请输入正确的 TRC20 地址"""

    # 查询中
    PROCESSING = """🔄 正在查询地址信息..."""

    # 查询结果
    QUERY_RESULT = """📍 <b>地址信息</b>

地址: <code>{address}</code>

💰 TRX 余额: <b>{trx_balance} TRX</b>
🪙 USDT 余额: <b>{usdt_balance} USDT</b>

{transactions_info}

如需再次查询，可稍后重新发送地址。"""

    # 查询结果（无API数据）
    QUERY_RESULT_NO_API = """📍 <b>地址信息</b>

地址: <code>{address}</code>

ℹ️ <i>API 暂时不可用，无法获取详细信息</i>

地址格式正确，您可以通过下方链接查看详情。

如需再次查询，可稍后重新发送地址。"""

    # 最近交易
    RECENT_TRANSACTIONS = """📊 <b>最近 5 笔交易:</b>

{transaction_list}"""

    # 无交易记录
    NO_TRANSACTIONS = """📊 <i>暂无最近交易记录</i>"""

    # 查询失败
    QUERY_ERROR = """❌ <b>查询失败</b>

系统处理您的请求时出现错误，请稍后重试。

如果问题持续存在，请联系客服。"""

    # 取消查询
    QUERY_CANCELLED = """❌ <b>已取消</b>

地址查询已取消

返回主菜单"""
