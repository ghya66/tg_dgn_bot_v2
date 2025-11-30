# 🏗️ TG DGN Bot V2 架构文档

> 更新时间: 2025-11-30
> 版本: v2.2.0

## 📁 完整目录结构

```
src/
│
├── bot_v2.py                         # 🚀 主程序入口
├── config.py                         # ⚙️ 配置管理（环境变量）
├── database.py                       # 💾 数据库连接和模型
├── models.py                         # 📦 通用数据模型
│
├── api/                              # 🌐 REST API 层
│   ├── __init__.py
│   ├── app.py                        # FastAPI 应用实例
│   ├── auth.py                       # API 认证
│   ├── middleware.py                 # 中间件
│   └── routes.py                     # API 路由定义
│
├── bot_admin/                        # 👑 Bot 管理功能
│   ├── __init__.py
│   ├── audit_log.py                  # 审计日志
│   ├── config_manager.py             # 配置管理器
│   ├── handler.py                    # 管理命令处理
│   ├── menus.py                      # 管理菜单
│   ├── middleware.py                 # 权限中间件
│   └── stats_manager.py              # 统计管理
│
├── clients/                          # 🔌 外部 API 客户端
│   ├── __init__.py
│   └── tron.py                       # TRON 区块链客户端
│
├── common/                           # 🔧 公共组件
│   ├── __init__.py
│   ├── content_service.py            # 内容服务（欢迎语等）
│   ├── conversation_wrapper.py       # 对话包装器
│   ├── db_manager.py                 # 数据库上下文管理
│   ├── decorators.py                 # 装饰器
│   ├── error_collector.py            # 错误收集
│   ├── http_client.py                # HTTP 客户端
│   ├── http_utils.py                 # HTTP 工具
│   ├── navigation_manager.py         # 导航管理器
│   ├── redis_helper.py               # Redis 辅助
│   └── settings_service.py           # 设置服务
│
├── core/                             # 🎯 核心基础设施
│   ├── __init__.py
│   ├── base.py                       # BaseModule 基类
│   ├── formatter.py                  # HTML 消息格式化
│   ├── registry.py                   # 模块注册中心
│   └── state_manager.py              # 状态管理器
│
├── modules/                          # 📦 标准化模块（核心业务）
│   ├── __init__.py
│   │
│   ├── menu/                         # 📱 主菜单模块 (priority=0)
│   │   ├── __init__.py
│   │   ├── handler.py                # MainMenuModule
│   │   ├── keyboards.py              # 主菜单按钮
│   │   ├── messages.py               # 消息模板
│   │   └── states.py                 # 状态定义
│   │
│   ├── health/                       # 🏥 健康检查模块 (priority=1)
│   │   ├── __init__.py
│   │   ├── handler.py                # HealthModule
│   │   └── service.py                # 健康检查服务
│   │
│   ├── premium/                      # ⭐ Premium会员模块 (priority=2)
│   │   ├── __init__.py
│   │   ├── handler.py                # PremiumModule
│   │   ├── handler_v2.py             # Premium 处理器 V2
│   │   ├── delivery.py               # 交付服务
│   │   ├── recipient_parser.py       # 收件人解析
│   │   ├── security.py               # 安全服务
│   │   ├── user_verification.py      # 用户验证
│   │   ├── keyboards.py              # 套餐选择按钮
│   │   ├── messages.py               # 支付引导消息
│   │   └── states.py                 # 购买流程状态
│   │
│   ├── energy/                       # ⚡ 能量兑换模块 (priority=3)
│   │   ├── __init__.py
│   │   ├── handler.py                # EnergyModule
│   │   ├── client.py                 # trxno.com API 客户端
│   │   ├── models.py                 # 数据模型 (Pydantic V2)
│   │   ├── keyboards.py              # 套餐选择按钮
│   │   ├── messages.py               # 支付引导消息
│   │   └── states.py                 # 购买流程状态
│   │
│   ├── address_query/                # 🔍 地址查询模块 (priority=4)
│   │   ├── __init__.py
│   │   ├── handler.py                # AddressQueryModule
│   │   ├── validator.py              # 地址验证器
│   │   ├── explorer.py               # 浏览器链接生成
│   │   ├── keyboards.py              # 查询按钮
│   │   ├── messages.py               # 查询结果消息
│   │   └── states.py                 # 查询流程状态
│   │
│   ├── profile/                      # 👤 个人中心模块 (priority=5)
│   │   ├── __init__.py
│   │   ├── handler.py                # ProfileModule
│   │   ├── keyboards.py              # 钱包/充值按钮
│   │   ├── messages.py               # 余额显示消息
│   │   └── states.py                 # 充值流程状态
│   │
│   ├── trx_exchange/                 # 💱 TRX闪兑模块 (priority=6)
│   │   ├── __init__.py
│   │   ├── handler.py                # TRXExchangeModule
│   │   ├── config.py                 # 兑换配置
│   │   ├── rate_manager.py           # 汇率管理
│   │   ├── trx_sender.py             # TRX 发送器
│   │   ├── payment_monitor.py        # 支付监控
│   │   ├── models.py                 # 数据库模型
│   │   ├── keyboards.py              # 兑换按钮
│   │   ├── messages.py               # 汇率/确认消息
│   │   └── states.py                 # 兑换流程状态
│   │
│   ├── admin/                        # 🔧 管理面板模块 (priority=10)
│   │   ├── __init__.py
│   │   └── handler.py                # AdminModule
│   │
│   ├── orders/                       # 📋 订单查询模块 (priority=11)
│   │   ├── __init__.py
│   │   ├── handler.py                # OrdersModule
│   │   └── query_handler.py          # 订单查询核心逻辑
│   │
│   └── help/                         # ❓ 帮助中心模块 (priority=12)
│       ├── __init__.py
│       ├── handler.py                # HelpModule
│       ├── keyboards.py              # FAQ按钮
│       └── messages.py               # 帮助文档（动态价格）
│
├── payments/                         # 💳 支付处理
│   ├── __init__.py
│   ├── amount_calculator.py          # 金额计算
│   ├── order.py                      # 订单管理
│   └── suffix_manager.py             # 唯一金额后缀
│
├── rates/                            # 💹 汇率服务
│   ├── __init__.py
│   └── jobs.py                       # 汇率刷新任务
│
├── services/                         # 🎯 业务服务层
│   ├── __init__.py
│   ├── address_service.py            # 地址服务
│   ├── config_service.py             # 配置服务
│   ├── energy_service.py             # 能量服务
│   ├── payment_service.py            # 支付服务
│   ├── trx_service.py                # TRX 服务
│   └── wallet_service.py             # 钱包服务
│
├── tasks/                            # ⏰ 后台任务
│   ├── __init__.py
│   └── order_expiry.py               # 订单过期检查
│
├── utils/                            # 🛠️ 工具函数
│   └── __init__.py
│
├── wallet/                           # 💰 钱包功能
│   ├── __init__.py
│   └── balance.py                    # 余额管理
│
└── webhook/                          # 🔗 Webhook 处理
    ├── __init__.py
    └── handler.py                    # 支付回调处理
```

## 📊 模块优先级

| 优先级 | 模块 | 说明 |
|--------|------|------|
| 0 | menu | 主菜单，最先加载 |
| 1 | health | 健康检查 |
| 2 | premium | Premium会员 |
| 3 | energy | 能量兑换 |
| 4 | address_query | 地址查询 |
| 5 | profile | 个人中心 |
| 6 | trx_exchange | TRX闪兑 |
| 10 | admin | 管理面板 |
| 11 | orders | 订单查询 |
| 12 | help | 帮助中心 |

## 🔄 数据流

```
用户请求 → Telegram API → bot_v2.py → ModuleRegistry → 对应模块 → 响应
                                           ↓
                                      BaseModule
                                           ↓
                              handler.py / keyboards.py / messages.py
```

## 📁 测试目录

```
tests/
├── test_health.py                    # 健康检查测试
├── test_orders_module.py             # 订单模块测试
├── test_help_module.py               # 帮助模块测试
├── test_trx_exchange_auto.py         # TRX 兑换测试
├── test_recipient_parser.py          # 收件人解析测试
├── test_premium_*.py                 # Premium 相关测试
└── ...                               # 其他测试
```
