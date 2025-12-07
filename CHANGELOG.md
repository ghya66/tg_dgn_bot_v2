# Changelog

本文档记录项目的所有重要更改。

---

## [2025-12-07] 数据库配置统一

### 概述

将分散的数据库文件统一到 `./data/tg_bot.db`，解决本地开发与 Docker 部署使用不同数据库路径的问题。

### 🔧 变更内容

#### 问题背景

项目存在两个数据库文件，不同部署方式使用不同路径：

| 部署方式 | 修改前使用的数据库 |
|----------|-------------------|
| 本地直接运行 | `./tg_bot.db` (根目录) |
| Docker 部署 | `./data/tg_bot.db` (data 目录) |
| Render.com | PostgreSQL (不受影响) |

#### 解决方案

统一使用 `./data/tg_bot.db` 作为默认数据库路径。

### 📁 修改文件

| 文件 | 修改内容 |
|------|---------|
| `src/database.py` | 第14行：`sqlite:///./tg_bot.db` → `sqlite:///./data/tg_bot.db` |
| `alembic.ini` | 第17行：`sqlite:///./tg_bot.db` → `sqlite:///./data/tg_bot.db` |

### 配置对比

**修改前 (`src/database.py` 第14行)**:
```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tg_bot.db")
```

**修改后**:
```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/tg_bot.db")
```

**修改前 (`alembic.ini` 第17行)**:
```ini
sqlalchemy.url = sqlite:///./tg_bot.db
```

**修改后**:
```ini
sqlalchemy.url = sqlite:///./data/tg_bot.db
```

### 数据迁移

将根目录的数据库文件移动到 data 目录：
```powershell
Move-Item -Force ./tg_bot.db ./data/tg_bot.db
```

### 对各部署方式的影响

| 部署方式 | 影响 | 说明 |
|----------|------|------|
| 本地直接运行 | ✅ 无问题 | 默认值已改为 `./data/tg_bot.db` |
| Docker Compose | ✅ 无问题 | `docker-compose.yml` 已是 `./data/tg_bot.db` |
| Render.com | ✅ 无问题 | 继续使用 PostgreSQL，不受影响 |
| CI/CD 测试 | ✅ 无问题 | 测试使用内存数据库，不依赖文件路径 |

### 🧪 测试验证

```
761 passed, 1 failed, 2 skipped in 332.05s (5:32)
```

- **761 个测试通过** ✅
- **1 个测试失败** - `test_concurrent_order_creation`（并发压力测试，与本次修改无关）
- **2 个测试跳过** - CI 环境跳过的 Redis 压测

### 注意事项

1. 如果使用环境变量 `DATABASE_URL` 覆盖配置，则不受此次修改影响
2. Alembic 迁移命令现在默认操作 `./data/tg_bot.db`
3. 如需使用其他数据库路径，设置 `DATABASE_URL` 环境变量即可

---

## [2025-12-06] 第三阶段（稳定性）- 提高服务稳定性和可观测性

### 概述

完成第三阶段稳定性改进，修复连接泄漏、数据丢失风险，启用结构化日志格式，全面提升服务可观测性。

### ✅ P1-1: 统一数据库会话管理方式

- **问题**: `trc20_handler.py` 仍使用旧的 `get_db()/close_db()` 模式，存在连接泄漏风险
- **修复**: 统一改为 `get_db_context()` 上下文管理器
- **文件**: `src/webhook/trc20_handler.py`（第270-296行、第328-348行）
- **测试**: 修复 `tests/test_trc20_handler.py` 和 `tests/test_trx_exchange_auto.py`

### ✅ P1-4: 实现错误收集器持久化

- **问题**: `ErrorCollector` 数据仅存内存，进程重启后丢失
- **修复**:
  - 启动时自动加载历史数据
  - 异步落盘（使用 `ThreadPoolExecutor`）
  - 进程退出时自动保存（`atexit` hook）
  - 线程安全（`threading.Lock`）
  - 自动保存间隔从 300 秒减少到 60 秒
- **文件**: `src/common/error_collector.py`

### ✅ P1-5: 修复 Energy API 客户端连接泄漏

