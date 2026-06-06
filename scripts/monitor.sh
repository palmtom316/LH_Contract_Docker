#!/bin/bash

# ============================================
# 合同管理系统 - 健康监控脚本
# 用途:
# 1. 常规健康检查
# 2. hardening 升级后的兼容性巡检
# 3. 关键回滚信号提前告警
# ============================================

set -u

APP_URL="${APP_URL:-http://localhost}"
API_BASE_URL="${API_BASE_URL:-${APP_URL%/}/api/v1}"
LOG_FILE="${LOG_FILE:-/var/log/lh_contract_monitor.log}"
ALERT_EMAIL="${ALERT_EMAIL:-admin@example.com}"
ALERT_THRESHOLD="${ALERT_THRESHOLD:-3}"
FAILURE_COUNT_FILE="${FAILURE_COUNT_FILE:-/tmp/lh_contract_failures}"

DB_CONTAINER="${DB_CONTAINER:-lh_contract_db_prod}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-lh_contract_backend_prod}"
REDIS_CONTAINER="${REDIS_CONTAINER:-lh_contract_redis_prod}"

MONITOR_BEARER_TOKEN="${MONITOR_BEARER_TOKEN:-}"
MONITOR_FILE_URL="${MONITOR_FILE_URL:-}"

mkdir -p "$(dirname "$FAILURE_COUNT_FILE")" 2>/dev/null || true
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

if [ ! -f "$FAILURE_COUNT_FILE" ]; then
    echo "0" > "$FAILURE_COUNT_FILE"
fi

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_alert() {
    local message="$1"
    log "ALERT: $message"
    # 可在此接入邮件、钉钉、企业微信或其他 webhook
    # echo "$message" | mail -s "LH Contract System Alert" "$ALERT_EMAIL"
}

increment_failure() {
    local count
    count="$(cat "$FAILURE_COUNT_FILE" 2>/dev/null || echo 0)"
    count=$((count + 1))
    echo "$count" > "$FAILURE_COUNT_FILE"
    echo "$count"
}

reset_failure() {
    echo "0" > "$FAILURE_COUNT_FILE"
}

request_status() {
    local url="$1"
    shift || true
    curl -sS -o /dev/null -w "%{http_code}" "$@" "$url"
}

check_application() {
    log "检查应用健康状态..."

    local response
    response="$(request_status "${APP_URL%/}/health")"

    if [ "$response" = "200" ]; then
        log "PASS 应用健康检查通过 (HTTP $response)"
        reset_failure
        return 0
    fi

    log "FAIL 应用健康检查失败 (HTTP $response)"
    local failures
    failures="$(increment_failure)"
    if [ "$failures" -ge "$ALERT_THRESHOLD" ]; then
        send_alert "应用健康检查连续失败 ${failures} 次，HTTP=${response}"
    fi
    return 1
}

check_detailed_health() {
    log "执行详细健康检查..."

    local health_json
    health_json="$(curl -sS "${APP_URL%/}/health/detailed" 2>/dev/null || true)"
    if [ -z "$health_json" ]; then
        log "FAIL 详细健康检查无响应"
        send_alert "详细健康检查接口无响应"
        return 1
    fi

    local status
    status="$(echo "$health_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo unknown)"

    if [ "$status" = "healthy" ] || [ "$status" = "degraded" ]; then
        local db_latency
        local redis_status
        local minio_status
        db_latency="$(echo "$health_json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('checks',{}).get('database',{}).get('latency_ms','n/a'))" 2>/dev/null || echo n/a)"
        redis_status="$(echo "$health_json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('checks',{}).get('redis',{}).get('status','unknown'))" 2>/dev/null || echo unknown)"
        minio_status="$(echo "$health_json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('checks',{}).get('minio',{}).get('status','unknown'))" 2>/dev/null || echo unknown)"
        log "PASS 详细健康检查状态=${status}, db_latency=${db_latency}ms, redis=${redis_status}, minio=${minio_status}"
        return 0
    fi

    log "FAIL 详细健康检查异常: status=${status}"
    send_alert "系统详细健康检查异常: ${status}"
    return 1
}

check_dictionary_compatibility() {
    log "检查数据字典兼容接口..."

    local url="${API_BASE_URL%/}/system/options?category=expense_type"
    local code
    code="$(request_status "$url")"

    if [ "$code" = "200" ]; then
        log "PASS expense_type 字典接口可访问"
        return 0
    fi

    log "FAIL expense_type 字典接口异常 (HTTP $code)"
    send_alert "expense_type 字典接口异常，可能影响历史费用类别显示: HTTP ${code}"
    return 1
}

