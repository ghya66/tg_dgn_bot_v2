-- ===================================================
-- TG DGN Bot V2 - 完整数据库表结构 (15张表)
-- 生成时间: 2025-11-27
-- 兼容: SQLite / PostgreSQL
-- ===================================================

-- ===== 核心表 (6个) =====

-- 1. users - 用户表
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username VARCHAR(64),
    balance_micro_usdt INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);

-- 2. orders - 主订单表
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_type VARCHAR(32) NOT NULL,
    base_amount INTEGER NOT NULL,
    unique_suffix INTEGER,
    amount_usdt INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    recipient VARCHAR(255),
    premium_months INTEGER,
    tx_hash VARCHAR(100),
    user_tx_hash VARCHAR(100),
    user_confirmed_at DATETIME,
    user_confirm_source VARCHAR(32),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_at DATETIME,
    delivered_at DATETIME,
    expires_at DATETIME NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_orders_type_status ON orders(order_type, status);
CREATE INDEX IF NOT EXISTS idx_orders_user_status ON orders(user_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);

-- 3. deposit_orders - 充值订单表
CREATE TABLE IF NOT EXISTS deposit_orders (
    order_id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    base_amount REAL NOT NULL,
    unique_suffix INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    amount_micro_usdt INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    tx_hash VARCHAR(100),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_at DATETIME,
    expires_at DATETIME NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_deposit_user_status ON deposit_orders(user_id, status);
CREATE INDEX IF NOT EXISTS idx_deposit_suffix ON deposit_orders(unique_suffix);

-- 4. trx_exchange_orders - TRX兑换订单表
CREATE TABLE IF NOT EXISTS trx_exchange_orders (
    order_id VARCHAR(32) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    usdt_amount DECIMAL(10,3) NOT NULL,
    trx_amount DECIMAL(20,6) NOT NULL,
    exchange_rate DECIMAL(10,6) NOT NULL,
    recipient_address VARCHAR(64) NOT NULL,
    payment_address VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    tx_hash VARCHAR(128),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_at DATETIME,
    transferred_at DATETIME,
    expires_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_trx_user ON trx_exchange_orders(user_id);

-- 5. premium_orders - Premium订单表
CREATE TABLE IF NOT EXISTS premium_orders (
    order_id VARCHAR(36) PRIMARY KEY,
    buyer_id BIGINT NOT NULL,
    recipient_id BIGINT,
    recipient_username VARCHAR(32),
    recipient_type VARCHAR(10) NOT NULL,
    premium_months INTEGER NOT NULL,
    amount_usdt REAL NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_at DATETIME,
    delivered_at DATETIME,
    expires_at DATETIME NOT NULL,
    tx_hash VARCHAR(100),
    delivery_result TEXT
);
CREATE INDEX IF NOT EXISTS idx_premium_buyer_status ON premium_orders(buyer_id, status);
CREATE INDEX IF NOT EXISTS idx_premium_recipient ON premium_orders(recipient_id);

-- 6. energy_orders - 能量订单表
CREATE TABLE IF NOT EXISTS energy_orders (
    order_id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    energy_amount INTEGER,
    purchase_count INTEGER,
    package_count INTEGER,
    usdt_amount REAL,
    receive_address VARCHAR(64) NOT NULL,
    total_price_trx REAL,
    total_price_usdt REAL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    api_order_id VARCHAR(64),
    error_message VARCHAR(500),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    user_tx_hash VARCHAR(100),
    user_confirmed_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_energy_user_status ON energy_orders(user_id, status);
CREATE INDEX IF NOT EXISTS idx_energy_order_type ON energy_orders(order_type);
CREATE INDEX IF NOT EXISTS idx_energy_api_order ON energy_orders(api_order_id);

-- ===== 辅助表 (9个) =====

-- 7. debit_records - 扣费记录表
CREATE TABLE IF NOT EXISTS debit_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount_micro_usdt INTEGER NOT NULL,
    order_type VARCHAR(32) NOT NULL,
    related_order_id VARCHAR(36),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_debit_user ON debit_records(user_id);

-- 8. suffix_allocations - 后缀分配表
CREATE TABLE IF NOT EXISTS suffix_allocations (
    suffix INTEGER PRIMARY KEY,
    order_id VARCHAR(36),
    allocated_at DATETIME,
    expires_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_suffix_order ON suffix_allocations(order_id);

-- 9. address_query_logs - 地址查询限频表
CREATE TABLE IF NOT EXISTS address_query_logs (
    user_id INTEGER PRIMARY KEY,
    last_query_at DATETIME NOT NULL,
    query_count INTEGER NOT NULL DEFAULT 1
);

-- 10. user_bindings - 用户绑定表
CREATE TABLE IF NOT EXISTS user_bindings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(32) UNIQUE,
    nickname VARCHAR(255),
    is_verified BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_binding_user ON user_bindings(user_id);
CREATE INDEX IF NOT EXISTS idx_binding_username ON user_bindings(username);

-- 11. price_configs - 价格配置表
CREATE TABLE IF NOT EXISTS price_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value REAL NOT NULL,
    description VARCHAR(200),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER
);

-- 12. content_configs - 内容配置表
CREATE TABLE IF NOT EXISTS content_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description VARCHAR(200),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER
);

-- 13. setting_configs - 系统设置表
CREATE TABLE IF NOT EXISTS setting_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value VARCHAR(200) NOT NULL,
    description VARCHAR(200),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER
);

-- 14. audit_logs - 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    target VARCHAR(200),
    details TEXT,
    result VARCHAR(20),
    ip_address VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 15. trx_exchange_rates - TRX汇率表
CREATE TABLE IF NOT EXISTS trx_exchange_rates (
    id VARCHAR(10) PRIMARY KEY DEFAULT 'current',
    rate DECIMAL(10,6) NOT NULL,
    updated_at DATETIME NOT NULL,
    updated_by VARCHAR(50) NOT NULL
);
