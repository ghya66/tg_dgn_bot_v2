# 🤖 TG DGN Bot V2

<p align="center">
  <strong>一个功能丰富的 Telegram 多功能服务 Bot</strong>
</p>

<p align="center">
  <a href="https://github.com/ghya66/tg_dgn_bot_v2/actions/workflows/ci.yml"><img src="https://github.com/ghya66/tg_dgn_bot_v2/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.11%20|%203.12-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Telegram-Bot%20API-blue.svg" alt="Telegram">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Version-2.0.2-orange.svg" alt="Version">
</p>

---

## 📖 项目简介

TG DGN Bot V2 是一个基于 Python 的 Telegram Bot，提供以下核心服务：

- 💎 **Premium 会员开通** - 自动为用户开通 Telegram Premium
- ⚡ **能量兑换** - TRON 网络能量租赁服务
- 💱 **TRX 闪兑** - USDT 兑换 TRX 服务
- 🔍 **地址查询** - 波场地址信息查询
- 👤 **余额管理** - 用户钱包充值与余额查询

---

## ✨ 功能特性

| 功能 | 描述 | 状态 |
|------|------|------|
| 💎 Premium会员 | 支持为自己或他人开通 3/6/12 个月 Premium | ✅ |
| ⚡ 能量兑换 | 时长能量、笔数套餐、闪兑三种模式 | ✅ |
| 💱 TRX闪兑 | USDT → TRX 实时汇率兑换 | ✅ |
| 🔍 地址查询 | 波场地址余额查询，支持限频控制 | ✅ |
| 👤 个人中心 | 余额充值、余额查询、充值记录 | ✅ |
| 📋 订单管理 | 查看历史订单和订单状态 | ✅ |
| 🔧 管理后台 | 动态配置、数据统计、用户管理 | ✅ |
| ❓ 帮助中心 | 使用指南和常见问题 | ✅ |

---

## 🛠️ 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 语言 | Python | 3.11+ |
| Bot 框架 | python-telegram-bot | 20.x |
| Web 框架 | FastAPI | 0.100+ |
| ORM | SQLAlchemy | 2.0+ |
| 数据库 | SQLite | 3.x |
| 缓存 | Redis | 7.0+ |
| 定时任务 | APScheduler | 3.x |
| 数据库迁移 | Alembic | 1.x |

---

## 📋 前置要求

