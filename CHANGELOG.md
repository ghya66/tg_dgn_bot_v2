# Changelog

本文档记录项目的所有重要更改。

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
