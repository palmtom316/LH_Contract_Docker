#!/usr/bin/env bash

# ============================================
# 蓝海合同管理系统 - 自动备份脚本
# 版本: 1.1
# 用途: 升级前基线备份与安全快照
# ============================================

set -u
set -o pipefail

DATE="$(date +%Y%m%d_%H%M%S)"

# 基础配置（支持环境变量覆盖）
BACKUP_ROOT="${BACKUP_ROOT:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
DB_USER="${DB_USER:-${POSTGRES_USER:-postgres}}"
DB_NAME="${DB_NAME:-${POSTGRES_DB:-lh_contract}}"
DB_CONTAINER="${DB_CONTAINER:-}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-}"
UPLOADS_SOURCE_DIR="${UPLOADS_SOURCE_DIR:-./uploads}"
MINIO_ALIAS="${MINIO_ALIAS:-lhminio}"
MINIO_BUCKET="${MINIO_BUCKET:-${MINIO_BUCKET_CONTRACTS:-contracts-active}}"

if ! mkdir -p "${BACKUP_ROOT}" 2>/dev/null || ! touch "${BACKUP_ROOT}/.write_test" 2>/dev/null; then
    BACKUP_ROOT="./backups"
    mkdir -p "${BACKUP_ROOT}"
else
    rm -f "${BACKUP_ROOT}/.write_test"
fi

DB_BACKUP_DIR="${BACKUP_ROOT}/database"
FILES_BACKUP_DIR="${BACKUP_ROOT}/uploads"
DICTIONARY_DIR="${BACKUP_ROOT}/dictionaries"
OBJECT_STORE_DIR="${BACKUP_ROOT}/object_store"
BASELINE_DIR="${BACKUP_ROOT}/baseline"
LOG_FILE="${BACKUP_ROOT}/backup.log"

mkdir -p "${DB_BACKUP_DIR}" "${FILES_BACKUP_DIR}" "${DICTIONARY_DIR}" "${OBJECT_STORE_DIR}" "${BASELINE_DIR}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

warn() {
    log "⚠️  $1"
}

has_command() {
    command -v "$1" >/dev/null 2>&1
}

find_container() {
    local explicit="$1"
    shift
    if [ -n "${explicit}" ]; then
        echo "${explicit}"
        return 0
    fi

    local names
    names="$(docker ps --format '{{.Names}}' 2>/dev/null || true)"
    local candidate
    for candidate in "$@"; do
        if echo "${names}" | grep -Fxq "${candidate}"; then
            echo "${candidate}"
            return 0
        fi
    done
    return 1
}

run_psql() {
    local sql="$1"
    docker exec "${RESOLVED_DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -At -F ',' -c "${sql}"
}

CRITICAL_FAILURES=0
WARNINGS=0

log "========================================="
log "开始备份任务（升级前基线模式）"
log "========================================="

if ! has_command docker; then
    log "✗ 未找到 docker 命令，无法执行容器内备份"
    exit 1
fi

if RESOLVED_DB_CONTAINER="$(find_container "${DB_CONTAINER}" lh_db_prod lh_contract_db_prod db)"; then
    log "数据库容器: ${RESOLVED_DB_CONTAINER}"
else
    log "✗ 未找到数据库容器，请通过 DB_CONTAINER 指定"
    exit 1
fi

if RESOLVED_BACKEND_CONTAINER="$(find_container "${BACKEND_CONTAINER}" lh_backend_prod lh_contract_backend_prod backend)"; then
    log "后端容器: ${RESOLVED_BACKEND_CONTAINER}"
else
    warn "未找到后端容器，将仅尝试从主机目录备份 uploads"
    WARNINGS=$((WARNINGS + 1))
    RESOLVED_BACKEND_CONTAINER=""
fi

DB_BACKUP_FILE="${DB_BACKUP_DIR}/lh_contract_db_${DATE}.sql"
DB_TMP_FILE="/tmp/lh_contract_db_${DATE}.sql"

