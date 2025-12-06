# ============================================
# tg_dgn_bot_v2 代码审计脚本 (PowerShell)
# 用于生产环境部署前的质量检查
# ============================================

param(
    [switch]$Fix,           # 自动修复可修复的问题
    [switch]$SkipTests,     # 跳过测试执行
    [switch]$Verbose        # 详细输出
)

$ErrorActionPreference = "Stop"
$script:exitCode = 0
$script:startTime = Get-Date

# 颜色输出函数
function Write-Step { param($msg) Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Fail { param($msg) Write-Host "[FAIL] $msg" -ForegroundColor Red; $script:exitCode = 1 }
function Write-Skip { param($msg) Write-Host "[SKIP] $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Gray }

Write-Host @"
============================================
  tg_dgn_bot_v2 代码审计
  版本: v2.0.2
  时间: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
============================================
"@ -ForegroundColor Magenta

# Step 1: Ruff 代码风格检查
Write-Step "1/5 Ruff 代码风格检查"
try {
    if ($Fix) {
        Write-Info "运行自动修复模式..."
        python -m ruff check src/ --fix --show-fixes
    } else {
        python -m ruff check src/
    }
    Write-Success "Ruff 检查通过"
} catch {
    Write-Fail "Ruff 发现代码风格问题"
    if (-not $Fix) { Write-Info "提示: 使用 -Fix 参数自动修复" }
}

# Step 2: Ruff 格式化检查
Write-Step "2/5 Ruff 代码格式化检查"
try {
    if ($Fix) {
        python -m ruff format src/
        Write-Success "代码格式化完成"
    } else {
        python -m ruff format src/ --check
        Write-Success "代码格式符合规范"
    }
} catch {
    Write-Fail "代码格式不符合规范"
    if (-not $Fix) { Write-Info "提示: 使用 -Fix 参数自动格式化" }
}

# Step 3: MyPy 静态类型检查
Write-Step "3/5 MyPy 静态类型检查"
try {
    python -m mypy src/ --config-file pyproject.toml 2>&1 | Tee-Object -Variable mypyOutput
    if ($LASTEXITCODE -eq 0) {
        Write-Success "MyPy 类型检查通过"
    } else {
        Write-Fail "MyPy 发现类型错误"
    }
} catch {
    Write-Fail "MyPy 执行失败: $_"
}

# Step 4: Bandit 安全扫描
Write-Step "4/5 Bandit 安全扫描"
try {
    python -m bandit -r src/ -c pyproject.toml --quiet 2>&1 | Tee-Object -Variable banditOutput
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Bandit 未发现安全问题"
    } else {
        Write-Fail "Bandit 发现安全问题"
        Write-Host $banditOutput
    }
} catch {
    # Bandit 返回非零可能只是警告
    if ($banditOutput -match "No issues identified") {
        Write-Success "Bandit 未发现安全问题"
    } else {
        Write-Fail "Bandit 发现潜在安全问题"
    }
}

# Step 5: Pytest 单元测试
Write-Step "5/5 Pytest 单元测试"
if ($SkipTests) {
    Write-Skip "跳过测试执行 (-SkipTests)"
} else {
    try {
        python -m pytest tests/ -q --tb=no 2>&1 | Tee-Object -Variable pytestOutput
        if ($LASTEXITCODE -eq 0) {
            Write-Success "所有测试通过"
        } else {
            Write-Fail "测试失败"
        }
    } catch {
        Write-Fail "Pytest 执行失败: $_"
    }
}

# 最终报告
$duration = (Get-Date) - $script:startTime
Write-Host @"

============================================
  审计完成
  耗时: $($duration.TotalSeconds.ToString("F1")) 秒
  结果: $(if ($script:exitCode -eq 0) { "通过 [OK]" } else { "失败 [FAIL]" })
============================================
"@ -ForegroundColor $(if ($script:exitCode -eq 0) { "Green" } else { "Red" })

exit $script:exitCode