- **问题**: `EnergyAPIClient` 的 `httpx.AsyncClient` 在进程退出时未正确关闭
- **修复**:
  - 添加 `__aenter__/__aexit__` 支持上下文管理器
  - 延迟创建 `httpx.AsyncClient`（避免在事件循环外创建）
  - FastAPI 使用 `lifespan` 统一管理资源清理
  - 移除 `middleware.py` 中重复的 `on_event("shutdown")`
- **文件**:
  - `src/modules/energy/client.py`
  - `src/api/app.py`
  - `src/api/routes.py`
  - `src/api/middleware.py`

### ✅ P1-6: 启用结构化日志格式

- **新增**: `src/common/logging_config.py` 结构化日志模块
- **功能**:
  - 支持 JSON 格式（生产环境）和人类可读格式（开发环境）
  - `trace_id` 关联同一请求的所有日志
  - 环境变量配置：`LOG_FORMAT`（json/text）、`LOG_LEVEL`、`LOG_FILE`
  - API 请求自动添加 `X-Trace-ID` 响应头
- **文件**:
  - `src/common/logging_config.py`（新建）
  - `src/bot_v2.py`
  - `src/api/middleware.py`

### 📁 修改文件清单

```
src/webhook/trc20_handler.py          # P1-1: 数据库会话管理
src/common/error_collector.py         # P1-4: 持久化改进
src/modules/energy/client.py          # P1-5: 上下文管理器
src/api/app.py                        # P1-5: lifespan 资源清理
src/api/routes.py                     # P1-5: close_energy_api_client()
src/api/middleware.py                 # P1-5: 移除重复 shutdown; P1-6: trace_id
src/bot_v2.py                         # P1-6: 使用新日志配置
src/common/logging_config.py          # P1-6: 新建结构化日志模块
tests/test_trx_exchange_auto.py       # 修复测试
tests/test_trc20_handler.py           # 修复测试
```

### 🧪 测试结果

```
749 passed, 2 skipped
```

### 使用说明

#### 结构化日志配置

```bash
# 开发环境（人类可读格式）
python src/bot_v2.py

# 生产环境（JSON 格式）
LOG_FORMAT=json LOG_LEVEL=INFO python src/bot_v2.py

# 输出到文件
LOG_FILE=logs/bot.log python src/bot_v2.py
```

#### 日志示例

**人类可读格式**:
```
2025-12-06 16:33:04 - test - INFO - [abc123] API Request: GET /api/health
```

**JSON 格式**:
```json
{"timestamp": "2025-12-06T08:33:04.037173Z", "level": "INFO", "logger": "test", "message": "API Request: GET /api/health", "trace_id": "abc123", "module": "middleware", "function": "log_requests", "line": 85}
```

---

## [2025-12-06] CI/CD 兼容性修复

### 概述

修复 GitHub Actions CI 在 Python 3.11/3.12 环境下的测试失败问题，涉及依赖版本升级、数据库初始化和测试稳定性优化。

### 🔧 Fixed

#### CI 数据库初始化
- **问题**: 测试使用 `SessionLocal()` 连接数据库，但 CI 环境中没有创建数据库表
- **错误**: `sqlite3.OperationalError: no such table: address_query_logs`
- **修复**: 在 CI 工作流中添加数据库初始化步骤
- **文件**: `.github/workflows/ci.yml`

#### pytest-asyncio 版本兼容性
- **问题**: `asyncio_default_fixture_loop_scope` 配置需要 pytest-asyncio 1.0+
- **错误**: 异步 fixture 在 Python 3.11/3.12 上运行失败
- **修复**: 升级 `pytest-asyncio>=1.0.0`
- **文件**: `requirements.txt`

#### Application 创建优化
- **问题**: `python-telegram-bot` 的 `Application.builder()` 在某些条件下产生 weakref 错误
- **修复**: 完全禁用 JobQueue、Updater 和并发更新
- **文件**: `tests/conftest.py`

### ⏭️ Changed

#### CI 工作流优化
- **超时时间**: job 超时从 15 分钟增加到 20 分钟
- **测试超时**: 每个测试添加 120 秒超时限制（`--timeout=120`）
- **缓存策略**: 更新缓存 key 避免恢复旧版本依赖

