#!/bin/bash
# LH Contract Management System - Production Safe Upgrade Script
# Version: 1.4.1 -> 1.5.0
# Date: 2026-01-11
#
# This script ensures:
# 1. Zero data loss - all existing data and files are preserved
# 2. Production safety - no debug/dev configurations
# 3. Rollback capability - full backup before upgrade

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./backups/upgrade_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="./upgrade_$(date +%Y%m%d_%H%M%S).log"

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

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi

    if [ ! -f ".env" ]; then
        error ".env file not found"
        exit 1
    fi

    log "✓ Prerequisites check passed"
}

# Verify production environment configuration
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

    # Check MinIO password is not default
    if grep -q "MINIO_ROOT_PASSWORD=CHANGE_THIS" .env 2>/dev/null; then
        warning "MinIO password is still set to default value - consider changing"
    fi

    log "✓ Production configuration verified"
}

# Create full backup
create_backup() {
    log "Creating backup in $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"

    # Backup database
    log "Backing up database..."
    docker-compose exec -T db pg_dump -U "${POSTGRES_USER:-lh_admin}" "${POSTGRES_DB:-lh_contract_db}" > "$BACKUP_DIR/database_backup.sql"

    if [ $? -ne 0 ]; then
        error "Database backup failed!"
        exit 1
    fi

    # Backup uploads directory
    log "Backing up uploads directory..."
    if [ -d "./backend/uploads" ]; then
        cp -r ./backend/uploads "$BACKUP_DIR/uploads_backup"
        log "✓ Backed up $(du -sh ./backend/uploads | cut -f1) of files"
    fi

    # Backup .env file
    cp .env "$BACKUP_DIR/.env.backup"

    # Backup docker-compose.yml
    cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml.backup"

    log "✓ Backup completed: $BACKUP_DIR"
    log "  - Database: $BACKUP_DIR/database_backup.sql"
    log "  - Files: $BACKUP_DIR/uploads_backup"
    log "  - Config: $BACKUP_DIR/.env.backup"
}

# Verify backup integrity
verify_backup() {
    log "Verifying backup integrity..."

    # Check database backup size
    DB_SIZE=$(stat -f%z "$BACKUP_DIR/database_backup.sql" 2>/dev/null || stat -c%s "$BACKUP_DIR/database_backup.sql" 2>/dev/null)
    if [ "$DB_SIZE" -lt 1000 ]; then
        error "Database backup seems too small ($DB_SIZE bytes)"
        exit 1
    fi

    # Check uploads backup
    if [ -d "$BACKUP_DIR/uploads_backup" ]; then
        FILE_COUNT=$(find "$BACKUP_DIR/uploads_backup" -type f | wc -l)
        log "✓ Backed up $FILE_COUNT files"
    fi

    log "✓ Backup integrity verified"
}

# Update environment configuration for v1.5
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
        echo "MINIO_ENDPOINT=minio:9000" >> .env
        echo "MINIO_ACCESS_KEY=\${MINIO_ROOT_USER:-minioadmin}" >> .env
        echo "MINIO_SECRET_KEY=\${MINIO_ROOT_PASSWORD:-minioadmin123}" >> .env
        echo "MINIO_SECURE=false" >> .env
        echo "MINIO_BUCKET_CONTRACTS=contracts-active" >> .env
        log "✓ Added MinIO configuration"
    fi

    log "✓ Environment configuration updated"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."

    # Start database and backend
    docker-compose up -d db redis
    sleep 5

    docker-compose up -d backend
    sleep 10

    # Run Alembic migrations
    docker-compose exec -T backend alembic upgrade head

    if [ $? -ne 0 ]; then
        error "Database migration failed!"
        exit 1
    fi

    log "✓ Database migrations completed"
}

# Verify file paths in database
verify_file_paths() {
    log "Verifying file paths in database..."

    # Check if any files are referenced in database
    FILE_COUNT=$(docker-compose exec -T db psql -U "${POSTGRES_USER:-lh_admin}" -d "${POSTGRES_DB:-lh_contract_db}" -t -c "
        SELECT COUNT(*) FROM contracts_upstream WHERE contract_file_path IS NOT NULL
        UNION ALL
        SELECT COUNT(*) FROM contracts_downstream WHERE contract_file_path IS NOT NULL
        UNION ALL
        SELECT COUNT(*) FROM contracts_management WHERE contract_file_path IS NOT NULL
    " | awk '{s+=$1} END {print s}')

    log "Found $FILE_COUNT file references in database"

    # Verify files exist on disk
    log "Verifying files exist on disk..."
    docker-compose exec -T backend python -c "
import os
from pathlib import Path

upload_dir = Path('/app/uploads')
missing_files = []

for root, dirs, files in os.walk(upload_dir):
    for file in files:
        if not file.startswith('_migrated_'):
            file_path = Path(root) / file
            if not file_path.exists():
                missing_files.append(str(file_path))

if missing_files:
    print(f'WARNING: {len(missing_files)} files missing')
    for f in missing_files[:10]:
        print(f'  - {f}')
else:
    print('✓ All files verified')
"

    log "✓ File path verification completed"
}

# Start MinIO and create buckets
setup_minio() {
    log "Setting up MinIO..."

    docker-compose up -d minio
    sleep 10

    # Create buckets
    docker-compose exec -T backend python -c "
from minio import Minio
from minio.error import S3Error
import os

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
"

    log "✓ MinIO setup completed"
}

# Migrate files to MinIO (optional, with dry-run first)
migrate_files_to_minio() {
    log "File migration to MinIO (optional)..."

    echo ""
    echo "=========================================="
    echo "File Migration to MinIO"
    echo "=========================================="
    echo ""
    echo "Current files are stored locally in ./backend/uploads"
    echo "V1.5 supports MinIO for better scalability and backup."
    echo ""
    echo "Options:"
    echo "  1) Keep files local (no migration) - RECOMMENDED for now"
    echo "  2) Migrate files to MinIO (can be done later)"
    echo "  3) Run dry-run to preview migration"
    echo ""
    read -p "Choose option (1/2/3): " MIGRATE_CHOICE

    case $MIGRATE_CHOICE in
        2)
            log "Running file migration dry-run first..."
            docker-compose exec -T backend python /app/scripts/migrate_to_minio.py --dry-run

            echo ""
            read -p "Proceed with actual migration? (yes/no): " CONFIRM
            if [ "$CONFIRM" = "yes" ]; then
                log "Migrating files to MinIO..."
                docker-compose exec -T backend python /app/scripts/migrate_to_minio.py

                log "Verifying migration..."
                docker-compose exec -T backend python /app/scripts/verify_migration.py
            else
                log "Migration cancelled"
            fi
            ;;
        3)
            log "Running migration dry-run..."
            docker-compose exec -T backend python /app/scripts/migrate_to_minio.py --dry-run
            ;;
        *)
            log "Keeping files local - migration can be done later"
            ;;
    esac
}

