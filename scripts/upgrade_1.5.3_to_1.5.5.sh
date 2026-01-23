#!/bin/bash
# =============================================================================
# LH Contract Management System - Production Upgrade Script
# Upgrade path: v1.5.3 -> v1.5.5
# Date: 2026-01-23
# =============================================================================
#
# 更新内容 (v1.5.5):
# - RefreshToken轮换/撤销机制（新增数据库表）
# - 安全修复：dashboard/reports权限校验、init-admin令牌保护
# - Bug修复：dashboard.py缺失导入、Layout.vue版本硬编码
# - 备份文件自动清理、文件路径安全校验
#
# =============================================================================

set -e

# Configuration
BACKUP_DIR="./backups/upgrade_1.5.3_to_1.5.5_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="./upgrade_1.5.5_$(date +%Y%m%d_%H%M%S).log"
TARGET_BRANCH="release/V1.5.5"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"; }

echo "=============================================="
echo "  LH Contract v1.5.3 -> v1.5.5 升级脚本"
echo "=============================================="
echo ""

# =============================================================================
# Step 1: 前置检查
# =============================================================================
log "Step 1: 前置检查..."

# 检查是否在项目目录
if [ ! -f "docker-compose.yml" ]; then
    error "请在项目根目录运行此脚本"
    exit 1
fi

# 检查Docker服务
if ! docker compose ps | grep -q "lh_contract"; then
    error "Docker服务未运行，请先启动服务"
    exit 1
fi

log "✓ 前置检查通过"

# =============================================================================
# Step 2: 备份
# =============================================================================
log "Step 2: 创建备份..."

mkdir -p "$BACKUP_DIR"

# 备份数据库
log "  - 备份数据库..."
docker compose exec -T db pg_dump -U lh_admin lh_contract_db > "$BACKUP_DIR/db_backup.sql"

# 备份环境配置
cp .env "$BACKUP_DIR/.env.backup" 2>/dev/null || true

# 备份上传文件目录信息
ls -la ./backend/uploads/ > "$BACKUP_DIR/uploads_listing.txt" 2>/dev/null || true

log "✓ 备份完成: $BACKUP_DIR"

# =============================================================================
# Step 3: 拉取新代码
# =============================================================================
log "Step 3: 拉取新代码..."

git fetch origin
git checkout $TARGET_BRANCH
git pull origin $TARGET_BRANCH

CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ]; then
    error "无法切换到分支 $TARGET_BRANCH"
    exit 1
fi

log "✓ 代码已更新到 $TARGET_BRANCH"

# =============================================================================
# Step 4: 数据库迁移 (RefreshToken表)
# =============================================================================
log "Step 4: 数据库迁移..."

# 创建 refresh_tokens 表
log "  - 创建 refresh_tokens 表..."
docker compose exec -T db psql -U lh_admin -d lh_contract_db << 'EOF'
-- RefreshToken 表用于令牌轮换和撤销
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    jti VARCHAR(36) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_jti ON refresh_tokens(jti);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_revoked ON refresh_tokens(user_id, revoked);

-- 清理过期令牌的函数（可选，用于定期维护）
-- 建议设置定时任务执行: DELETE FROM refresh_tokens WHERE expires_at < NOW() - INTERVAL '30 days';
EOF

if [ $? -eq 0 ]; then
    log "✓ 数据库迁移完成"
else
    error "数据库迁移失败"
    exit 1
fi

# =============================================================================
# Step 5: 更新环境配置
# =============================================================================
log "Step 5: 检查环境配置..."

# 确保INIT_ADMIN_TOKEN已配置（生产环境安全要求）
if ! grep -q "INIT_ADMIN_TOKEN=" .env; then
    # 生成随机令牌
    ADMIN_TOKEN=$(openssl rand -hex 16 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 32)
    echo "" >> .env
    echo "# Admin初始化令牌 (v1.5.5安全增强)" >> .env
    echo "INIT_ADMIN_TOKEN=$ADMIN_TOKEN" >> .env
    log "  - 已添加 INIT_ADMIN_TOKEN"
    warn "  ⚠ 请记录此令牌，用于初始化管理员: $ADMIN_TOKEN"
fi

# 确保ALLOW_QUERY_TOKEN配置（默认禁用）
if ! grep -q "ALLOW_QUERY_TOKEN=" .env; then
    echo "ALLOW_QUERY_TOKEN=false" >> .env
    log "  - 已添加 ALLOW_QUERY_TOKEN=false"
fi

# 确保TRUSTED_PROXIES配置
if ! grep -q "TRUSTED_PROXIES=" .env; then
    echo "TRUSTED_PROXIES=" >> .env
    log "  - 已添加 TRUSTED_PROXIES (空值，需手动配置)"
fi

log "✓ 环境配置检查完成"

# =============================================================================
# Step 6: 重建并重启服务
# =============================================================================
log "Step 6: 重建服务..."

# 重建后端镜像（包含新代码）
docker compose build --no-cache backend

# 重建前端镜像（版本号更新）
docker compose build --no-cache frontend

# 重启所有服务
docker compose down
docker compose up -d

log "✓ 服务重启完成"

# =============================================================================
# Step 7: 验证升级
# =============================================================================
log "Step 7: 验证升级..."
sleep 15

# 检查后端健康
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo "failed")
if echo "$HEALTH" | grep -q "healthy"; then
    log "✓ 后端健康检查通过"
else
    error "后端健康检查失败"
fi

# 检查版本号
VERSION_CHECK=$(docker compose exec -T backend python -c "from app.config import settings; print(settings.APP_VERSION)" 2>/dev/null || echo "unknown")
if [[ "$VERSION_CHECK" == *"1.5.5"* ]]; then
    log "✓ 版本验证通过: $VERSION_CHECK"
else
    warn "版本检查异常，预期1.5.5，实际: $VERSION_CHECK"
fi

# 检查前端
FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "failed")
if [ "$FRONTEND" == "200" ]; then
    log "✓ 前端服务正常"
else
    warn "前端服务异常，HTTP状态码: $FRONTEND"
fi

# 检查新表是否存在
TABLE_CHECK=$(docker compose exec -T db psql -U lh_admin -d lh_contract_db -c "SELECT COUNT(*) FROM refresh_tokens;" 2>/dev/null || echo "failed")
if echo "$TABLE_CHECK" | grep -q "0"; then
    log "✓ refresh_tokens 表已创建"
else
    warn "refresh_tokens 表检查异常"
fi

# =============================================================================
# 完成
# =============================================================================
echo ""
echo "=============================================="
echo "  升级完成！"
echo "=============================================="
echo ""
log "升级日志: $LOG_FILE"
log "备份目录: $BACKUP_DIR"
echo ""
echo "v1.5.5 新功能提示:"
echo "  1. RefreshToken轮换: 每次刷新令牌时自动轮换"
echo "  2. /api/v1/auth/logout: 新增登出接口，撤销所有令牌"
echo "  3. 安全增强: 报表和看板需要相应权限"
echo ""
echo "如需回滚，请使用备份文件:"
echo "  psql -U lh_admin -d lh_contract_db < $BACKUP_DIR/db_backup.sql"
echo ""
