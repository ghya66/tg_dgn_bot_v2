# 数据库表结构文档

> 生成时间: 2025-11-27

## 概览

| 表名 | 描述 | 主键 |
|------|------|------|
| `users` | 用户表 | `user_id` |
| `orders` | 主订单表 | `order_id` |
| `deposit_orders` | 充值订单表 | `order_id` |
| `trx_exchange_orders` | TRX兑换订单表 | `order_id` |
| `premium_orders` | Premium订单表 | `order_id` |
| `energy_orders` | 能量订单表 | `order_id` |
| `debit_records` | 扣费记录表 | `id` |
| `suffix_allocations` | 后缀分配表 | `suffix` |
| `address_query_logs` | 地址查询限频表 | `user_id` |
| `user_bindings` | 用户绑定表 | `id` |

---

## 表结构详情

### 1. users - 用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `user_id` | INTEGER | PRIMARY KEY | Telegram用户ID |
| `username` | VARCHAR(64) | NULLABLE | 用户名 |
| `balance_micro_usdt` | INTEGER | NOT NULL DEFAULT 0 | 余额(微USDT, ×10^6) |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |

---

### 2. orders - 主订单表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `order_id` | VARCHAR(36) | PRIMARY KEY | 订单ID (UUID) |
| `user_id` | INTEGER | NOT NULL INDEX | 用户ID |
| `order_type` | VARCHAR(32) | NOT NULL | 订单类型(premium/deposit/trx_exchange/energy) |
| `base_amount` | INTEGER | NOT NULL | 基础金额(微USDT) |
| `unique_suffix` | INTEGER | NULLABLE | 唯一后缀(1-999) |
| `amount_usdt` | INTEGER | NOT NULL | 总金额(微USDT) |
| `status` | VARCHAR(20) | NOT NULL DEFAULT 'PENDING' | 状态 |
| `recipient` | VARCHAR(255) | NULLABLE | 收件人/目标地址 |
| `premium_months` | INTEGER | NULLABLE | Premium月数 |
| `tx_hash` | VARCHAR(100) | NULLABLE | 交易哈希 |
| `user_tx_hash` | VARCHAR(100) | NULLABLE | 用户确认交易哈希 |
| `user_confirmed_at` | DATETIME | NULLABLE | 用户确认时间 |
| `user_confirm_source` | VARCHAR(32) | NULLABLE | 确认来源 |
| `created_at` | DATETIME | NOT NULL INDEX | 创建时间 |
| `paid_at` | DATETIME | NULLABLE | 支付时间 |
| `delivered_at` | DATETIME | NULLABLE | 交付时间 |
| `expires_at` | DATETIME | NOT NULL | 过期时间 |

**索引:**
- `idx_orders_type_status` (order_type, status)
- `idx_orders_user_status` (user_id, status)
- `idx_orders_created` (created_at)

---

### 3. deposit_orders - 充值订单表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `order_id` | VARCHAR(36) | PRIMARY KEY | 订单ID |
| `user_id` | INTEGER | NOT NULL INDEX | 用户ID |
| `base_amount` | FLOAT | NOT NULL | 基础金额 |
| `unique_suffix` | INTEGER | NOT NULL | 唯一后缀(1-999) |
| `total_amount` | FLOAT | NOT NULL | 总金额 |
| `amount_micro_usdt` | INTEGER | NOT NULL | 微USDT金额 |
| `status` | VARCHAR(20) | NOT NULL DEFAULT 'PENDING' | 状态 |
| `tx_hash` | VARCHAR(100) | NULLABLE | 交易哈希 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `paid_at` | DATETIME | NULLABLE | 支付时间 |
| `expires_at` | DATETIME | NOT NULL | 过期时间 |

**索引:**
- `idx_user_status` (user_id, status)
- `idx_suffix` (unique_suffix)

---

### 4. trx_exchange_orders - TRX兑换订单表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `order_id` | VARCHAR(32) | PRIMARY KEY | 订单ID |
| `user_id` | INTEGER | NOT NULL INDEX | 用户ID |
| `usdt_amount` | DECIMAL(10,3) | NOT NULL | USDT金额(含3位后缀) |
| `trx_amount` | DECIMAL(20,6) | NOT NULL | TRX数量 |
| `exchange_rate` | DECIMAL(10,6) | NOT NULL | 汇率(锁定) |
| `recipient_address` | VARCHAR(64) | NOT NULL | 用户TRX接收地址 |
| `payment_address` | VARCHAR(64) | NOT NULL | Bot USDT接收地址 |
| `status` | VARCHAR(20) | NOT NULL DEFAULT 'PENDING' | 状态 |
| `tx_hash` | VARCHAR(128) | NULLABLE | TRX转账哈希 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `paid_at` | DATETIME | NULLABLE | 支付时间 |
| `transferred_at` | DATETIME | NULLABLE | TRX转账时间 |
| `expires_at` | DATETIME | NULLABLE | 过期时间 |

---

