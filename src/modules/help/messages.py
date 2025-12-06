"""
帮助消息模板 - 动态价格版本
"""


class HelpMessages:
    """帮助消息模板"""
    
    MAIN_HELP = """<b>帮助中心</b>

欢迎使用！请选择帮助分类：

点击下方按钮查看详细说明"""

    BASIC_HELP = """<b>基础功能</b>

<b>可用命令：</b>
/start - 显示主菜单
/help - 显示帮助信息
/profile - 个人中心
/cancel - 取消当前操作

<b>操作说明：</b>
1. 点击主菜单按钮选择功能
2. 按照提示输入相关信息
3. 确认订单并完成支付
4. 系统自动处理并交付

<b>处理时效：</b>
• 支付确认：2-5 分钟
• Premium 交付：支付后即时
• 余额充值：支付后即时到账
• TRX 兑换：支付后 5-10 分钟"""

    @staticmethod
    def get_payment_help():
        """获取支付充值帮助（动态订单超时时间）"""
        try:
            from src.common.settings_service import get_order_timeout_minutes
            timeout = get_order_timeout_minutes()
        except Exception:
            timeout = 30
        
        return f"""<b>支付充值</b>

<b>支持的支付方式：</b>
• TRC20 USDT（波场网络）
• 三位小数唯一识别码

<b>支付步骤：</b>
1. 创建订单后获取支付地址
2. 使用钱包转账指定金额（含小数）
3. 等待区块确认（通常 1-2 分钟）
4. 系统自动完成交付

<b>重要提示：</b>
• 请务必转账<b>精确金额</b>（包括小数点后3位）
• 转账金额示例：10.123 USDT
• 金额不符将无法识别订单
• 订单有效期：{timeout} 分钟"""

    @staticmethod
    def get_services_help():
        """获取服务使用帮助（动态价格）"""
        try:
            from src.bot_admin.config_manager import config_manager
            price_3 = config_manager.get_price("premium_3_months", 10)
            price_6 = config_manager.get_price("premium_6_months", 18)
            price_12 = config_manager.get_price("premium_12_months", 30)
            energy_small = config_manager.get_price("energy_small", 3)
            energy_large = config_manager.get_price("energy_large", 6)
        except Exception:
            price_3, price_6, price_12 = 10, 18, 30
            energy_small, energy_large = 3, 6
        
        return f"""<b>服务使用</b>

<b>Premium 会员：</b>
• 3个月套餐：${price_3:.0f}
• 6个月套餐：${price_6:.0f}
• 12个月套餐：${price_12:.0f}
• 支持通过用户名或链接赠送

<b>余额充值：</b>
• 最低充值：$1
• 充值即时到账
• 可用于所有服务消费

<b>TRX 兑换：</b>
• 最低兑换：$5
• 最高兑换：$20,000
• 实时汇率
• 转账手续费由 Bot 承担

<b>能量服务：</b>
• 能量闪租：{energy_small:.0f}/{energy_large:.0f} TRX
• 笔数套餐：最低 5 USDT
• 闪兑能量：USDT 直兑"""

    @staticmethod
    def get_query_help():
        """获取查询功能帮助（动态限频时间）"""
        try:
            from src.common.settings_service import get_address_cooldown_minutes
            cooldown = get_address_cooldown_minutes()
        except Exception:
            cooldown = 30
        
        return f"""<b>查询功能</b>

<b>地址查询（免费）：</b>
• 查询波场地址信息
• 跳转区块链浏览器
• 限频：{cooldown}分钟/次/人
• 支持 Tronscan 和 OKLink"""

    FAQ = """<b>常见问题</b>

<b>Q: 支付后多久到账？</b>
A: 系统确认到账后 2-5 分钟自动处理

<b>Q: 金额转错了怎么办？</b>
A: 请联系客服处理

<b>Q: 订单过期了怎么办？</b>
A: 重新创建订单即可

<b>Q: 可以退款吗？</b>
A: 虚拟商品不支持退款"""

    QUICK_START = """<b>快速开始</b>

<b>5分钟上手指南：</b>

1️⃣ <b>充值余额</b>
   点击"个人中心" → "充值 USDT"

2️⃣ <b>购买 Premium</b>
   点击"飞机会员" → 选择套餐 → 输入用户名

3️⃣ <b>TRX 兑换</b>
   点击"TRX 兑换" → 输入金额 → 转账 USDT

<b>提示：</b> 支付时请确保金额精确到3位小数！"""
