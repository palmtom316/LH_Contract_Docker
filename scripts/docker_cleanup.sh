#!/bin/bash
# ============================================================
# Docker 安全清理脚本
# 合同管理系统
# ============================================================
# 此脚本用于定期清理 Docker 环境中的无用数据
# 使用方法: ./docker_cleanup.sh [--aggressive]
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 显示清理前的磁盘使用情况
show_disk_usage() {
    log_info "=== Docker 磁盘使用情况 ==="
    docker system df
    echo ""
    
    log_info "=== 系统磁盘使用情况 ==="
    df -h / | head -2
    echo ""
}

# 安全清理：只清理悬空资源
safe_cleanup() {
    log_info "开始安全清理（保守模式）..."
    
    # 1. 清理已停止的容器
    log_info "清理已停止的容器..."
    stopped_containers=$(docker ps -aq --filter status=exited | wc -l)
    if [ "$stopped_containers" -gt 0 ]; then
        docker container prune -f
        log_success "已清理 ${stopped_containers} 个停止的容器"
    else
        log_info "没有需要清理的停止容器"
    fi
    
    # 2. 清理悬空镜像
    log_info "清理悬空镜像..."
    dangling_images=$(docker images -f "dangling=true" -q | wc -l)
    if [ "$dangling_images" -gt 0 ]; then
        docker image prune -f
        log_success "已清理 ${dangling_images} 个悬空镜像"
    else
        log_info "没有需要清理的悬空镜像"
    fi
    
    # 3. 清理未使用的网络
    log_info "清理未使用的网络..."
    docker network prune -f > /dev/null 2>&1 || true
    log_success "网络清理完成"
    
    # 4. 清理构建缓存
    log_info "清理构建缓存..."
    docker builder prune -f > /dev/null 2>&1 || true
    log_success "构建缓存清理完成"
    
    log_success "安全清理完成！"
}

# 深度清理：清理所有未使用资源（不包括卷）
aggressive_cleanup() {
    log_warning "开始深度清理模式..."
    log_warning "这将删除所有未被容器使用的镜像！"
    
    # 等待确认
    read -t 10 -p "确认继续？(y/N) 10秒后自动取消: " confirm || confirm="n"
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "深度清理已取消"
        return 0
    fi
    
    # 执行深度清理（不包括卷！）
    docker system prune -a -f
    
    log_success "深度清理完成！"
}

# 显示当前运行的容器
show_running_containers() {
    log_info "=== 当前运行的容器 ==="
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
    echo ""
}

# 显示卷信息（提醒用户这些不会被清理）
show_volumes() {
    log_info "=== 数据卷（不会被清理） ==="
    docker volume ls --format "table {{.Name}}\t{{.Driver}}"
    echo ""
}

# 主函数
main() {
    log_info "=============================================="
    log_info "  Docker 安全清理脚本 v1.0"
    log_info "=============================================="
    echo ""
    
    # 检查 Docker 是否运行
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker 未运行或无权限访问 Docker！"
        exit 1
    fi
    
    # 显示当前状态
    show_running_containers
    show_volumes
    show_disk_usage
    
    # 根据参数选择清理模式
    if [[ "$1" == "--aggressive" ]]; then
        safe_cleanup
        aggressive_cleanup
    else
        safe_cleanup
    fi
    
    echo ""
    log_info "=== 清理后的磁盘使用情况 ==="
    docker system df
    echo ""
    
    log_success "清理脚本执行完毕！"
}

# 执行主函数
main "$@"