log "正在备份 PostgreSQL 全库..."
if docker exec "${RESOLVED_DB_CONTAINER}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" -F p -f "${DB_TMP_FILE}" \
    && docker cp "${RESOLVED_DB_CONTAINER}:${DB_TMP_FILE}" "${DB_BACKUP_FILE}" \
    && docker exec "${RESOLVED_DB_CONTAINER}" rm -f "${DB_TMP_FILE}"; then
    gzip -f "${DB_BACKUP_FILE}"
    DB_SIZE="$(du -h "${DB_BACKUP_FILE}.gz" | cut -f1)"
    log "✓ 数据库备份完成: ${DB_BACKUP_FILE}.gz (大小: ${DB_SIZE})"
else
    log "✗ 数据库备份失败"
    CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
fi

FILES_BACKUP_FILE="${FILES_BACKUP_DIR}/uploads_${DATE}.tar.gz"
log "正在备份 uploads 目录..."
if [ -d "${UPLOADS_SOURCE_DIR}" ]; then
    if tar -czf "${FILES_BACKUP_FILE}" "${UPLOADS_SOURCE_DIR}"; then
        FILES_SIZE="$(du -h "${FILES_BACKUP_FILE}" | cut -f1)"
        log "✓ 文件备份完成(主机目录): ${FILES_BACKUP_FILE} (大小: ${FILES_SIZE})"
    else
        log "✗ 主机目录 uploads 备份失败"
        CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
    fi
elif [ -n "${RESOLVED_BACKEND_CONTAINER}" ]; then
    FILES_TMP_FILE="/tmp/uploads_${DATE}.tar.gz"
    if docker exec "${RESOLVED_BACKEND_CONTAINER}" sh -lc "tar -czf ${FILES_TMP_FILE} -C /app uploads" \
        && docker cp "${RESOLVED_BACKEND_CONTAINER}:${FILES_TMP_FILE}" "${FILES_BACKUP_FILE}" \
        && docker exec "${RESOLVED_BACKEND_CONTAINER}" rm -f "${FILES_TMP_FILE}"; then
        FILES_SIZE="$(du -h "${FILES_BACKUP_FILE}" | cut -f1)"
        log "✓ 文件备份完成(容器目录): ${FILES_BACKUP_FILE} (大小: ${FILES_SIZE})"
    else
        log "✗ 容器目录 uploads 备份失败"
        CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
    fi
else
    warn "未找到 uploads 目录，跳过文件备份"
    WARNINGS=$((WARNINGS + 1))
fi

DICT_JSON_FILE="${DICTIONARY_DIR}/sys_dictionaries_${DATE}.json"
DICT_CSV_FILE="${DICTIONARY_DIR}/sys_dictionaries_${DATE}.csv"
log "正在导出 sys_dictionaries 快照..."
if [ "$(run_psql "SELECT to_regclass('public.sys_dictionaries') IS NOT NULL;")" = "t" ]; then
    if run_psql "SELECT COALESCE(json_agg(t), '[]'::json) FROM (SELECT * FROM sys_dictionaries ORDER BY id) t;" > "${DICT_JSON_FILE}" \
        && docker exec "${RESOLVED_DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "COPY (SELECT * FROM sys_dictionaries ORDER BY id) TO STDOUT WITH CSV HEADER" > "${DICT_CSV_FILE}"; then
        log "✓ 字典快照导出完成: ${DICT_JSON_FILE}, ${DICT_CSV_FILE}"
    else
        warn "字典快照导出失败"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    warn "未发现 sys_dictionaries 表，跳过字典导出"
    WARNINGS=$((WARNINGS + 1))
fi

OBJECT_SNAPSHOT_FILE="${OBJECT_STORE_DIR}/minio_snapshot_${DATE}.txt"
log "正在采集对象存储摘要..."
if has_command mc; then
    if mc du --json "${MINIO_ALIAS}/${MINIO_BUCKET}" > "${OBJECT_SNAPSHOT_FILE}" 2>/dev/null \
        && mc ls --recursive "${MINIO_ALIAS}/${MINIO_BUCKET}" 2>/dev/null | awk 'END {print "object_count=" NR}' >> "${OBJECT_SNAPSHOT_FILE}"; then
        log "✓ MinIO 摘要采集完成: ${OBJECT_SNAPSHOT_FILE}"
    else
        {
            echo "status=skipped"
            echo "reason=mc_available_but_snapshot_failed"
            echo "alias=${MINIO_ALIAS}"
            echo "bucket=${MINIO_BUCKET}"
        } > "${OBJECT_SNAPSHOT_FILE}"
        warn "mc 可用但 MinIO 摘要采集失败（请确认 alias/bucket 配置）"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    {
        echo "status=skipped"
        echo "reason=mc_not_installed"
        echo "alias=${MINIO_ALIAS}"
        echo "bucket=${MINIO_BUCKET}"
    } > "${OBJECT_SNAPSHOT_FILE}"
    warn "未安装 mc，跳过 MinIO 摘要采集"
    WARNINGS=$((WARNINGS + 1))
