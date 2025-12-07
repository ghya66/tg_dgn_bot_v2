# 🚀 tg_dgn_bot_v2 生产环境部署指南

本文档提供完整的生产环境部署步骤，适用于全新服务器部署。

---

## 📋 系统要求

| 组件 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Docker | 20.10+ | 24.0+ |
| Docker Compose | 2.0+ | 2.20+ |
| 操作系统 | Ubuntu 20.04 / CentOS 8 | Ubuntu 22.04 LTS |
| 内存 | 1GB | 2GB+ |
| 存储 | 5GB | 10GB+ |

> ⚠️ **推荐使用 Docker 部署**，无需单独安装 Python 或 Redis。

---

## 📦 部署步骤

### 第一步：解压部署包

```bash
# 上传 ZIP 文件到服务器后
unzip tg_dgn_bot_v2_prod_*.zip
cd tg_dgn_bot_v2_prod
```

### 第二步：配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
nano .env   # 或使用 vim/vi
```

**必须填写的配置项（4个）：**

```ini
# ========== 必填项 ==========

# 从 @BotFather 获取的 Bot Token
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# 管理员 Telegram User ID（获取方法见下文）
BOT_OWNER_ID=123456789

# USDT TRC20 收款地址（波场网络）
USDT_TRC20_RECEIVE_ADDR=TXxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 支付回调签名密钥（随机生成）
WEBHOOK_SECRET=your_random_secret_key_at_least_32_chars
```

**生产环境必改配置：**

```ini
# ========== 生产环境设置 ==========

# 环境标识（必须改为 prod）
ENV=prod

# 启用 Webhook 模式（生产环境必须为 true）
USE_WEBHOOK=true

# Webhook URL（替换为实际域名）
BOT_WEBHOOK_URL=https://your-domain.com/webhook

# 关闭 TRX 兑换测试模式（启用真实转账）
TRX_EXCHANGE_TEST_MODE=false
```

### 第三步：创建数据目录

```bash
# 创建数据持久化目录
mkdir -p data

# 设置目录权限
chmod 755 data
```

### 第四步：启动服务

```bash
# 构建并启动（后台运行）
docker compose up -d

# 查看启动日志
docker compose logs -f bot_primary

# 确认服务状态
docker compose ps
```

**预期输出：**
```
NAME                    STATUS              PORTS
tg_dgn_bot-redis-1      Up                  0.0.0.0:6379->6379/tcp
tg_dgn_bot-bot_primary  Up                  0.0.0.0:8080->8080/tcp
```

### 第五步：初始化配置数据

首次部署必须执行以下初始化脚本：

```bash
# 初始化价格配置和系统设置
docker compose exec bot_primary python scripts/init_admin_config.py

# 初始化文案配置
docker compose exec bot_primary python scripts/init_content_configs.py
```

**预期输出：**
```
✅ 数据库初始化完成
✅ 默认配置已写入数据库
💎 Premium 会员价格：
  3个月：$17.0 USDT
  6个月：$25.0 USDT
  12个月：$40.0 USDT
✅ 初始化完成！
```

### 第六步：验证部署

1. **Telegram 测试**：
   - 向 Bot 发送 `/start`，确认收到欢迎消息
   - 发送 `/admin`（使用 BOT_OWNER_ID 对应的账号），确认进入管理面板

2. **健康检查**：
   ```bash
   # 检查容器状态
   docker compose ps
   
   # 检查 Bot 日志
   docker compose logs bot_primary --tail=20
   
   # 检查 Redis 连接
   docker compose exec redis redis-cli ping
   # 预期输出：PONG
   ```

---

## ⚙️ 配置详解

### 必填配置项

| 配置项 | 说明 | 获取方式 |
|--------|------|----------|
| `BOT_TOKEN` | Bot 令牌 | 在 Telegram 中联系 @BotFather，发送 `/newbot` 创建 |
| `BOT_OWNER_ID` | 管理员 ID | 在 Telegram 中联系 @userinfobot，发送任意消息获取 |
| `USDT_TRC20_RECEIVE_ADDR` | 收款地址 | 波场钱包地址（T 开头，34 位） |
| `WEBHOOK_SECRET` | 签名密钥 | 随机生成：`openssl rand -hex 32` |

### 可选配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `TRX_EXCHANGE_RECEIVE_ADDRESS` | TRX 兑换收 USDT 地址 | (空) |
| `TRX_EXCHANGE_SEND_ADDRESS` | TRX 兑换发 TRX 地址 | (空) |
| `TRX_EXCHANGE_PRIVATE_KEY` | TRX 发币钱包私钥 | (空) |
| `ENERGY_API_USERNAME` | 能量 API 账号 | (空) |
| `ENERGY_API_PASSWORD` | 能量 API 密码 | (空) |
| `TRON_API_KEY` | TronGrid API 密钥 | (空) |
| `SUPPORT_CONTACT` | 客服联系方式 | @your_support_bot |
| `ORDER_TIMEOUT_MINUTES` | 订单超时时间 | 30 分钟 |

---

## 🔧 管理命令

### 日常运维

```bash
# 查看服务状态
docker compose ps

