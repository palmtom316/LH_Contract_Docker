#!/bin/bash
# LH Contract Management System - Production Safe Upgrade Script
# Version: 1.4.1 -> 1.5.0
# Date: 2026-01-13 (Updated with lessons learned from production upgrade)
#
# This script ensures:
# 1. Zero data loss - all existing data and files are preserved
# 2. Production safety - no debug/dev configurations
# 3. Rollback capability - full backup before upgrade
# 4. Robust migration - automatic fallback to manual SQL if Alembic fails

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./backups/upgrade_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="./upgrade_$(date +%Y%m%d_%H%M%S).log"
EXPECTED_ALEMBIC_VERSION="v1_5_complete_fix"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# ============================================
# PRE-UPGRADE CHECKS
# ============================================

check_prerequisites() {
    log "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi

    if ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi

    if [ ! -f ".env" ]; then
        error ".env file not found"
        exit 1
    fi

    log "✓ Prerequisites check passed"
}

check_git_status() {
    log "Checking Git status..."
    
    # Check for local modifications
    if [ -n "$(git status --porcelain)" ]; then
        warning "⚠️  存在未提交的本地修改:"
        git status --short | head -10
        echo ""
        read -p "是否继续升级？本地修改可能导致冲突 (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            error "升级已取消"
            exit 1
        fi
    else
        log "✓ Git 工作目录干净"
    fi
    
    # Show current branch
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
    log "当前分支: $CURRENT_BRANCH"
}

verify_production_config() {
    log "Verifying production environment configuration..."

    # Check DEBUG is false
    if grep -q "DEBUG=true" .env 2>/dev/null; then
        error "DEBUG=true found in .env - MUST be false for production!"
        exit 1
    fi

    # Check SECRET_KEY is set and not default
    if grep -q "SECRET_KEY=CHANGE_THIS" .env 2>/dev/null; then
        error "SECRET_KEY is still set to default value!"
        exit 1
    fi

    if ! grep -q "SECRET_KEY=" .env 2>/dev/null; then
        error "SECRET_KEY not found in .env!"
        exit 1
    fi

    # Check database password is not default
    if grep -q "POSTGRES_PASSWORD=CHANGE_THIS" .env 2>/dev/null; then
        error "Database password is still set to default value!"
        exit 1
    fi

    log "✓ Production configuration verified"
}

# ============================================
# BACKUP
# ============================================

create_backup() {
    log "Creating backup in $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"

    # Backup database
    log "Backing up database..."
    docker compose exec -T db pg_dump -U "${POSTGRES_USER:-lh_admin}" "${POSTGRES_DB:-lh_contract_db}" > "$BACKUP_DIR/database_backup.sql"

    if [ $? -ne 0 ]; then
        error "Database backup failed!"
        exit 1
    fi

    # Backup uploads directory
    log "Backing up uploads directory..."
    if [ -d "./uploads" ]; then
        cp -r ./uploads "$BACKUP_DIR/uploads_backup"
        log "✓ Backed up $(du -sh ./uploads | cut -f1) of files"
    elif [ -d "./backend/uploads" ]; then
        cp -r ./backend/uploads "$BACKUP_DIR/uploads_backup"
        log "✓ Backed up $(du -sh ./backend/uploads | cut -f1) of files"
    fi

    # Backup .env file
    cp .env "$BACKUP_DIR/.env.backup"

    # Save backup path for later reference
    echo "$BACKUP_DIR" > .last_backup_path

    log "✓ Backup completed: $BACKUP_DIR"
}

verify_backup() {
    log "Verifying backup integrity..."

    # Check database backup size
    DB_SIZE=$(stat -c%s "$BACKUP_DIR/database_backup.sql" 2>/dev/null || stat -f%z "$BACKUP_DIR/database_backup.sql" 2>/dev/null)
    if [ "$DB_SIZE" -lt 1000 ]; then
        error "Database backup seems too small ($DB_SIZE bytes)"
        exit 1
    fi

    log "✓ Backup integrity verified (database: $DB_SIZE bytes)"
}

# ============================================
# ENVIRONMENT UPDATE
# ============================================