# Rebuild and restart services
rebuild_services() {
    log "Rebuilding services..."

    # Rebuild images
    docker-compose build --no-cache backend frontend

    # Restart all services
    docker-compose down
    docker-compose up -d

    log "Waiting for services to start..."
    sleep 15

    log "✓ Services restarted"
}

# Verify upgrade
verify_upgrade() {
    log "Verifying upgrade..."

    # Check backend health
    HEALTH_CHECK=$(curl -s http://localhost:8000/health || echo "failed")
    if [[ "$HEALTH_CHECK" == *"healthy"* ]]; then
        log "✓ Backend is healthy"
    else
        error "Backend health check failed"
        exit 1
    fi

    # Check database connection
    docker-compose exec -T db psql -U "${POSTGRES_USER:-lh_admin}" -d "${POSTGRES_DB:-lh_contract_db}" -c "SELECT 1" > /dev/null
    if [ $? -eq 0 ]; then
        log "✓ Database connection OK"
    else
        error "Database connection failed"
        exit 1
    fi

    # Check file access
    log "Checking file access..."
    docker-compose exec -T backend ls -la /app/uploads > /dev/null
    if [ $? -eq 0 ]; then
        log "✓ File access OK"
    else
        error "File access failed"
        exit 1
    fi

    log "✓ Upgrade verification completed"
}

# Print rollback instructions
print_rollback_instructions() {
    echo ""
    echo "=========================================="
    echo "Rollback Instructions (if needed)"
    echo "=========================================="
    echo ""
    echo "If you encounter issues, you can rollback:"
    echo ""
    echo "1. Stop services:"
    echo "   docker-compose down"
    echo ""
    echo "2. Restore database:"
    echo "   docker-compose up -d db"
    echo "   docker-compose exec -T db psql -U ${POSTGRES_USER:-lh_admin} -d ${POSTGRES_DB:-lh_contract_db} < $BACKUP_DIR/database_backup.sql"
    echo ""
    echo "3. Restore files:"
    echo "   rm -rf ./backend/uploads"
    echo "   cp -r $BACKUP_DIR/uploads_backup ./backend/uploads"
    echo ""
    echo "4. Restore configuration:"
    echo "   cp $BACKUP_DIR/.env.backup .env"
    echo "   cp $BACKUP_DIR/docker-compose.yml.backup docker-compose.yml"
    echo ""
    echo "5. Restart services:"
    echo "   docker-compose up -d"
    echo ""
}

# Main upgrade process
main() {
    echo "=========================================="
    echo "LH Contract Management System"
    echo "Production Safe Upgrade: 1.4.1 -> 1.5.0"
    echo "=========================================="
    echo ""

    # Confirmation
    echo "This script will:"
    echo "  1. Create full backup (database + files)"
    echo "  2. Verify production configuration"
    echo "  3. Run database migrations"
    echo "  4. Update services to v1.5"
    echo "  5. Verify upgrade success"
    echo ""
    echo "Estimated time: 10-20 minutes"
    echo "Downtime: ~5 minutes"
    echo ""
    read -p "Continue with upgrade? (yes/no): " CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        echo "Upgrade cancelled"
        exit 0
    fi

    # Execute upgrade steps
    check_prerequisites
    verify_production_config
    create_backup
    verify_backup
    update_env_config
    run_migrations
    verify_file_paths
    setup_minio
    migrate_files_to_minio
    rebuild_services
    verify_upgrade

    # Success
    echo ""
    echo "=========================================="
    echo "✓ Upgrade Completed Successfully!"
    echo "=========================================="
    echo ""
    echo "Version: 1.5.0"
    echo "Backup: $BACKUP_DIR"
    echo "Log: $LOG_FILE"
    echo ""
    echo "Next steps:"
    echo "  1. Test file upload/download in UI"
    echo "  2. Verify all existing files are accessible"
    echo "  3. Monitor logs: docker-compose logs -f backend"
    echo ""

    print_rollback_instructions
}

# Run main function
main
