"""
TRX兑换消息模板
"""

class TRXExchangeMessages:
    """TRX兑换消息模板"""
    
    WELCOME = """💱 <b>TRX 闪兑</b>

24小时自动兑换，安全快捷！

最低兑换：<code>5 USDT</code>
最高兑换：<code>20,000 USDT</code>
到账时间：5-10 分钟
手续费：Bot 承担

请输入您要兑换的 USDT 数量："""
    
    INVALID_AMOUNT = """金额无效，请重新输入

要求：
• 最低 5 USDT
• 最高 20,000 USDT
• 支持小数

输入 /cancel 取消"""
    
    INPUT_ADDRESS = """请输入您的 TRX 收款地址：

地址要求：
• T 开头的波场地址
• 34位字符

输入 /cancel 取消"""
    
    INVALID_ADDRESS = """地址无效，请重新输入

要求：
• T 开头
• 34位字符
• 波场 TRON 地址

输入 /cancel 取消"""
    
    PAYMENT_INFO = """<b>TRX 兑换订单</b>

订单号: <code>{order_id}</code>
兑换金额: <code>{usdt_amount:.3f}</code> USDT
预计获得: <code>{trx_amount:.2f}</code> TRX
汇率: 1 TRX = {rate:.4f} USDT
收款地址: <code>{receive_address}</code>

<b>支付信息</b>
请转账: <code>{payment_amount:.3f}</code> USDT
到地址: <code>{payment_address}</code>

倒计时: {timeout_minutes} 分钟

⚠️ 请务必转账 <b>准确金额</b>，金额必须精确到3位小数！"""
    
    PAYMENT_EXPIRED = """订单已过期

请重新发起兑换"""
    
    WAITING_TX_HASH = """已确认支付

请输入交易哈希（可选）：
或点击"跳过"继续"""
    
    ORDER_SUBMITTED = """订单已提交

订单号: <code>{order_id}</code>
交易哈希: <code>{tx_hash}</code>

TRX 将在 5-10 分钟内到账
如有问题请联系客服"""
    
    ORDER_SKIP_HASH = """订单已提交

订单号: <code>{order_id}</code>

TRX 将在确认支付后 5-10 分钟内到账
如有问题请联系客服"""