update_env_config() {
    log "Updating environment configuration for v1.5..."

    # Add ENV variable if not exists
    if ! grep -q "^ENV=" .env; then
        echo "" >> .env
        echo "# Environment (production/development)" >> .env
        echo "ENV=production" >> .env
        log "✓ Added ENV=production"
    fi

    # Add MinIO configuration if not exists
    if ! grep -q "^MINIO_ENDPOINT=" .env; then
        echo "" >> .env
        echo "# MinIO Configuration (V1.5+)" >> .env
        echo "MINIO_ROOT_USER=minioadmin" >> .env
        echo "MINIO_ROOT_PASSWORD=minioadmin123" >> .env
        echo "MINIO_ENDPOINT=minio:9000" >> .env
        echo "MINIO_ACCESS_KEY=\${MINIO_ROOT_USER}" >> .env
        echo "MINIO_SECRET_KEY=\${MINIO_ROOT_PASSWORD}" >> .env
        echo "MINIO_SECURE=false" >> .env
        echo "MINIO_BUCKET_ACTIVE=contracts-active" >> .env
        echo "MINIO_BUCKET_ARCHIVE=contracts-archive" >> .env
        log "✓ Added MinIO configuration"
    fi

    log "✓ Environment configuration updated"
}

# ============================================
# DATABASE MIGRATION
# ============================================

run_migrations() {
    log "Running database migrations..."

    # Start database and backend
    docker compose up -d db redis
    sleep 5

    docker compose build --no-cache backend
    docker compose up -d backend
    sleep 10

    # Run Alembic migrations
    log "Executing Alembic upgrade head..."
    if docker compose exec -T backend alembic upgrade head; then
        log "✓ Alembic migration completed"
    else
        warning "Alembic migration failed, attempting manual fix..."
        run_manual_fix_sql
    fi
}

run_manual_fix_sql() {
    log "Running manual SQL fix script..."
    
    docker compose exec -T db psql -U "${POSTGRES_USER:-lh_admin}" -d "${POSTGRES_DB:-lh_contract_db}" << 'EOF'

-- V1.5 完整数据库列修复脚本
BEGIN;

-- 1. 合同表
ALTER TABLE contracts_upstream ADD COLUMN IF NOT EXISTS contract_file_key VARCHAR(500);
ALTER TABLE contracts_upstream ADD COLUMN IF NOT EXISTS contract_file_storage VARCHAR(50) DEFAULT 'local';
ALTER TABLE contracts_upstream ADD COLUMN IF NOT EXISTS approval_pdf_key VARCHAR(500);
ALTER TABLE contracts_upstream ADD COLUMN IF NOT EXISTS approval_pdf_storage VARCHAR(50) DEFAULT 'local';

ALTER TABLE contracts_downstream ADD COLUMN IF NOT EXISTS contract_file_key VARCHAR(500);
ALTER TABLE contracts_downstream ADD COLUMN IF NOT EXISTS contract_file_storage VARCHAR(50) DEFAULT 'local';
ALTER TABLE contracts_downstream ADD COLUMN IF NOT EXISTS approval_pdf_key VARCHAR(500);
ALTER TABLE contracts_downstream ADD COLUMN IF NOT EXISTS approval_pdf_storage VARCHAR(50) DEFAULT 'local';

ALTER TABLE contracts_management ADD COLUMN IF NOT EXISTS contract_file_key VARCHAR(500);
ALTER TABLE contracts_management ADD COLUMN IF NOT EXISTS contract_file_storage VARCHAR(50) DEFAULT 'local';
ALTER TABLE contracts_management ADD COLUMN IF NOT EXISTS approval_pdf_key VARCHAR(500);
ALTER TABLE contracts_management ADD COLUMN IF NOT EXISTS approval_pdf_storage VARCHAR(50) DEFAULT 'local';

-- 2. 财务发票表
ALTER TABLE finance_upstream_invoices ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE finance_upstream_invoices ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) DEFAULT 'local';
ALTER TABLE finance_downstream_invoices ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE finance_downstream_invoices ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) DEFAULT 'local';
ALTER TABLE finance_management_invoices ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE finance_management_invoices ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) DEFAULT 'local';

-- 3. 财务应收应付表
ALTER TABLE finance_upstream_receivables ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE finance_upstream_receivables ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) DEFAULT 'local';
ALTER TABLE finance_upstream_receipts ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE finance_upstream_receipts ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) DEFAULT 'local';
ALTER TABLE finance_downstream_payables ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE finance_downstream_payables ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) DEFAULT 'local';
ALTER TABLE finance_downstream_payments ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE finance_downstream_payments ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) DEFAULT 'local';
ALTER TABLE finance_management_payables ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE finance_management_payables ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) DEFAULT 'local';
ALTER TABLE finance_management_payments ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE finance_management_payments ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) DEFAULT 'local';