### 5. premium_orders - Premium订单表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `order_id` | VARCHAR(36) | PRIMARY KEY | 订单ID |
| `buyer_id` | BIGINT | NOT NULL INDEX | 购买者ID |
| `recipient_id` | BIGINT | NULLABLE | 接收者ID |
| `recipient_username` | VARCHAR(32) | NULLABLE | 接收者用户名 |
| `recipient_type` | VARCHAR(10) | NOT NULL | 类型(self/other) |
| `premium_months` | INTEGER | NOT NULL | Premium月数 |
| `amount_usdt` | FLOAT | NOT NULL | 金额(USDT) |
| `status` | VARCHAR(20) | NOT NULL DEFAULT 'PENDING' | 状态 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `paid_at` | DATETIME | NULLABLE | 支付时间 |
| `delivered_at` | DATETIME | NULLABLE | 交付时间 |
| `expires_at` | DATETIME | NOT NULL | 过期时间 |
| `tx_hash` | VARCHAR(100) | NULLABLE | 交易哈希 |
| `delivery_result` | TEXT | NULLABLE | 交付结果 |

**索引:**
- `idx_premium_orders_buyer_status` (buyer_id, status)
- `idx_premium_orders_recipient` (recipient_id)

---

### 6. energy_orders - 能量订单表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `order_id` | VARCHAR(36) | PRIMARY KEY | 订单ID |
| `user_id` | INTEGER | NOT NULL INDEX | 用户ID |
| `order_type` | VARCHAR(20) | NOT NULL | 类型(hourly/package/flash) |
| `energy_amount` | INTEGER | NULLABLE | 能量数量 |
| `purchase_count` | INTEGER | NULLABLE | 购买笔数 |
| `package_count` | INTEGER | NULLABLE | 套餐笔数 |
| `usdt_amount` | FLOAT | NULLABLE | USDT金额 |
| `receive_address` | VARCHAR(64) | NOT NULL | 接收地址 |
| `total_price_trx` | FLOAT | NULLABLE | 总价(TRX) |
| `total_price_usdt` | FLOAT | NULLABLE | 总价(USDT) |
| `status` | VARCHAR(20) | NOT NULL DEFAULT 'PENDING' | 状态 |
| `api_order_id` | VARCHAR(64) | NULLABLE INDEX | API订单ID |
| `error_message` | VARCHAR(500) | NULLABLE | 错误信息 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `completed_at` | DATETIME | NULLABLE | 完成时间 |
| `user_tx_hash` | VARCHAR(100) | NULLABLE | 用户交易哈希 |
| `user_confirmed_at` | DATETIME | NULLABLE | 用户确认时间 |

**索引:**
- `idx_energy_user_status` (user_id, status)
- `idx_energy_order_type` (order_type)

---

### 7. debit_records - 扣费记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTO | 记录ID |
| `user_id` | INTEGER | NOT NULL INDEX | 用户ID |
| `amount_micro_usdt` | INTEGER | NOT NULL | 扣费金额(微USDT) |
| `order_type` | VARCHAR(32) | NOT NULL | 订单类型 |
| `related_order_id` | VARCHAR(36) | NULLABLE | 关联订单ID |
| `created_at` | DATETIME | NOT NULL | 创建时间 |

---

### 8. suffix_allocations - 后缀分配表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `suffix` | INTEGER | PRIMARY KEY | 后缀值(1-999) |
| `order_id` | VARCHAR(36) | NULLABLE INDEX | 分配的订单ID |
| `allocated_at` | DATETIME | NULLABLE | 分配时间 |
| `expires_at` | DATETIME | NULLABLE | 过期时间 |

---

### 9. address_query_logs - 地址查询限频表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `user_id` | INTEGER | PRIMARY KEY | 用户ID |
| `last_query_at` | DATETIME | NOT NULL | 最后查询时间 |
| `query_count` | INTEGER | NOT NULL DEFAULT 1 | 查询次数 |

---

### 10. user_bindings - 用户绑定表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTO | 记录ID |
| `user_id` | BIGINT | NOT NULL UNIQUE INDEX | Telegram用户ID |
| `username` | VARCHAR(32) | NULLABLE UNIQUE INDEX | 用户名 |
| `nickname` | VARCHAR(255) | NULLABLE | 昵称 |
| `is_verified` | BOOLEAN | NOT NULL DEFAULT FALSE | 是否已验证 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |

---

## 状态枚举

### 订单状态 (OrderStatus)
- `PENDING` - 待支付
- `PAID` - 已支付
- `DELIVERED` - 已交付
- `PARTIAL` - 部分交付
- `EXPIRED` - 已过期
- `CANCELLED` - 已取消

### 能量订单状态 (EnergyOrderStatus)
- `pending` - 待支付
- `processing` - 处理中
- `completed` - 已完成
- `failed` - 失败
- `expired` - 已过期

### TRX兑换状态
- `PENDING` - 待支付
- `PAID` - 已支付
- `TRANSFERRED` - 已转账
- `FAILED` - 失败
