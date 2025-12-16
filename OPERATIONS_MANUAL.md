# 运维手册

**系统**: 蓝海合同管理系统  
**版本**: 1.0.0  
**更新日期**: 2025-12-16

---

## 📋 目录

1. [系统架构](#系统架构)
2. [部署指南](#部署指南)
3. [日常运维](#日常运维)
4. [监控告警](#监控告警)
5. [备份恢复](#备份恢复)
6. [故障排查](#故障排查)
7. [性能优化](#性能优化)
8. [安全管理](#安全管理)

---

## 系统架构

### 技术栈

**后端**:
- FastAPI 0.104.1
- Python 3.11
- SQLAlchemy (Async)
- PostgreSQL 15

**前端**:
- Vue 3
- Vite 5
- Element Plus

**基础设施**:
- Docker & Docker Compose
- Nginx
- Redis 7

### 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80, 443 | Web服务器 |
| Backend | 8000 | FastAPI应用 |
| Frontend Dev | 5173 | 开发服务器 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |

---

## 部署指南

### 生产环境部署

#### 1. 准备工作

```bash
# 克隆代码
git clone <repository-url>
cd LH_Contract_Docker

# 创建生产环境配置
cp .env.example .env.production
```

#### 2. 配置环境变量

编辑 `.env.production`:

```bash
# 数据库配置
POSTGRES_USER=lh_admin
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=lh_contract_db

# 应用密钥 (必须修改!)
SECRET_KEY=<use: python -c "import secrets; print(secrets.token_urlsafe(64))">

# Redis配置
REDIS_URL=redis://redis:6379/0

# 应用配置
DEBUG=false
CORS_ORIGINS=https://yourdomain.com
```

#### 3. 构建和启动

```bash
# 使用生产配置启动
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 检查健康状态
curl http://localhost/health/detailed
```

#### 4. 初始化数据

```bash
# 进入后端容器
docker exec -it lh_contract_backend_prod bash

# 运行数据库迁移
alembic upgrade head

# 创建管理员账户
python -c "from app.init_data import init_data; import asyncio; asyncio.run(init_data())"
```

---

## 日常运维

### 服务管理

#### 启动服务

```bash
docker-compose -f docker-compose.prod.yml up -d
```

#### 停止服务

```bash
docker-compose -f docker-compose.prod.yml down
```

#### 重启服务

```bash
# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 重启单个服务
docker-compose -f docker-compose.prod.yml restart backend
```

#### 查看日志

```bash
# 所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend

# 最近100行
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

#### 服务状态

```bash
# 查看所有容器状态
docker-compose -f docker-compose.prod.yml ps

# 查看资源使用
docker stats
```

---

## 监控告警

### 健康检查

#### 简单健康检查

```bash
curl http://localhost/health
```

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-16T14:28:00"
}
```

#### 详细健康检查

```bash
curl http://localhost/health/detailed
```

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-16T14:28:00",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5.2,
      "connection": "ok"
    },
    "cache": {
      "status": "healthy",
      "type": "redis",
      "response_time_ms": 1.8
    },
    "disk": {
      "status": "healthy",
      "total_gb": 100,
      "free_gb": 75,
      "percent_used": 25
    }
  }
}
```

### 监控指标

#### 关键指标

1. **应用健康**:
   - HTTP 200响应率
   - 平均响应时间
   - 错误率

2. **数据库**:
   - 连接数
   - 查询响应时间
   - 慢查询数量

3. **缓存**:
   - 命中率
   - 内存使用
   - 连接数

4. **系统资源**:
   - CPU使用率
   - 内存使用率
   - 磁盘使用率
   - 网络I/O

#### 监控脚本

创建 `scripts/monitor.sh`:

```bash
#!/bin/bash

# 检查所有服务健康状态

echo "=== System Health Check ==="
echo "Time: $(date)"
echo ""

# Backend健康检查
echo "Backend Health:"
curl -s http://localhost/health/detailed | python -m json.tool
echo ""

# 数据库连接
echo "Database:"
docker exec lh_contract_db_prod pg_isready -U lh_admin
echo ""

# Redis状态
echo "Redis:"
docker exec lh_contract_redis_prod redis-cli ping
echo ""

# 磁盘空间
echo "Disk Usage:"
df -h | grep -E "Filesystem|/dev/sd"
echo ""

# 容器状态
echo "Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

## 备份恢复

### 数据库备份

#### 自动备份脚本

创建 `scripts/backup.sh`:

```bash
#!/bin/bash

# 数据库自动备份脚本

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/lh_contract_db_$DATE.sql"

echo "Starting backup at $(date)"

# 创建备份
docker exec lh_contract_db_prod pg_dump \
  -U lh_admin \
  -d lh_contract_db \
  -F c \
  -f /backups/lh_contract_db_$DATE.sql

# 压缩备份
gzip $BACKUP_FILE

echo "Backup completed: ${BACKUP_FILE}.gz"

# 删除7天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Old backups cleaned"
```

#### 设置定时备份

```bash
# 编辑crontab
crontab -e

# 添加每天凌晨2点备份
0 2 * * * /opt/lh_contract/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### 恢复数据

```bash
# 停止应用
docker-compose -f docker-compose.prod.yml stop backend

# 恢复数据库
gunzip -c /backups/lh_contract_db_20251216.sql.gz | \
  docker exec -i lh_contract_db_prod pg_restore \
  -U lh_admin \
  -d lh_contract_db \
  -c

# 重启应用
docker-compose -f docker-compose.prod.yml start backend
```

### 文件备份

```bash
# 备份上传文件
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz ./uploads

# 备份到远程服务器
rsync -avz ./uploads/ backup-server:/backups/lh_contract/uploads/
```

---

## 故障排查

### 常见问题

#### 1. 后端无法启动

**症状**: Backend容器启动后立即退出

**检查步骤**:
```bash
# 查看日志
docker-compose logs backend

# 检查配置
docker-compose config

# 检查数据库连接
docker exec lh_contract_db_prod psql -U lh_admin -d lh_contract_db -c "SELECT 1"
```

**常见原因**:
- 数据库未就绪
- SECRET_KEY未设置
- 环境变量配置错误

#### 2. 数据库连接池耗尽

**症状**: 出现 "QueuePool limit exceeded"

**解决方案**:
```python
# 调整数据库连接池大小
# backend/app/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,        # 增加
    max_overflow=40,     # 增加
    pool_timeout=30
)
```

#### 3. Redis内存不足

**症状**: Redis频繁淘汰数据

**检查**:
```bash
docker exec lh_contract_redis_prod redis-cli INFO memory
```

**解决方案**:
```bash
# 增加Redis内存限制
# docker-compose.prod.yml
command: redis-server --maxmemory 1gb
```

#### 4. 磁盘空间不足

**检查**:
```bash
df -h
du -sh /var/lib/docker/volumes/*
```

**清理**:
```bash
# 清理Docker资源
docker system prune -a

# 清理旧日志
find ./logs -name "*.log" -mtime +30 -delete
```

---

## 性能优化

### 数据库优化

#### 1. 慢查询分析

```sql
-- 开启慢查询日志
ALTER SYSTEM SET log_min_duration_statement = 1000; -- 1秒
SELECT pg_reload_conf();

-- 查看慢查询
SELECT * FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

#### 2. 连接池调优

```python
# 根据并发量调整
POOL_SIZE = CPU_CORES * 2 + 1
MAX_OVERFLOW = POOL_SIZE * 2
```

### 缓存优化

#### Redis配置

```bash
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
```

#### 缓存策略

```python
# 热点数据缓存
TTL_SHORT = 300      # 5分钟
TTL_MEDIUM = 1800    # 30分钟  
TTL_LONG = 3600      # 1小时
```

---

## 安全管理

### SSL证书

#### 使用Let's Encrypt

```bash
# 安装certbot
apt-get install certbot

# 获取证书
certbot certonly --standalone -d yourdomain.com

# 自动续期
crontab -e
0 3 * * * certbot renew --quiet
```

### 防火墙配置

```bash
# 只开放必要端口
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

### 定期更新

```bash
# 更新系统包
apt-get update && apt-get upgrade

# 更新Docker镜像
docker-compose pull
docker-compose up -d
```

---

## 维护检查清单

### 每日检查

- [ ] 查看应用健康状态
- [ ] 检查错误日志
- [ ] 验证备份完成

### 每周检查

- [ ] 审查系统资源使用
- [ ] 检查慢查询日志
- [ ] 清理旧备份和日志

### 每月检查

- [ ] 数据库性能分析
- [ ] 安全更新检查
- [ ] 容量规划评估

---

## 联系方式

**技术支持**: support@example.com  
**紧急联系**: emergency@example.com

---

**文档版本**: 1.0  
**最后更新**: 2025-12-16