# 查看实时日志
docker compose logs -f bot_primary

# 重启服务
docker compose restart bot_primary

# 停止所有服务
docker compose down

# 更新并重启（代码更新后）
docker compose build --no-cache bot_primary
docker compose up -d bot_primary
```

### 数据库管理

```bash
# 进入容器执行 SQLite 命令
docker compose exec bot_primary sqlite3 /app/data/tg_bot.db

# 查看所有表
.tables

# 查看订单统计
SELECT status, COUNT(*) FROM premium_orders GROUP BY status;

# 退出
.exit
```

### 备份数据

```bash
# 备份数据库
docker compose exec bot_primary cp /app/data/tg_bot.db /app/data/tg_bot.db.backup

# 导出到宿主机
docker cp $(docker compose ps -q bot_primary):/app/data/tg_bot.db ./backup_$(date +%Y%m%d).db
```

---

## 🔐 安全建议

### 1. 配置文件权限

```bash
# 限制 .env 文件访问权限
chmod 600 .env
```

### 2. 防火墙配置

```bash
# 仅开放必要端口
# Bot Webhook 端口
ufw allow 8080/tcp

# 如果 Redis 不需要外部访问
ufw deny 6379/tcp
```

### 3. 定期备份

建议每天自动备份数据库：

```bash
# 添加到 crontab
crontab -e

# 每天凌晨 2 点备份
0 2 * * * docker cp $(docker compose ps -q bot_primary):/app/data/tg_bot.db /backup/tg_bot_$(date +\%Y\%m\%d).db
```

### 4. 敏感信息保护

- ⚠️ **绝不要**将 `.env` 文件提交到版本控制
- ⚠️ **绝不要**在日志中打印私钥或 Token
- ⚠️ 定期更换 `WEBHOOK_SECRET` 密钥

---

## 🐛 常见问题

### Q1: Bot 启动失败

**检查步骤：**
```bash
# 查看详细错误日志
docker compose logs bot_primary

# 常见原因：
# 1. BOT_TOKEN 错误 → 检查 Token 是否正确
# 2. .env 文件格式错误 → 检查是否有多余空格或引号
# 3. 端口被占用 → 修改 BOT_SERVICE_PORT
```

### Q2: 管理面板无法访问

**检查步骤：**
```bash
# 确认 BOT_OWNER_ID 设置正确
grep BOT_OWNER_ID .env

# 确认使用正确的 Telegram 账号发送 /admin
```

### Q3: 支付未到账

**检查步骤：**
1. 确认 `USDT_TRC20_RECEIVE_ADDR` 配置正确
2. 确认转账金额与订单金额完全一致（包括小数）
3. 检查订单是否已过期（默认 30 分钟）

### Q4: TRX 兑换不工作

**检查步骤：**
1. 确认 `TRX_EXCHANGE_TEST_MODE=false`
2. 确认已配置 `TRX_EXCHANGE_PRIVATE_KEY`
3. 确认发币钱包有足够 TRX 余额

---

## 📊 监控和告警

### 健康检查端点

Bot 提供健康检查接口：

```bash
# 检查 Bot 健康状态
curl http://localhost:8080/health
```

### 日志级别调整

```ini
# .env 中设置日志级别
LOG_LEVEL=INFO    # 生产环境推荐
LOG_LEVEL=DEBUG   # 调试时使用
```

---

## 📞 技术支持

如遇问题，请准备以下信息后联系技术支持：

1. 错误日志（`docker compose logs bot_primary --tail=100`）
2. 系统环境（操作系统、Docker 版本）
3. 配置文件（删除敏感信息后的 .env）

---

## 📝 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 2.0.2 | 2025-12-07 | 初始生产版本，支持配置热更新 |

---

**部署完成后，建议进行完整功能测试，确保所有模块正常工作。**