- ✅ Python 3.11+
- ✅ Redis 7.0+
- ✅ Telegram Bot Token（通过 [@BotFather](https://t.me/BotFather) 创建）
- ✅ 波场钱包地址（用于接收 USDT/TRX）

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/tg_dgn_bot_v2.git
cd tg_dgn_bot_v2
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写必要配置：

```bash
# 必填项
BOT_TOKEN=your_bot_token_here
USDT_TRC20_RECEIVE_ADDR=TYourReceiveAddress
WEBHOOK_SECRET=your_secret_key_32_chars
BOT_OWNER_ID=123456789

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# 数据库配置
DATABASE_URL=sqlite:///./data/tg_bot.db
```

### 4. 启动 Redis

```bash
# Ubuntu/Debian
sudo apt-get install redis-server && redis-server

# macOS
brew install redis && redis-server

# Windows (WSL)
sudo service redis-server start
```

### 5. 启动 Bot

```bash
# 使用启动脚本
./scripts/start_bot.sh

# 或直接运行
python -m src.bot_v2
```

### 6. 验证部署

在 Telegram 中找到你的 Bot，发送 `/start`，应该看到欢迎消息和功能按钮。

---

## 📁 项目结构

```
tg_dgn_bot_v2/
├── src/                          # 源代码目录
│   ├── bot_v2.py                 # 🚀 主程序入口
│   ├── config.py                 # ⚙️ 配置管理
│   ├── database.py               # 💾 数据库连接
│   │
│   ├── modules/                  # 📦 业务模块
│   │   ├── menu/                 # 主菜单
│   │   ├── premium/              # Premium会员
│   │   ├── energy/               # 能量兑换
│   │   ├── trx_exchange/         # TRX闪兑
│   │   ├── address_query/        # 地址查询
│   │   ├── profile/              # 个人中心
│   │   ├── orders/               # 订单管理
│   │   ├── admin/                # 管理后台
│   │   ├── help/                 # 帮助中心
│   │   └── health/               # 健康检查
│   │
│   ├── core/                     # 🎯 核心基础设施
│   │   ├── base.py               # BaseModule 基类
│   │   ├── registry.py           # 模块注册中心
│   │   ├── formatter.py          # 消息格式化
│   │   └── state_manager.py      # 状态管理器
│   │
│   ├── api/                      # 🌐 REST API
│   ├── bot_admin/                # 👑 管理功能
│   ├── common/                   # 🔧 公共组件
│   ├── payments/                 # 💳 支付处理
│   ├── services/                 # 🎯 业务服务
│   ├── tasks/                    # ⏰ 后台任务
│   └── wallet/                   # 💰 钱包功能
│
├── tests/                        # 测试代码
├── scripts/                      # 辅助脚本
├── migrations/                   # 数据库迁移
├── docs/                         # 项目文档
├── data/                         # 数据目录
├── requirements.txt              # Python 依赖
├── alembic.ini                   # Alembic 配置
└── .env.example                  # 环境变量模板
```

---

## ⚙️ 配置说明

### 必填配置

| 变量 | 说明 | 示例 |
|------|------|------|
| `BOT_TOKEN` | Telegram Bot Token | `123456789:ABC...` |
| `USDT_TRC20_RECEIVE_ADDR` | USDT 收款地址 | `TXxx...xxx` |
| `WEBHOOK_SECRET` | 签名验证密钥 | 32位随机字符串 |
| `BOT_OWNER_ID` | 管理员 Telegram ID | `123456789` |

### 可选配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `REDIS_HOST` | Redis 主机 | `localhost` |
| `REDIS_PORT` | Redis 端口 | `6379` |
| `DATABASE_URL` | 数据库连接 | `sqlite:///./data/tg_bot.db` |
| `ORDER_TIMEOUT_MINUTES` | 订单超时时间 | `30` |
| `ADDRESS_QUERY_RATE_LIMIT_MINUTES` | 地址查询限频 | `1` |
| `TRON_EXPLORER` | 区块链浏览器 | `tronscan` |

### 生产环境配置

| 变量 | 说明 | 建议值 |
|------|------|--------|
| `ENV` | 环境标识 | `prod` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `LOG_FORMAT` | 日志格式（便于日志收集） | `json` |
| `SUPPORT_CONTACT` | 客服联系方式 | `@your_support` |
| `API_KEYS` | API 认证密钥（逗号分隔） | `key1,key2` |
| `TRX_EXCHANGE_TEST_MODE` | TRX 发币测试模式 | `false` |

---

## 🧪 测试

```bash
# 运行全部测试
pytest tests/ -v

# 跳过 Redis 集成测试
pytest tests/ -m "not redis" -v

# 查看测试覆盖率
pytest tests/ --cov=src --cov-report=html
```

---

## 📊 命令列表

### 用户命令

| 命令 | 说明 |
|------|------|
| `/start` | 启动 Bot，显示主菜单 |
| `/premium` | 进入 Premium 开通 |
| `/energy` | 进入能量兑换 |
| `/trx` | 进入 TRX 闪兑 |
| `/query` | 进入地址查询 |
| `/profile` | 进入个人中心 |
| `/help` | 查看帮助文档 |

### 管理员命令

| 命令 | 说明 |
|------|------|
| `/admin` | 进入管理后台 |
| `/orders` | 查看订单列表 |
| `/health` | 系统健康检查 |

---

## 🔐 安全建议

1. **保护配置文件**
   ```bash
   chmod 600 .env
   ```

2. **生成强密钥**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **定期备份数据库**
   ```bash
   cp data/tg_bot.db backup/tg_bot_$(date +%Y%m%d).db
   ```

4. **确保 .env 不被提交**
   - 已在 `.gitignore` 中配置

5. **生产部署检查清单**
   - [ ] `BOT_TOKEN` - 从 @BotFather 获取的真实 Token
   - [ ] `BOT_OWNER_ID` - 管理员的 Telegram User ID
   - [ ] `TRX_EXCHANGE_TEST_MODE=false` - 关闭测试模式启用真实转账
   - [ ] `TRX_EXCHANGE_PRIVATE_KEY` - TRX 发币钱包私钥
   - [ ] `USDT_TRC20_RECEIVE_ADDR` - USDT 收款地址
   - [ ] `WEBHOOK_SECRET` - 支付回调签名密钥
   - [ ] 执行数据库迁移：`alembic upgrade head`

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| [QUICK_START.md](docs/QUICK_START.md) | 快速上手指南 |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | 部署和测试指南 |
| [API_REFERENCE.md](docs/API_REFERENCE.md) | REST API 文档 |
| [DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | 数据库结构 |
| [ADMIN_PANEL_GUIDE.md](docs/ADMIN_PANEL_GUIDE.md) | 管理后台指南 |
| [CODE_REVIEW_REPORT.md](docs/CODE_REVIEW_REPORT.md) | 代码审查报告 |

---

## 🔄 更新日志

### v2.0.2 (2025-12-06) - 生产就绪版本 🚀

**核心功能**
- ✅ 能量订单状态同步任务：自动每5分钟从 trxfast.com 同步订单状态
- ✅ 修复能量 API 订单查询端点：`/api/order` → `/api/orderinfo`
- ✅ 添加订单完成/失败用户通知功能
- ✅ 结构化日志支持（JSON/Text 格式）
- ✅ 数据库会话管理统一化

**生产部署修复**
- ✅ 修复能量同步任务 URL 参数：`energy_sync.py` 添加 `base_url`/`backup_url` 参数传递
- ✅ 完善 `.env.example`：添加生产环境配置项（ENV、LOG_LEVEL、SUPPORT_CONTACT、API_KEYS）
- ✅ 添加生产环境安全检查清单

**数据库迁移**
- ✅ 新增迁移脚本 `004_user_confirmation_fields.py`
- ✅ `energy_orders` 表：添加 `user_tx_hash`、`user_confirmed_at` 字段
- ✅ `orders` 表：添加 `user_tx_hash`、`user_confirmed_at`、`user_confirm_source` 字段
- ✅ `premium_orders` 表：添加 `fail_reason` 字段

**测试覆盖**
- ✅ 新增能量同步任务 URL 参数验证测试
- ✅ 全量测试通过：758 passed, 2 skipped

### v2.0.1 (2025-12-06)

- ✅ Premium 方案A：直接信任用户名格式（优化用户体验）
- ✅ 实时汇率显示优化：支持渠道切换（所有/银行卡/支付宝/微信）
- ✅ 汇率刷新频率调整为每12小时
- ✅ 数据库字段修复（energy_orders.expires_at, trx_exchange_orders.send_tx_hash）

### v2.0.0 (2025-12-05)

- ✅ 完成模块化架构重构
- ✅ 新增 TRX 闪兑功能
- ✅ 新增管理后台
- ✅ 完成两轮代码审查修复
- ✅ 添加对话超时处理
- ✅ 统一状态机规范

### v1.0.0 (2025-11-26)

- 🎉 初始版本发布
- ✅ Premium 会员开通
- ✅ 能量兑换
- ✅ 地址查询
- ✅ 余额管理

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 📞 联系方式

- **Issues**: [GitHub Issues](https://github.com/your-repo/tg_dgn_bot_v2/issues)
- **Telegram**: [@your_support_bot](https://t.me/your_support_bot)

---

<p align="center">
  Made with ❤️ by TG DGN Bot Team
</p>
