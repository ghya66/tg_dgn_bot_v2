# Render.com 部署指南

## 概述

本文档介绍如何将 tg_dgn_bot_v2 部署到 Render.com 平台。

## 前置条件

- Render.com 账号
- GitHub 仓库访问权限
- 以下敏感信息：
  - Telegram Bot Token（从 @BotFather 获取）
  - USDT TRC20 收款地址
  - TRX 发币钱包私钥（生产环境）

## 服务架构

```
┌─────────────────────────────────────┐
│           Render.com                │
├─────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  │
│  │ Web Service │  │  Key Value   │  │
│  │  (Bot +     │  │   (Redis)    │  │
│  │  Webhook)   │  │   $10/月     │  │
│  │   $9/月     │  └──────────────┘  │
│  └─────────────┘                    │
│         │                           │
│         ▼                           │
│  ┌─────────────┐                    │
│  │ PostgreSQL  │                    │
│  │   $6/月     │                    │
│  └─────────────┘                    │
└─────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│         Telegram API                │
│     (Webhook: /webhook)             │
└─────────────────────────────────────┘
```

## 快速开始

### 1. 连接 GitHub 仓库

1. 登录 [Render Dashboard](https://dashboard.render.com)
2. 点击 "New" -> "Blueprint"
3. 连接 GitHub 仓库
4. 选择 `deploy/render` 分支
5. Render 会自动识别 `render.yaml` 配置

### 2. 创建 PostgreSQL 数据库

1. Dashboard -> New -> PostgreSQL
2. 配置：
   - Name: `tg-bot-postgres`
   - Region: `Singapore`
   - PostgreSQL Version: `16`
   - Plan: `Basic 256MB` ($6/月)
3. 创建完成后，记录 Internal Database URL

### 3. 创建 Redis 服务

1. Dashboard -> New -> Key Value
2. 配置：
   - Name: `tg-bot-redis`
   - Region: `Singapore`
   - Plan: `Starter` ($10/月)
3. 创建完成后，复制 Internal URL

### 4. 配置敏感环境变量

在 Web Service 的 Environment 页面设置以下变量：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `BOT_TOKEN` | Telegram Bot Token | `123456:ABC-DEF...` |
| `BOT_OWNER_ID` | 管理员 Telegram ID | `123456789` |
| `BOT_WEBHOOK_URL` | Webhook URL | `https://your-service.onrender.com/webhook` |
| `WEBHOOK_SECRET` | Webhook 签名密钥 | `your-secret-key` |
| `USDT_TRC20_RECEIVE_ADDR` | USDT 收款地址 | `T...` |
| `TRX_EXCHANGE_RECEIVE_ADDRESS` | TRX 兑换收款地址 | `T...` |
| `TRX_EXCHANGE_SEND_ADDRESS` | TRX 发币地址 | `T...` |
| `TRX_EXCHANGE_PRIVATE_KEY` | TRX 发币私钥 | `(敏感)` |
| `REDIS_CONNECTION_STRING` | Redis 连接字符串 | `redis://...` |
| `ENERGY_API_USERNAME` | 能量 API 用户名 | `your-username` |
| `ENERGY_API_PASSWORD` | 能量 API 密码 | `your-password` |

### 5. 触发部署

1. 保存环境变量配置
2. 点击 "Manual Deploy" -> "Deploy latest commit"
3. 观察部署日志

### 6. 验证服务

```bash
# 检查健康状态
curl https://your-service.onrender.com/health

# 检查 Telegram Webhook
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"

# 在 Telegram 中测试
# 向 Bot 发送 /start 命令
```

## 月度成本估算

| 服务 | 规格 | 费用 |
|------|------|------|
| Web Service | Starter (512MB) | $9 |
| PostgreSQL | Basic-256mb | $6 |
| Key Value | Starter (256MB) | $10 |
| **总计** | | **$25/月** |

## 故障排查

### Bot 无响应

1. 检查 Render 日志：Dashboard -> Service -> Logs
2. 验证 Webhook 状态：访问 `/health` 端点
3. 检查 Telegram Webhook 配置

### 数据库连接失败

1. 确认 `DATABASE_URL` 环境变量正确
2. 检查 PostgreSQL 服务状态
3. 验证 IP 白名单设置

### Redis 连接失败

1. 确认 `REDIS_CONNECTION_STRING` 格式正确
2. 检查 Key Value 服务状态

## 回滚操作

在 Render Dashboard 中：
1. 进入 Service -> Deploys
2. 找到之前的成功部署
3. 点击 "Redeploy"

## 相关链接

- [Render 文档](https://render.com/docs)
- [项目 README](../README.md)
- [API 参考](API_REFERENCE.md)

