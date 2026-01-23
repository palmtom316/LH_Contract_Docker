#!/bin/bash
# LH Contract Management System - Production Upgrade Script v1.5.1
# Upgrade path: Any -> 1.5.1
# Date: 2026-01-16

set -e

# Configuration
BACKUP_DIR="./backups/upgrade_1.5.1_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="./upgrade_1.5.1_$(date +%Y%m%d_%H%M%S).log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"; }

# 1. 检查并切换代码
log "Step 1: Checking code version..."
git fetch origin 1.5.1
git checkout 1.5.1
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "1.5.1" ]; then
    error "Failed to switch to branch 1.5.1"
    exit 1
fi
log "✓ Switched to branch 1.5.1"

# 2. 备份
log "Step 2: Creating backup..."
mkdir -p "$BACKUP_DIR"
docker compose exec -T db pg_dump -U lh_admin lh_contract_db > "$BACKUP_DIR/db_backup.sql"
cp .env "$BACKUP_DIR/.env.backup"
log "✓ Backup created at $BACKUP_DIR"

# 3. 更新配置
log "Step 3: Updating configuration..."
# 确保 MinIO 配置存在 (复用原脚本逻辑)
if ! grep -q "MINIO_ENDPOINT=" .env; then
    echo "" >> .env
    echo "# MinIO Configuration" >> .env
    echo "MINIO_ROOT_USER=minioadmin" >> .env
    echo "MINIO_ROOT_PASSWORD=minioadmin123" >> .env
    echo "MINIO_ENDPOINT=minio:9000" >> .env
    echo "MINIO_ACCESS_KEY=\${MINIO_ROOT_USER}" >> .env
    echo "MINIO_SECRET_KEY=\${MINIO_ROOT_PASSWORD}" >> .env
    echo "MINIO_SECURE=false" >> .env
    echo "MINIO_BUCKET_ACTIVE=contracts-active" >> .env
    echo "MINIO_BUCKET_ARCHIVE=contracts-archive" >> .env
    log "✓ Added MinIO config"
fi

# 确保版本号配置正确 (如果 .env 中有覆盖)
sed -i 's/APP_VERSION=.*/APP_VERSION=1.5.1/' .env || true

# 4. 数据库迁移
log "Step 4: Running database migrations..."
# 启动数据库
docker compose up -d db
sleep 5
# 运行迁移
docker compose up -d backend
sleep 10
if docker compose exec -T backend alembic upgrade head; then
    log "✓ Database migration successful"
else
    error "Database migration failed. Please check logs."
    exit 1
fi

# 5. 重建并重启服务
log "Step 5: Rebuilding services..."
docker compose build --no-cache backend frontend
docker compose down
docker compose up -d

# 6. 验证
log "Step 6: Verifying installation..."
sleep 15
VERSION_CHECK=$(docker compose exec -T backend python -c "from app.config import settings; print(settings.APP_VERSION)" 2>/dev/null)
if [[ "$VERSION_CHECK" == *"1.5.1"* ]]; then
    log "✓ Version verification passed: $VERSION_CHECK"
else
    error "Version check failed. Expected 1.5.1, got $VERSION_CHECK"
fi

echo ""
echo "Upgrade to 1.5.1 completed successfully!"
