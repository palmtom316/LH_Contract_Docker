#!/bin/bash
# V1.4.1 安全升级脚本
# 包含：代码更新、Docker镜像重建、数据库迁移、缓存清理

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

# 1. 检查执行环境
log "1. 检查环境..."
if [ ! -f "docker-compose.prod.yml" ]; then
    error "未找到 docker-compose.prod.yml，请在项目根目录执行此脚本"
fi

# 2. 拉取最新代码
log "2. 拉取最新代码 (release/V1.4.1)..."
git fetch --all
# 强制覆盖本地修改（确保配置干净）
git reset --hard origin/release/V1.4.1
git checkout release/V1.4.1
git pull origin release/V1.4.1 || error "代码拉取失败"

# 3. 赋予脚本执行权限
chmod +x migrate_v14.sh

# 4. 执行数据库迁移
log "3. 执行数据库迁移..."
./migrate_v14.sh || error "数据库迁移失败"

# 5. 重建容器（关键：强制不使用缓存以确保 .dockerignore 生效）
log "4. 重建 Docker 容器 (No Cache)..."
log "这将花费几分钟时间..."
docker compose -f docker-compose.prod.yml build --no-cache frontend || error "前端构建失败"
docker compose -f docker-compose.prod.yml build backend || error "后端构建失败"

# 6. 重启服务
log "5. 重启服务..."
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --force-recreate

# 7. 等待服务启动
log "6. 等待服务启动 (30秒)..."
sleep 30

# 8. 验证
log "7. 验证部署..."
# 检查后端版本
VERSION=$(curl -s http://localhost/api/v1/ | grep -o 'version":"[^"]*' | cut -d'"' -f3)
if [[ "$VERSION" == "1.4.1" ]]; then
    log "✅ 版本验证成功: $VERSION"
else
    warn "⚠️ 版本验证返回: $VERSION (预期 1.4.1)"
fi

# 检查 Nginx 代理
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
if [[ "$HTTP_STATUS" == "200" ]]; then
    log "✅ 前端访问正常 (HTTP 200)"
else
    error "❌ 前端访问异常 (HTTP $HTTP_STATUS)"
fi

log "\n🎉 V1.4.1 升级成功完成！"
log "请在浏览器中使用无痕模式访问 http://192.168.72.101"