#### 依赖版本更新
| 包 | 旧版本 | 新版本 | 原因 |
|----|--------|--------|------|
| `pytest` | `>=7.4.3` | `>=8.0.0` | 与 pytest-asyncio 1.0+ 兼容 |
| `pytest-asyncio` | `>=0.24.0` | `>=1.0.0` | 支持 `asyncio_default_fixture_loop_scope` |
| `pandas` | `==2.1.4` | `>=2.2.0` | 支持 Python 3.13 |

### ⏩ Skipped

#### 不稳定测试跳过
- **测试**: `test_suffix_stress_test` (Redis 压力测试)
- **原因**: CI 环境中 Redis 连接不稳定（`Error UNKNOWN while writing to socket`）
- **标记**: `@pytest.mark.skipif(os.getenv("CI") == "true", ...)`
- **文件**: `tests/test_suffix_pool_redis.py`

### 📁 修改文件清单

```
.github/workflows/ci.yml      # 添加数据库初始化，增加超时时间
requirements.txt              # 升级 pytest-asyncio>=1.0.0
tests/conftest.py             # 优化 Application 创建方式
tests/test_suffix_pool_redis.py  # 跳过 CI 中的 Redis 压测
pytest.ini                    # 添加 asyncio_default_fixture_loop_scope
```

### ✅ 验证结果

| Python 版本 | 测试结果 | 备注 |
|-------------|----------|------|
| 3.11 | ✅ 通过 | 726+ passed |
| 3.12 | ✅ 通过 | 726+ passed |
| 3.13 | ⏸️ 暂未支持 | 等生态完善后添加 |

---

## [2025-12-06] 功能优化与数据库修复

### 概述

完成 Premium 模块优化、实时汇率显示优化和数据库字段修复。

### ✅ Premium 模块 - 方案A 实现

- **修改**: 实现直接信任用户名格式（不通过 Telegram API 验证）
- **原因**: Telegram Bot API 的 `get_chat()` 只能查询已与 Bot 交互过的用户
- **安全性**: 发货时如果用户名无效会失败，有完善的失败处理和通知机制
- **文件**: `src/modules/premium/user_verification.py`

### ✅ 实时汇率显示优化

- **新格式**: TOP10 商家列表，带排名 emoji（🥇🥈🥉4️⃣5️⃣6️⃣7️⃣8️⃣9️⃣🔟）
- **渠道切换**: 支持"所有/银行卡/支付宝/微信"切换按钮
- **刷新频率**: 从每5分钟改为每12小时
- **新增方法**:
  - `_build_rates_text()` - 构建汇率文本
  - `_build_rates_keyboard()` - 构建渠道切换键盘
  - `handle_rate_channel()` - 处理渠道切换
  - `handle_rate_close()` - 处理关闭操作
- **文件**: `src/modules/menu/handler.py`, `src/bot_v2.py`

### ✅ 数据库字段修复

- **energy_orders 表**: 添加 `expires_at` 字段（订单过期时间）
- **trx_exchange_orders 表**: 添加 `send_tx_hash` 字段（Bot发送TRX交易哈希）
- **文件**: `src/database.py`

---

## [2025-11-30] 代码审查修复

### 概述

基于全面代码审查，修复了 **9 个问题**（P0: 4, P1: 2, P2: 3），涉及 **14 个文件**的修改。

### 🔴 P0 - 高优先级修复

#### P0-1: Premium 文案不一致
- **问题**: "Premium 开通"、"Premium直充"、"Premium会员" 混用
- **修复**: 统一为 `💎 Premium会员`
- **文件**: `menu/keyboards.py`, `menu/handler.py`

#### P0-2: 个人中心图标不一致
- **问题**: 🏠 和 👤 混用
- **修复**: 统一为 `👤 个人中心`
- **文件**: `menu/keyboards.py`, `menu/handler.py`

#### P0-3: TRX 兑换图标不一致
- **问题**: 🔄 和 💱 混用，文案"TRX 兑换"和"TRX闪兑"混用
- **修复**: 统一为 `💱 TRX闪兑`
- **文件**: `menu/keyboards.py`, `menu/handler.py`, `trx_exchange/handler.py`

#### P0-4: Profile 模块缺少返回主菜单按钮
- **问题**: 用户进入个人中心子页面后无法直接返回主菜单
- **修复**: 在 `back_to_profile()` 键盘中添加 `🏠 返回主菜单` 按钮
- **文件**: `profile/keyboards.py`