fi

BASELINE_FILE="${BASELINE_DIR}/baseline_${DATE}.txt"
log "正在采集业务基线统计..."
{
    echo "captured_at=${DATE}"
    echo "users_total=$(run_psql "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "N/A")"
    echo "contracts_total=$(run_psql "SELECT (SELECT COUNT(*) FROM contracts_upstream) + (SELECT COUNT(*) FROM contracts_downstream) + (SELECT COUNT(*) FROM contracts_management);" 2>/dev/null || echo "N/A")"
    echo "expenses_total=$(run_psql "SELECT (SELECT COUNT(*) FROM expenses_non_contract) + (SELECT COUNT(*) FROM zero_hour_labor);" 2>/dev/null || echo "N/A")"
    echo "audit_logs_total=$(run_psql "SELECT COUNT(*) FROM audit_logs;" 2>/dev/null || echo "N/A")"
    echo "new_records_last_30_days=$(run_psql "SELECT (SELECT COUNT(*) FROM contracts_upstream WHERE created_at >= now() - interval '30 days') + (SELECT COUNT(*) FROM contracts_downstream WHERE created_at >= now() - interval '30 days') + (SELECT COUNT(*) FROM contracts_management WHERE created_at >= now() - interval '30 days') + (SELECT COUNT(*) FROM expenses_non_contract WHERE created_at >= now() - interval '30 days') + (SELECT COUNT(*) FROM zero_hour_labor WHERE created_at >= now() - interval '30 days') + (SELECT COUNT(*) FROM audit_logs WHERE created_at >= now() - interval '30 days');" 2>/dev/null || echo "N/A")"
    echo "active_dictionary_values=$(run_psql "SELECT COALESCE(string_agg(concat(category, ':', label, '=', value), '; ' ORDER BY category, label), '') FROM sys_dictionaries WHERE is_active = true;" 2>/dev/null || echo "N/A")"
} > "${BASELINE_FILE}"
log "✓ 基线统计已输出: ${BASELINE_FILE}"

log "正在清理 ${RETENTION_DAYS} 天前的旧备份..."
DELETED_DB="$(find "${DB_BACKUP_DIR}" -name "*.sql.gz" -mtime +"${RETENTION_DAYS}" -print -delete | wc -l | tr -d ' ')"
DELETED_FILES="$(find "${FILES_BACKUP_DIR}" -name "*.tar.gz" -mtime +"${RETENTION_DAYS}" -print -delete | wc -l | tr -d ' ')"
log "✓ 删除了 ${DELETED_DB} 个旧数据库备份"
log "✓ 删除了 ${DELETED_FILES} 个旧文件备份"

DB_COUNT="$(find "${DB_BACKUP_DIR}" -name "*.sql.gz" | wc -l | tr -d ' ')"
FILES_COUNT="$(find "${FILES_BACKUP_DIR}" -name "*.tar.gz" | wc -l | tr -d ' ')"
TOTAL_SIZE="$(du -sh "${BACKUP_ROOT}" | cut -f1)"

log "========================================="
log "备份统计信息"
log "========================================="
log "数据库备份数量: ${DB_COUNT}"
log "文件备份数量: ${FILES_COUNT}"
log "备份总大小: ${TOTAL_SIZE}"
log "警告数量: ${WARNINGS}"
log "关键失败数量: ${CRITICAL_FAILURES}"

if [ "${CRITICAL_FAILURES}" -gt 0 ]; then
    log "备份任务完成，但存在关键失败"
    exit 1
fi

log "========================================="
log "备份任务完成"
log "========================================="
exit 0
