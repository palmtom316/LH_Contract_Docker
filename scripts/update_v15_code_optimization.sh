#!/bin/bash
# ============================================
# V1.5 代码优化更新脚本
# 用途：从旧版 V1.5 升级到当前 V1.5（代码优化版）
# 创建日期：2026-01-15
# 说明：本次更新无数据库迁移，仅代码/依赖更新
# ============================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}   V1.5 代码优化更新脚本${NC}"
echo -e "${BLUE}   更新内容：代码重构 + 依赖升级${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# 检查是否在正确的目录
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ 错误：未找到 docker-compose.yml${NC}"
    echo -e "${RED}   请在项目根目录执行此脚本${NC}"
    exit 1
fi

# 步骤 1：检查当前服务状态
echo -e "${YELLOW}[1/7] 检查当前服务状态...${NC}"
docker compose ps
echo ""

# 步骤 2：创建快速备份（仅数据库）
echo -e "${YELLOW}[2/7] 创建数据库备份...${NC}"
BACKUP_FILE="backup_v15_update_$(date +%Y%m%d_%H%M%S).sql"
docker compose exec -T db pg_dump -U lh_admin lh_contract_db > "$BACKUP_FILE"
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
    echo -e "${GREEN}✅ 备份完成: $BACKUP_FILE ($BACKUP_SIZE)${NC}"
else
    echo -e "${RED}❌ 备份失败${NC}"
    exit 1
fi
echo ""

# 步骤 3：拉取最新代码
echo -e "${YELLOW}[3/7] 拉取最新代码...${NC}"
git fetch origin
git pull origin release/V1.5
echo -e "${GREEN}✅ 代码更新完成${NC}"
echo ""

# 步骤 4：重建后端容器
echo -e "${YELLOW}[4/7] 重建后端容器（包含新依赖）...${NC}"
docker compose build --no-cache backend
echo -e "${GREEN}✅ 后端重建完成${NC}"
echo ""

# 步骤 5：重建前端容器
echo -e "${YELLOW}[5/7] 重建前端容器...${NC}"
docker compose build --no-cache frontend
echo -e "${GREEN}✅ 前端重建完成${NC}"
echo ""

# 步骤 6：重启所有服务
echo -e "${YELLOW}[6/7] 重启所有服务...${NC}"
docker compose up -d
echo -e "${GREEN}✅ 服务重启完成${NC}"
echo ""

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 步骤 7：验证升级
echo -e "${YELLOW}[7/7] 验证升级...${NC}"
echo ""

# 检查容器状态
echo "容器状态："
docker compose ps
echo ""

# 检查后端健康
echo "后端健康检查："
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "failed")
if [ "$HEALTH_CHECK" = "200" ]; then
    echo -e "${GREEN}✅ 后端健康检查通过 (HTTP 200)${NC}"
else
    echo -e "${YELLOW}⚠️  后端健康检查返回: $HEALTH_CHECK${NC}"
fi
echo ""

# 检查后端日志是否有错误
echo "检查后端日志（最后 10 行）："
docker compose logs backend --tail=10 2>&1 | tail -10
echo ""

# 显示更新内容摘要
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}✅ V1.5 代码优化更新完成！${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo "本次更新内容："
echo "  • reports.py 拆分为模块化结构"
echo "  • 后端依赖更新 (FastAPI, SQLAlchemy, Pydantic)"
echo "  • 前端依赖更新 (Vue, Element Plus, Pinia)"
echo "  • 缓存 TTL 支持 (cachetools)"
echo "  • 全局错误处理增强"
echo "  • ESLint no-console 规则"
echo ""
echo -e "${YELLOW}备份文件位置: $BACKUP_FILE${NC}"
echo ""
echo "请手动验证："
echo "  1. 访问系统登录页面"
echo "  2. 检查合同列表是否正常加载"
echo "  3. 测试文件上传/下载功能"
echo ""