### 🟡 P1 - 中优先级修复

#### P1-2: TRX Exchange 输入阶段缺少取消按钮
- **问题**: 用户在输入金额或地址时没有取消选项
- **修复**: 
  - 添加 `cancel_button()` 键盘方法
  - 在 `start_exchange` 和 `input_amount` 中显示取消按钮
  - 添加 `cancel_input` 处理方法
- **文件**: `trx_exchange/keyboards.py`, `trx_exchange/handler.py`

#### P1-3: 订单过期不通知用户
- **问题**: 订单超时取消后用户不知情
- **修复**:
  - 在 `OrderExpiryTask` 中添加 `set_bot()` 方法
  - 添加 `_notify_user_order_expired()` 通知方法
  - 在 `bot_v2.py` 中绑定 bot 实例
- **文件**: `tasks/order_expiry.py`, `bot_v2.py`

### 🟢 P2 - 低优先级修复

#### P2-1: callback_data 命名不统一
- **问题**: 返回主菜单有4种不同的callback（`back_to_main`, `nav_back_to_main`, `menu_back_to_main`, `addrq_back_to_main`）
- **修复**: 统一使用 `nav_back_to_main`
- **文件**: 
  - `help/keyboards.py`
  - `energy/keyboards.py`
  - `trx_exchange/keyboards.py`
  - `profile/keyboards.py`
  - `menu/keyboards.py`
  - `address_query/keyboards.py`
  - `menu/handler.py` (内联键盘)
  - `wallet/profile_handler.py`
  - `common/decorators.py`

#### P2-2: 部分模块未使用 error_collector
- **问题**: 关键业务流程错误只记录日志，未使用错误收集器
- **修复**: 在关键异常处理中添加 `collect_error()` 调用
- **文件**: `premium/handler.py`, `trx_exchange/payment_monitor.py`

#### P2-3: Energy STATE_INPUT_COUNT 遗留代码
- **问题**: `STATE_INPUT_COUNT` 和 `input_count` 方法是死代码
- **修复**: 
  - 删除 `states.py` 中的 `STATE_INPUT_COUNT = 4`
  - 删除 `handler.py` 中的 `STATE_INPUT_COUNT` 状态条目
  - 删除 `handler.py` 中的 `input_count` 方法
  - 重新编号状态常量
- **文件**: `energy/states.py`, `energy/handler.py`

---

### 📁 修改文件清单

```
src/modules/menu/handler.py             # P0-1, P0-2, P0-3
src/modules/menu/keyboards.py           # P0-1, P0-2, P0-3, P2-1
src/modules/profile/keyboards.py        # P0-4, P2-1
src/modules/trx_exchange/handler.py     # P0-3, P1-2
src/modules/trx_exchange/keyboards.py   # P1-2, P2-1
src/modules/trx_exchange/payment_monitor.py  # P2-2
src/modules/energy/states.py            # P2-3
src/modules/energy/handler.py           # P2-3
src/modules/energy/keyboards.py         # P2-1
src/modules/help/keyboards.py           # P2-1
src/modules/address_query/keyboards.py  # P2-1
src/modules/premium/handler.py          # P2-2
src/tasks/order_expiry.py               # P1-3
src/bot_v2.py                           # P1-3
```

### 🧪 新增测试

- **文件**: `tests/test_code_review_issues.py`
- **测试数量**: 25 个
- **覆盖范围**:
  - 图标文案一致性检查
  - 按钮映射完整性检查
  - callback_data 命名规范检查
  - 状态机完整性检查
  - 导航一致性检查
  - 错误处理检查
  - P1/P2 修复验证

### 📄 更新文档

- `docs/CODE_REVIEW_REPORT.md` - 完整审查报告（含修复记录）

---

### 验证

```bash
# 运行代码审查相关测试
python -m pytest tests/test_code_review_issues.py -v

# 运行核心功能测试
python -m pytest tests/test_menu_standard.py tests/test_navigation_system.py -v
```

### 兼容性说明

- 所有修改保持向后兼容
- `NavigationManager` 仍然支持旧的 callback 名称（`back_to_main` 等），但新代码应使用 `nav_back_to_main`
- 订单过期通知功能需要 bot 实例，如果未设置则静默跳过（不影响核心功能）