check_authenticated_smoke() {
    if [ -z "$MONITOR_BEARER_TOKEN" ]; then
        log "SKIP 未配置 MONITOR_BEARER_TOKEN，跳过登录态冒烟检查"
        return 0
    fi

    log "检查登录态与附件兼容巡检..."

    local me_code
    me_code="$(request_status "${API_BASE_URL%/}/auth/me" -H "Authorization: Bearer ${MONITOR_BEARER_TOKEN}")"
    if [ "$me_code" != "200" ]; then
        log "FAIL 登录态巡检失败 (HTTP $me_code)"
        send_alert "登录态巡检失败，可能存在 token/refresh 回归: HTTP ${me_code}"
        return 1
    fi

    log "PASS 登录态巡检通过"

    if [ -n "$MONITOR_FILE_URL" ]; then
        local file_code
        file_code="$(request_status "$MONITOR_FILE_URL" -H "Authorization: Bearer ${MONITOR_BEARER_TOKEN}")"
        if [ "$file_code" != "200" ]; then
            log "FAIL 历史附件巡检失败 (HTTP $file_code)"
            send_alert "历史附件巡检失败，可能出现 401/404 回归: HTTP ${file_code}"
            return 1
        fi
        log "PASS 历史附件巡检通过"
    else
        log "SKIP 未配置 MONITOR_FILE_URL，跳过历史附件巡检"
    fi

    return 0
}

check_containers() {
    if ! command -v docker >/dev/null 2>&1; then
        log "SKIP 未检测到 docker，跳过容器检查"
        return 0
    fi

    log "检查 Docker 容器状态..."

    local containers=("$DB_CONTAINER" "$REDIS_CONTAINER" "$BACKEND_CONTAINER")
    local all_healthy=true

    for container in "${containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -qx "$container"; then
            local status
            status="$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}running{{end}}' "$container" 2>/dev/null || echo unknown)"
            if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
                log "PASS ${container}: ${status}"
            else
                log "FAIL ${container}: ${status}"
                send_alert "容器 ${container} 状态异常: ${status}"
                all_healthy=false
            fi
        else
            log "FAIL ${container}: 未运行"
            send_alert "容器 ${container} 未运行"
            all_healthy=false
        fi
    done

    $all_healthy
}

check_system_resources() {
    log "检查系统资源..."

    if command -v top >/dev/null 2>&1; then
        local cpu_usage
        cpu_usage="$(top -bn1 2>/dev/null | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}' || echo 0)"
        log "INFO CPU使用率: ${cpu_usage}%"
    fi

    if command -v free >/dev/null 2>&1; then
        local mem_usage
        mem_usage="$(free | grep Mem | awk '{print ($3/$2) * 100.0}' || echo 0)"
        log "INFO 内存使用率: $(printf "%.1f" "$mem_usage")%"
        if command -v bc >/dev/null 2>&1 && [ "$(echo "$mem_usage > 90" | bc -l)" -eq 1 ]; then
            send_alert "内存使用率过高: $(printf "%.1f" "$mem_usage")%"
        fi
    fi

    local disk_usage
    disk_usage="$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//' || echo 0)"
    log "INFO 磁盘使用率: ${disk_usage}%"
    if [ "$disk_usage" -gt 85 ]; then
        send_alert "磁盘使用率过高: ${disk_usage}%"
    fi
}

check_database() {
    if ! command -v docker >/dev/null 2>&1; then
        log "SKIP 未检测到 docker，跳过数据库容器检查"
        return 0
    fi

    log "检查数据库..."

    if docker exec "$DB_CONTAINER" pg_isready -U lh_admin -d lh_contract_db >/dev/null 2>&1; then
        log "PASS 数据库连接正常"
        local connections
        connections="$(docker exec "$DB_CONTAINER" psql -U lh_admin -d lh_contract_db -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tr -d ' ' || echo unknown)"
        log "INFO 当前连接数: ${connections}"
        return 0
    fi

    log "FAIL 数据库连接失败"
    send_alert "数据库连接失败"
    return 1
}

main() {
    local exit_code=0

    log "========================================="
    log "开始健康监控"
    log "APP_URL=${APP_URL} API_BASE_URL=${API_BASE_URL}"
    log "========================================="

    check_application || exit_code=1
    check_detailed_health || exit_code=1
    check_dictionary_compatibility || exit_code=1
    check_authenticated_smoke || exit_code=1
    check_containers || exit_code=1
    check_system_resources || exit_code=1
    check_database || exit_code=1

    log "========================================="
    if [ "$exit_code" -eq 0 ]; then
        log "监控完成: 全部通过"
    else
        log "监控完成: 存在失败项"
    fi
    log "========================================="
    log ""

    exit "$exit_code"
}

main "$@"
