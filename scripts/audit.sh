#!/bin/bash
# ============================================
# tg_dgn_bot_v2 代码审计脚本 (Bash)
# 用于生产环境部署前的质量检查
# ============================================

set -e

# 参数解析
FIX=false
SKIP_TESTS=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix) FIX=true; shift ;;
        --skip-tests) SKIP_TESTS=true; shift ;;
        --verbose) VERBOSE=true; shift ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

EXIT_CODE=0
START_TIME=$(date +%s)

# 输出函数
step() { echo -e "\n${CYAN}=== $1 ===${NC}"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; EXIT_CODE=1; }
skip() { echo -e "${YELLOW}[SKIP]${NC} $1"; }
info() { echo -e "${GRAY}[INFO]${NC} $1"; }

echo -e "${MAGENTA}"
echo "============================================"
echo "  tg_dgn_bot_v2 代码审计"
echo "  版本: v2.0.2"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo -e "${NC}"

# Step 1: Ruff 代码风格检查
step "1/5 Ruff 代码风格检查"
if $FIX; then
    info "运行自动修复模式..."
    if python -m ruff check src/ --fix --show-fixes; then
        success "Ruff 检查通过"
    else
        fail "Ruff 发现代码风格问题"
    fi
else
    if python -m ruff check src/; then
        success "Ruff 检查通过"
    else
        fail "Ruff 发现代码风格问题"
        info "提示: 使用 --fix 参数自动修复"
    fi
fi

# Step 2: Ruff 格式化检查
step "2/5 Ruff 代码格式化检查"
if $FIX; then
    python -m ruff format src/
    success "代码格式化完成"
else
    if python -m ruff format src/ --check; then
        success "代码格式符合规范"
    else
        fail "代码格式不符合规范"
        info "提示: 使用 --fix 参数自动格式化"
    fi
fi

# Step 3: MyPy 静态类型检查
step "3/5 MyPy 静态类型检查"
if python -m mypy src/ --config-file pyproject.toml; then
    success "MyPy 类型检查通过"
else
    fail "MyPy 发现类型错误"
fi

# Step 4: Bandit 安全扫描
step "4/5 Bandit 安全扫描"
if python -m bandit -r src/ -c pyproject.toml --quiet 2>&1; then
    success "Bandit 未发现安全问题"
else
    fail "Bandit 发现潜在安全问题"
fi

# Step 5: Pytest 单元测试
step "5/5 Pytest 单元测试"
if $SKIP_TESTS; then
    skip "跳过测试执行 (--skip-tests)"
else
    if python -m pytest tests/ -q --tb=no; then
        success "所有测试通过"
    else
        fail "测试失败"
    fi
fi

# 最终报告
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}"
else
    echo -e "${RED}"
fi
echo "============================================"
echo "  审计完成"
echo "  耗时: ${DURATION} 秒"
if [ $EXIT_CODE -eq 0 ]; then
    echo "  结果: 通过 [OK]"
else
    echo "  结果: 失败 [FAIL]"
fi
echo "============================================"
echo -e "${NC}"

exit $EXIT_CODE

