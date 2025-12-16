#!/bin/bash

# ============================================
# 蓝海合同管理系统 - 健康监控脚本
# 版本: 1.0
# 用途: 监控系统健康状态并发送告警
# ============================================

set -e

# 配置
APP_URL="http://localhost"
LOG_FILE="/var/log/lh_contract_monitor.log"
ALERT_EMAIL="admin@example.com"
ALERT_THRESHOLD=3  # 连续失败次数阈值

# 临时文件
FAILURE_COUNT_FILE="/tmp/lh_contract_failures"

# 初始化失败计数
if [ ! -f $FAILURE_COUNT_FILE ]; then
    echo "0" > $FAILURE_COUNT_FILE
fi

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# 发送告警 (邮件)
send_alert() {
    local message="$1"
    log "❌ ALERT: $message"
    
    # 发送邮件 (需要配置mailutils)
    # echo "$message" | mail -s "LH Contract System Alert" $ALERT_EMAIL
    
    # 或使用webhook (Slack, 钉钉等)
    # curl -X POST -H 'Content-type: application/json' \
    #   --data "{\"text\":\"$message\"}" \
    #   https://hooks.slack.com/services/YOUR/WEBHOOK/URL
}

# 增加失败计数
increment_failure() {
    local count=$(cat $FAILURE_COUNT_FILE)
    count=$((count + 1))
    echo $count > $FAILURE_COUNT_FILE
    echo $count
}

# 重置失败计数
reset_failure() {
    echo "0" > $FAILURE_COUNT_FILE
}

# ============================================
# 1. 应用健康检查
# ============================================
check_application() {
    log "检查应用健康状态..."
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" $APP_URL/health)
    
    if [ "$response" = "200" ]; then
        log "✓ 应用健康检查通过 (HTTP $response)"
        reset_failure
        return 0
    else
        log "✗ 应用健康检查失败 (HTTP $response)"
        local failures=$(increment_failure)
        
        if [ $failures -ge $ALERT_THRESHOLD ]; then
            send_alert "应用健康检查连续失败 $failures 次! HTTP响应码: $response"
        fi
        return 1
    fi
}

# ============================================
# 2. 详细健康检查
# ============================================
check_detailed_health() {
    log "执行详细健康检查..."
    
    local health_json=$(curl -s $APP_URL/health/detailed)
    local status=$(echo $health_json | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
    
    if [ "$status" = "healthy" ]; then
        log "✓ 详细健康检查通过"
        
        # 提取关键指标
        local db_time=$(echo $health_json | python3 -c "import sys, json; print(json.load(sys.stdin)['checks']['database'].get('response_time_ms', 0))" 2>/dev/null)
        local cache_type=$(echo $health_json | python3 -c "import sys, json; print(json.load(sys.stdin)['checks']['cache'].get('type', 'unknown'))" 2>/dev/null)
        
        log "  - 数据库响应时间: ${db_time}ms"
        log "  - 缓存类型: $cache_type"
        
        return 0
    else
        log "✗ 详细健康检查失败: 状态=$status"
        send_alert "系统状态异常: $status"
        return 1
    fi
}

# ============================================
# 3. 容器状态检查
# ============================================
check_containers() {
    log "检查Docker容器状态..."
    
    local containers=("lh_contract_db_prod" "lh_contract_redis_prod" "lh_contract_backend_prod")
    local all_healthy=true
    
    for container in "${containers[@]}"; do
        if docker ps | grep -q $container; then
            local status=$(docker inspect --format='{{.State.Health.Status}}' $container 2>/dev/null || echo "no health check")
            
            if [ "$status" = "healthy" ] || [ "$status" = "no health check" ]; then
                log "✓ $container: 运行中"
            else
                log "✗ $container: 状态异常 ($status)"
                send_alert "容器 $container 状态异常: $status"
                all_healthy=false
            fi
        else
            log "✗ $container: 未运行"
            send_alert "容器 $container 未运行"
            all_healthy=false
        fi
    done
    
    if $all_healthy; then
        return 0
    else
        return 1
    fi
}

# ============================================
# 4. 系统资源检查
# ============================================
check_system_resources() {
    log "检查系统资源..."
    
    # CPU使用率
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    log "  - CPU使用率: ${cpu_usage}%"
    
    # 内存使用率
    local mem_usage=$(free | grep Mem | awk '{print ($3/$2) * 100.0}')
    log "  - 内存使用率: $(printf "%.1f" $mem_usage)%"
    
    # 磁盘使用率
    local disk_usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    log "  - 磁盘使用率: ${disk_usage}%"
    
    # 告警阈值
    if (( $(echo "$cpu_usage > 90" | bc -l) )); then
        send_alert "CPU使用率过高: ${cpu_usage}%"
    fi
    
    if (( $(echo "$mem_usage > 90" | bc -l) )); then
        send_alert "内存使用率过高: $(printf "%.1f" $mem_usage)%"
    fi
    
    if [ $disk_usage -gt 85 ]; then
        send_alert "磁盘使用率过高: ${disk_usage}%"
    fi
}

# ============================================
# 5. 数据库检查
# ============================================
check_database() {
    log "检查数据库..."
    
    if docker exec lh_contract_db_prod pg_isready -U lh_admin -d lh_contract_db > /dev/null 2>&1; then
        log "✓ 数据库连接正常"
        
        # 检查连接数
        local connections=$(docker exec lh_contract_db_prod psql -U lh_admin -d lh_contract_db -t -c "SELECT count(*) FROM pg_stat_activity;" | tr -d ' ')
        log "  - 当前连接数: $connections"
        
        return 0
    else
        log "✗ 数据库连接失败"
        send_alert "数据库连接失败"
        return 1
    fi
}

# ============================================
# 主监控流程
# ============================================
log "========================================="
log "开始健康监控"
log "========================================="

check_application
check_detailed_health
check_containers
check_system_resources
check_database

log "========================================="
log "监控完成"
log "========================================="
log ""

exit 0
