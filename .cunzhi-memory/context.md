# 项目上下文信息

- Zeabur 部署环境变量配置：
- REDIS_HOST=redis（内部服务名）
- REDIS_PASSWORD=留空（不使用密码）
- DATABASE_URL=sqlite:////app/data/tg_bot.db
- USE_WEBHOOK=false
- BOT_SERVICE_PORT=8080
- ## 2025-11-30 代码审查修复完成

### 修复概要
- P0: 4项（图标文案统一、返回按钮）
- P1: 2项（取消按钮、订单通知）  
- P2: 3项（callback统一、error_collector、死代码清理）

### 重要决定
1. 所有返回主菜单的 callback_data 统一使用 `nav_back_to_main`
2. 关键业务异常使用 `error_collector.collect_error()` 收集
3. Energy 模块删除了未使用的 STATE_INPUT_COUNT 状态

### 生成的文件
- docs/CODE_REVIEW_REPORT.md - 审查报告
- tests/test_code_review_issues.py - 25个验证测试
- CHANGELOG.md - 修改日志

### 测试命令
```bash
python -m pytest tests/test_code_review_issues.py -v
```