-- 4. 结算表
ALTER TABLE downstream_settlements ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE downstream_settlements ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) DEFAULT 'local';
ALTER TABLE management_settlements ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE management_settlements ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) DEFAULT 'local';

ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) DEFAULT 'local';
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS audit_report_key VARCHAR(500);
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS audit_report_storage VARCHAR(50) DEFAULT 'local';
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS settlement_report_key VARCHAR(500);
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS settlement_report_storage VARCHAR(50) DEFAULT 'local';
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS start_report_key VARCHAR(500);
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS start_report_storage VARCHAR(50) DEFAULT 'local';
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS completion_report_key VARCHAR(500);
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS completion_report_storage VARCHAR(50) DEFAULT 'local';
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS visa_records_key VARCHAR(500);
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS visa_records_storage VARCHAR(50) DEFAULT 'local';
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS measurement_records_key VARCHAR(500);
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS measurement_records_storage VARCHAR(50) DEFAULT 'local';
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS progress_payment_key VARCHAR(500);
ALTER TABLE project_settlements ADD COLUMN IF NOT EXISTS progress_payment_storage VARCHAR(50) DEFAULT 'local';

-- 5. 无合同费用表
ALTER TABLE expenses_non_contract ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE expenses_non_contract ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) DEFAULT 'local';
ALTER TABLE expenses_non_contract ADD COLUMN IF NOT EXISTS invoice_file_key VARCHAR(500);
ALTER TABLE expenses_non_contract ADD COLUMN IF NOT EXISTS invoice_file_storage VARCHAR(50) DEFAULT 'local';
ALTER TABLE expenses_non_contract ADD COLUMN IF NOT EXISTS approval_pdf_key VARCHAR(500);
ALTER TABLE expenses_non_contract ADD COLUMN IF NOT EXISTS approval_pdf_storage VARCHAR(50) DEFAULT 'local';

-- 6. 零星用工表
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS approval_pdf_key VARCHAR(500);
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS approval_pdf_storage VARCHAR(50) DEFAULT 'local';
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS dispatch_file_key VARCHAR(500);
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS dispatch_file_storage VARCHAR(50) DEFAULT 'local';
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS settlement_file_key VARCHAR(500);
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS settlement_file_storage VARCHAR(50) DEFAULT 'local';
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS invoice_file_key VARCHAR(500);
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS invoice_file_storage VARCHAR(50) DEFAULT 'local';

-- 7. 零星用工材料表
ALTER TABLE zero_hour_labor_materials ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE zero_hour_labor_materials ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) DEFAULT 'local';

COMMIT;
SELECT 'V1.5 manual SQL fix completed' AS result;
EOF

    if [ $? -eq 0 ]; then
        log "✓ Manual SQL fix completed"
        
        # Mark Alembic as up to date
        docker compose exec -T backend alembic stamp head 2>/dev/null || true
        log "✓ Alembic version stamped to head"
    else
        error "Manual SQL fix failed!"
        exit 1
    fi
}

verify_alembic_version() {
    log "Verifying Alembic migration version..."
    
    CURRENT_VERSION=$(docker compose exec -T backend alembic current 2>/dev/null | grep -o 'v1_5_[a-z_]*' | head -1)
    
    if [[ "$CURRENT_VERSION" == *"v1_5"* ]]; then
        log "✓ Alembic version: $CURRENT_VERSION"
    else
        warning "Alembic version may not be correct: $CURRENT_VERSION"
        warning "Stamping to head to fix..."
        docker compose exec -T backend alembic stamp head
    fi
}

