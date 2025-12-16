#!/bin/bash

# ============================================
# 蓝海合同管理系统 - 自动备份脚本
# 版本: 1.0
# 用途: 备份数据库和文件
# ============================================

set -e  # 遇到错误立即退出

# 配置
BACKUP_ROOT="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# 数据库配置
DB_CONTAINER="lh_contract_db_prod"
DB_USER="lh_admin"
DB_NAME="lh_contract_db"

# 备份目录
DB_BACKUP_DIR="$BACKUP_ROOT/database"
FILES_BACKUP_DIR="$BACKUP_ROOT/uploads"
LOG_FILE="$BACKUP_ROOT/backup.log"

# 创建备份目录
mkdir -p $DB_BACKUP_DIR
mkdir -p $FILES_BACKUP_DIR

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

log "========================================="
log "开始备份任务"
log "========================================="

# ============================================
# 1. 数据库备份
# ============================================
log "正在备份数据库..."

DB_BACKUP_FILE="$DB_BACKUP_DIR/lh_contract_db_$DATE.sql"

docker exec $DB_CONTAINER pg_dump \
    -U $DB_USER \
    -d $DB_NAME \
    -F c \
    -f /backups/database/lh_contract_db_$DATE.sql

if [ $? -eq 0 ]; then
    # 压缩备份文件
    gzip $DB_BACKUP_FILE
    
    DB_SIZE=$(du -h "${DB_BACKUP_FILE}.gz" | cut -f1)
    log "✓ 数据库备份完成: ${DB_BACKUP_FILE}.gz (大小: $DB_SIZE)"
else
    log "✗ 数据库备份失败"
    exit 1
fi

# ============================================
# 2. 上传文件备份
# ============================================
log "正在备份上传文件..."

FILES_BACKUP_FILE="$FILES_BACKUP_DIR/uploads_$DATE.tar.gz"

tar -czf $FILES_BACKUP_FILE ./uploads

if [ $? -eq 0 ]; then
    FILES_SIZE=$(du -h $FILES_BACKUP_FILE | cut -f1)
    log "✓ 文件备份完成: $FILES_BACKUP_FILE (大小: $FILES_SIZE)"
else
    log "✗ 文件备份失败"
fi

# ============================================
# 3. 清理旧备份
# ============================================
log "正在清理 $RETENTION_DAYS 天前的旧备份..."

# 删除旧的数据库备份
DELETED_DB=$(find $DB_BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
log "✓ 删除了 $DELETED_DB 个旧数据库备份"

# 删除旧的文件备份
DELETED_FILES=$(find $FILES_BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
log "✓ 删除了 $DELETED_FILES 个旧文件备份"

# ============================================
# 4. 备份统计
# ============================================
log "========================================="
log "备份统计信息"
log "========================================="

DB_COUNT=$(find $DB_BACKUP_DIR -name "*.sql.gz" | wc -l)
FILES_COUNT=$(find $FILES_BACKUP_DIR -name "*.tar.gz" | wc -l)
TOTAL_SIZE=$(du -sh $BACKUP_ROOT | cut -f1)

log "数据库备份数量: $DB_COUNT"
log "文件备份数量: $FILES_COUNT"
log "备份总大小: $TOTAL_SIZE"

# ============================================
# 5. 远程备份 (可选)
# ============================================
# 取消注释以启用远程备份
# REMOTE_SERVER="backup-server"
# REMOTE_PATH="/remote/backups/lh_contract"
# 
# log "正在同步到远程服务器..."
# rsync -avz --delete $BACKUP_ROOT/ $REMOTE_SERVER:$REMOTE_PATH/
# 
# if [ $? -eq 0 ]; then
#     log "✓ 远程同步完成"
# else
#     log "✗ 远程同步失败"
# fi

log "========================================="
log "备份任务完成"
log "========================================="

exit 0
