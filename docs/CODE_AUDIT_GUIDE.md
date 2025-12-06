# 🔍 代码审计指南

本文档提供 tg_dgn_bot_v2 项目的本地代码审计命令集，用于生产环境部署前的质量检查。

## 📦 工具安装

### 一键安装所有审计工具

```bash
pip install ruff>=0.8.0 mypy>=1.13.0 bandit>=1.7.0
```

### 工具说明

| 工具 | 版本 | 用途 | 检查范围 |
|------|------|------|----------|
| **Ruff** | >=0.8.0 | 代码风格检查 + 格式化 | `src/` |
| **MyPy** | >=1.13.0 | 静态类型检查 | `src/` |
| **Bandit** | >=1.7.0 | 安全漏洞扫描 | `src/`（排除 tests） |
| **Pytest** | >=8.0.0 | 单元测试 + 覆盖率 | `tests/` |

---

## 🚀 快速开始

### 一键执行审计（推荐）

**Windows (PowerShell):**
```powershell
.\scripts\audit.ps1              # 检查模式
.\scripts\audit.ps1 -Fix         # 自动修复模式
.\scripts\audit.ps1 -SkipTests   # 跳过测试
```

**Linux/macOS (Bash):**
```bash
chmod +x scripts/audit.sh
./scripts/audit.sh               # 检查模式
./scripts/audit.sh --fix         # 自动修复模式
./scripts/audit.sh --skip-tests  # 跳过测试
```

---

## 📋 单独命令说明

### 1. Ruff 代码风格检查

**检查命令:**
```bash
python -m ruff check src/
```

**自动修复:**
```bash
python -m ruff check src/ --fix --show-fixes
```

**格式化检查:**
```bash
python -m ruff format src/ --check
```

**自动格式化:**
```bash
python -m ruff format src/
```

**预期输出（通过）:**
```
All checks passed!
```

**常见问题:**
- `E501`: 行过长 → 配置中已设置 line-length=120
- `I001`: 导入排序错误 → 使用 `--fix` 自动修复
- `F401`: 未使用导入 → 检查是否为 re-export

---

### 2. MyPy 静态类型检查

**检查命令:**
```bash
python -m mypy src/ --ignore-missing-imports
```

**预期输出（通过）:**
```
Success: no issues found in XX source files
```

**常见问题:**
- `[attr-defined]`: 属性不存在 → 检查方法名拼写
- `[call-arg]`: 缺少必需参数 → 添加缺失参数
- `[misc]`: 类型不匹配 → 检查 await 使用

---

### 3. Bandit 安全扫描

**检查命令:**
```bash
python -m bandit -r src/ --skip B101,B311 -q
```

**详细报告:**
```bash
python -m bandit -r src/ --skip B101,B311 -f json -o bandit_report.json
```

**预期输出（通过）:**
```
Run metrics:
    Total issues (by severity):
        High: 0
        Medium: 0
        Low: 0
```

**常见问题:**
- `B101`: assert 使用（已跳过）
- `B311`: random 模块（已跳过，非加密场景）
- `B105`: 硬编码密码 → 检查是否为示例值

---

### 4. Pytest 单元测试

**快速测试:**
```bash
python -m pytest tests/ -q --tb=no
```

**详细测试:**
```bash
python -m pytest tests/ -v --tb=short
```

**带覆盖率:**
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

**预期输出:**
```
758 passed, 2 skipped in 92.30s
```

---

## ⚙️ 配置文件

所有审计工具配置集中在 `pyproject.toml`，主要配置项：

```toml
[tool.ruff]
line-length = 120
target-version = "py311"
include = ["src/**/*.py"]

[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true

[tool.bandit]
targets = ["src"]
skips = ["B101", "B311"]
```

---

## 🔄 CI/CD 集成

### GitHub Actions 配置

在 `.github/workflows/ci.yml` 中添加：

```yaml
  code-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install audit tools
        run: pip install ruff mypy bandit
      
      - name: Ruff check
        run: python -m ruff check src/
      
      - name: MyPy check
        run: python -m mypy src/ --ignore-missing-imports
        continue-on-error: true  # 渐进式类型化
      
      - name: Bandit scan
        run: python -m bandit -r src/ --skip B101,B311 -q
```

### 部署阻塞建议

| 检查项 | 是否阻塞部署 | 理由 |
|--------|-------------|------|
| Ruff 严重错误 (E/F) | ✅ 是 | 可能导致运行时错误 |
| Ruff 警告 (W/I) | ❌ 否 | 风格问题，不影响功能 |
| MyPy 错误 | ⚠️ 可选 | 渐进式类型化，建议逐步修复 |
| Bandit High | ✅ 是 | 高危安全问题 |
| Bandit Medium/Low | ❌ 否 | 需人工评估 |
| Pytest 失败 | ✅ 是 | 功能回归 |

---

## 📊 当前项目审计状态

```
审计时间: 2025-12-06
项目版本: v2.0.2

Ruff:    4032 issues (2124 可自动修复)
MyPy:    多个类型错误 (渐进式修复中)
Bandit:  8 Low, 4 Medium, 0 High
Pytest:  758 passed, 2 skipped ✅
```

### 建议优先级

1. **立即修复**: Bandit High 级别问题
2. **部署前修复**: Ruff E/F 错误
3. **后续迭代**: MyPy 类型错误、Ruff 警告