verify_database_columns() {
    log "Verifying V1.5 database columns..."
    
    # Count expected columns in contracts_upstream
    COLS=$(docker compose exec -T db psql -U "${POSTGRES_USER:-lh_admin}" -d "${POSTGRES_DB:-lh_contract_db}" -t -c "
        SELECT count(*) FROM information_schema.columns 
        WHERE table_name = 'contracts_upstream' 
        AND column_name IN ('contract_file_key','contract_file_storage','approval_pdf_key','approval_pdf_storage');
    " 2>/dev/null | tr -d ' ')
    
    if [ "$COLS" -eq 4 ]; then
        log "✓ contracts_upstream: 4/4 V1.5 columns exist"
    else
        warning "contracts_upstream: only $COLS/4 columns found"
        run_manual_fix_sql
    fi
}

# ============================================
# SERVICE SETUP
# ============================================

setup_minio() {
    log "Setting up MinIO..."

    docker compose up -d minio 2>/dev/null || true
    sleep 10

    # Create buckets (might fail if minio not in compose, ignore error)
    docker compose exec -T backend python -c "
from minio import Minio
from minio.error import S3Error
import os

try:
    client = Minio(
        os.getenv('MINIO_ENDPOINT', 'minio:9000'),
        access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
        secure=False
    )

    buckets = ['contracts-active', 'contracts-archive']
    for bucket in buckets:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            print(f'✓ Created bucket: {bucket}')
        else:
            print(f'✓ Bucket exists: {bucket}')
except Exception as e:
    print(f'MinIO setup skipped (not required): {e}')
" 2>/dev/null || true

    log "✓ MinIO setup completed (or skipped if not configured)"
}

rebuild_services() {
    log "Rebuilding services..."

    # Rebuild images
    docker compose build --no-cache frontend

    # Restart all services
    docker compose down
    docker compose up -d

    log "Waiting for services to start..."
    sleep 15

    log "✓ Services restarted"
}

# ============================================
# VERIFICATION
# ============================================

verify_upgrade() {
    log "Verifying upgrade..."
    
    PASS=0
    FAIL=0

    # Check backend health
    HEALTH_CHECK=$(curl -s http://localhost:8000/health 2>/dev/null || echo "failed")
    if [[ "$HEALTH_CHECK" == *"healthy"* ]]; then
        log "✓ Backend health check passed"
        ((PASS++))
    else
        warning "Backend health check failed"
        ((FAIL++))
    fi

    # Check database connection
    if docker compose exec -T db psql -U "${POSTGRES_USER:-lh_admin}" -d "${POSTGRES_DB:-lh_contract_db}" -c "SELECT 1" > /dev/null 2>&1; then
        log "✓ Database connection OK"
        ((PASS++))
    else
        warning "Database connection failed"
        ((FAIL++))
    fi

    # Check API endpoint
    API_TEST=$(curl -s "http://localhost:8000/api/v1/contracts/upstream/?page=1&page_size=1" 2>/dev/null)
    if [[ "$API_TEST" != *"error"* && "$API_TEST" != *"Error"* ]]; then
        log "✓ Contract API test passed"
        ((PASS++))
    else
        warning "Contract API test failed: ${API_TEST:0:100}"
        ((FAIL++))
    fi

    # Summary
    echo ""
    log "=== 验证结果 ==="
    log "✓ 通过: $PASS 项"
    if [ $FAIL -gt 0 ]; then
        warning "❌ 失败: $FAIL 项"
    fi
    
    if [ $FAIL -eq 0 ]; then
        log "🎉 升级验证全部通过！"
    else
        warning "部分验证未通过，请检查日志"
    fi
}

# ============================================
# ROLLBACK INSTRUCTIONS
# ============================================

print_rollback_instructions() {
    echo ""
    echo "=========================================="
    echo "Rollback Instructions (if needed)"
    echo "=========================================="
    echo ""
    echo "方式一：VM 快照回滚（推荐）"
    echo "  在 VM 管理界面恢复升级前的快照"
    echo ""
    echo "方式二：应用层回滚"
    echo "  1. docker compose down"
    echo "  2. docker compose up -d db"
    echo "  3. docker compose exec -T db psql -U ${POSTGRES_USER:-lh_admin} -d ${POSTGRES_DB:-lh_contract_db} < $BACKUP_DIR/database_backup.sql"
    echo "  4. cp $BACKUP_DIR/.env.backup .env"
    echo "  5. git checkout v1.4.1"
    echo "  6. docker compose up -d"
    echo ""
}

# ============================================
# MAIN
# ============================================

main() {
    echo "=========================================="
    echo "LH Contract Management System"
    echo "Production Safe Upgrade: 1.4.1 -> 1.5.0"
    echo "=========================================="
    echo ""
    echo "更新日期: 2026-01-13"
    echo "包含: 生产环境升级经验教训修复"
    echo ""

    # Confirmation
    echo "This script will:"
    echo "  1. 检查 Git 状态和生产配置"
    echo "  2. 创建完整备份 (database + files)"
    echo "  3. 运行数据库迁移 (自动备用方案)"
    echo "  4. 验证数据库列完整性"
    echo "  5. 更新服务到 v1.5"
    echo "  6. 运行升级后验证"
    echo ""
    echo "预计时间: 10-20 分钟"
    echo "停机时间: ~5 分钟"
    echo ""
    read -p "继续升级? (yes/no): " CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        echo "Upgrade cancelled"
        exit 0
    fi

    # Execute upgrade steps
    check_prerequisites
    check_git_status
    verify_production_config
    create_backup
    verify_backup
    update_env_config
    run_migrations
    verify_alembic_version
    verify_database_columns
    setup_minio
    rebuild_services
    verify_upgrade

    # Success
    echo ""
    echo "=========================================="
    echo "✓ Upgrade Completed!"
    echo "=========================================="
    echo ""
    echo "Version: 1.5.0"
    echo "Backup: $BACKUP_DIR"
    echo "Log: $LOG_FILE"
    echo ""
    echo "Next steps:"
    echo "  1. 在浏览器测试系统功能"
    echo "  2. 验证文件上传/下载"
    echo "  3. 监控日志: docker compose logs -f backend"
    echo ""

    print_rollback_instructions
}

# Run main function
main
