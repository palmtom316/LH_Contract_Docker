# 合同管理系统 - 生产环境部署指南

**版本**: 1.9.1
**更新日期**: 2026-07-16
**适用环境**: Ubuntu 20.04/22.04 LTS, Debian 11+, CentOS 7/8

本文默认部署路径为 `docker-compose.prod.yml` + `.env.production`。该路径由容器内 Nginx 对外暴露 80/443，后端、PostgreSQL、Redis、MinIO 均保持 Docker 网络内访问。

`docker-compose.production.yml` 是 HTTPS 加固预设，当前要求提前准备 `nginx/ssl/fullchain.pem` 与 `nginx/ssl/privkey.pem`，并复核 backend 环境变量透传；首次部署不要直接照 quick start 使用它。

---

## 📋 目录

1. [系统要求](#1-系统要求)
2. [部署前准备](#2-部署前准备)
3. [快速部署](#3-快速部署)
4. [详细配置](#4-详细配置)
5. [管理员初始化](#5-管理员初始化)
6. [Nginx 反向代理](#6-nginx-反向代理)
7. [SSL 证书配置](#7-ssl-证书配置)
8. [监控与日志](#8-监控与日志)
9. [备份策略](#9-备份策略)
10. [升级指南](#10-升级指南)
11. [故障排查](#11-故障排查)

---

## 1. 系统要求

### 1.1 硬件配置

| 配置项 | 最低要求 | 推荐配置 | 高负载环境 |
|--------|----------|----------|------------|
| CPU | 2 核 | 4 核 | 8 核+ |
| 内存 | 4 GB | 8 GB | 16 GB+ |
| 硬盘 | 40 GB | 100 GB SSD | 500 GB SSD |
| 带宽 | 5 Mbps | 10 Mbps | 100 Mbps+ |

### 1.2 软件要求

- **操作系统**: Ubuntu 20.04/22.04 LTS (推荐), Debian 11+, CentOS 7/8
- **Docker**: 20.10+ 或更高版本
- **Docker Compose**: 2.0+ 或更高版本
- **Git**: 2.0+

### 1.3 网络要求

- 服务器需要能够访问外网（拉取 Docker 镜像）
- 开放端口：80 (HTTP), 443 (HTTPS)
- 内部端口（不对外）：5432 (PostgreSQL), 6379 (Redis), 9000 (MinIO)

---

## 2. 部署前准备

### 2.1 安装 Docker

**Ubuntu/Debian**:
```bash
# 卸载旧版本
sudo apt-get remove docker docker-engine docker.io containerd runc

# 更新包索引
sudo apt-get update

# 安装依赖
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker compose version
```

**CentOS/RHEL**:
```bash
# 卸载旧版本
sudo yum remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine

# 安装依赖
sudo yum install -y yum-utils

# 添加 Docker 仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker Engine
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker
```

### 2.2 配置 Docker（可选优化）

```bash
# 创建 Docker 配置目录
sudo mkdir -p /etc/docker

# 配置 Docker daemon
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF

# 重启 Docker
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### 2.3 创建部署用户（推荐）

```bash
# 创建专用用户
sudo useradd -m -s /bin/bash lhcontract

# 将用户加入 docker 组
sudo usermod -aG docker lhcontract

# 切换到部署用户
sudo su - lhcontract
```

---

## 3. 快速部署

### 3.1 克隆项目

```bash
# 克隆仓库
git clone https://github.com/palmtom316/LH_Contract_Docker.git
cd LH_Contract_Docker

# 切换到稳定分支
git checkout release/1.8  # 或使用已发布的稳定分支/提交
```

只有在发布流程创建了对应 tag 后，才使用 `git checkout tags/v1.9.1`。

### 3.2 配置环境变量

```bash
# 复制生产环境变量模板
cp .env.production.example .env.production

# 编辑配置文件
nano .env.production  # 或使用 vim
```

**关键配置项**（必须修改）：

```bash
# 应用配置
APP_VERSION=1.9.1
DEBUG=false

# 数据库配置（修改密码！）
POSTGRES_USER=lh_admin
POSTGRES_PASSWORD=<生成强密码>
POSTGRES_DB=lh_contract_db
DATABASE_URL=postgresql+asyncpg://lh_admin:<密码>@db:5432/lh_contract_db

# 安全密钥（必须生成新的！）
SECRET_KEY=<使用下方命令生成>
INIT_ADMIN_TOKEN=<使用下方命令生成>

# MinIO 对象存储（修改密码！）
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=<至少8字符强密码>
MINIO_ENDPOINT=minio:9000
MINIO_BUCKET_CONTRACTS=contracts-active

# CORS（修改为实际域名！）
CORS_ORIGINS=https://your-domain.com,http://your-domain.com

# Redis
REDIS_URL=redis://redis:6379/0

# 其他
ENABLE_API_DOCS=false
TRUSTED_PROXIES=  # 如使用代理，填写代理 IP
```

**生成安全密钥**：
```bash
# 在服务器上运行
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 3.3 启动服务

```bash
# 使用生产环境配置启动
docker compose --env-file .env.production -f docker-compose.prod.yml up -d

# 查看启动日志
docker compose -f docker-compose.prod.yml logs -f

# 等待所有服务就绪（约 30-60 秒）
```

### 3.4 验证部署

```bash
# 检查容器状态
docker compose -f docker-compose.prod.yml ps

# 检查健康状态
curl http://localhost/health/ready

# 预期输出：
# {"status":"healthy", ...}
```

---

## 4. 详细配置

### 4.1 环境变量完整说明

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `APP_NAME` | 应用名称 | LH Contract Management System | 否 |
| `APP_VERSION` | 版本号 | 1.9.1 | 否 |
| `DEBUG` | 调试模式 | false | 否 |
| `SECRET_KEY` | 应用签名密钥（至少 64 字节） | - | **是** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 访问令牌过期时间 | 480（生产模板） | 否 |
| `POSTGRES_USER` | 数据库用户名 | lh_admin | 否 |
| `POSTGRES_PASSWORD` | 数据库密码 | - | **是** |
| `POSTGRES_DB` | 数据库名称 | lh_contract_db | 否 |
| `DATABASE_URL` | 数据库连接字符串 | - | **是** |
| `REDIS_URL` | Redis 连接字符串 | redis://redis:6379/0 | 否 |
| `MINIO_ROOT_USER` | MinIO 管理员用户名 | - | **是** |
| `MINIO_ROOT_PASSWORD` | MinIO 管理员密码（至少 8 字符） | - | **是** |
| `MINIO_ENDPOINT` | MinIO 内部端点 | minio:9000 | 否 |
| `MINIO_BUCKET_CONTRACTS` | 合同文件存储桶 | contracts-active | 否 |
| `CORS_ORIGINS` | 允许的跨域源（逗号分隔） | - | **是** |
| `INIT_ADMIN_TOKEN` | 管理员初始化令牌 | - | **是**（首次） |
| `ENABLE_API_DOCS` | 是否启用 API 文档 | false | 否 |
| `TRUSTED_PROXIES` | 可信代理列表（逗号分隔） | - | 否 |
| `MAX_FILE_SIZE` | 最大上传文件大小（字节） | 52428800 (50MB) | 否 |

### 4.2 Docker Compose 配置选择

项目提供多个 Docker Compose 配置文件：

| 文件名 | 用途 | 适用场景 |
|--------|------|----------|
| `docker-compose.yml` | 开发环境 | 本地开发、调试 |
| `docker-compose.prod.yml` | **默认生产环境（推荐）** | 标准生产部署，读取 `.env.production` |
| `docker-compose.prod.balanced.yml` | 平衡配置 | 4-8GB 内存服务器 |
| `docker-compose.prod.lowmem.yml` | 低内存配置 | 2-4GB 内存服务器 |
| `docker-compose.production.yml` | HTTPS 加固预设 | 已准备证书且复核环境变量透传的部署 |
| `docker-compose.pve-prod.yml` | PVE 专用配置 | PVE/宿主挂载目录部署 |

**推荐使用**: `docker-compose.prod.yml`。它通过 `env_file: .env.production` 将初始化令牌、token 过期时间、API 文档开关等配置传给 backend。

### 4.3 资源限制配置

编辑所选 compose 文件调整资源限制：

```yaml
services:
  db:
    deploy:
      resources:
        limits:
          memory: 1G        # 最大内存
        reservations:
          memory: 256M      # 预留内存

  backend:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 128M
```

---

## 5. 管理员初始化

系统不会自动创建默认管理员账户，需要手动初始化。

### 5.1 初始化步骤

```bash
# 确保服务已启动
docker compose -f docker-compose.prod.yml ps

# 初始化管理员
curl -X POST http://localhost/api/v1/auth/init-admin \
  -H 'Content-Type: application/json' \
  -H 'X-Init-Admin-Token: <你的 INIT_ADMIN_TOKEN>' \
  -d '{
    "username": "admin",
    "password": "YourStrongPassword123!",
    "email": "admin@example.com",
    "full_name": "系统管理员"
  }'
```

**成功响应**：
```json
{
  "username": "admin",
  "message": "管理员账户创建成功",
  "note": "请妥善保管初始化凭据"
}
```

### 5.2 安全建议

1. **初始化后立即删除令牌**：
   ```bash
   # 编辑 .env.production，删除或注释掉 INIT_ADMIN_TOKEN
   sed -i 's/^INIT_ADMIN_TOKEN/#INIT_ADMIN_TOKEN/' .env.production

   # 重启后端服务
   docker compose -f docker-compose.prod.yml restart backend
   ```

2. **修改管理员密码**：登录系统后，在个人中心修改初始密码。

3. **限制管理员数量**：仅为必要人员创建管理员账户。

---

## 6. Nginx 反向代理

### 6.1 默认拓扑：容器内 Nginx

默认生产部署不需要在宿主机额外安装 Nginx。`docker-compose.prod.yml` 会启动 `nginx` 服务并占用宿主机 `80/443`，再通过 Docker 网络代理到 `frontend:80` 与 `backend:8000`。

默认公开入口：

- Web UI: `http://<server-ip>/`
- API: `http://<server-ip>/api/v1/...`
- Health: `http://<server-ip>/health/ready`

内部服务不对宿主机暴露：`backend:8000`、`db:5432`、`redis:6379`、`minio:9000`。

### 6.2 可选拓扑：宿主机 Nginx

只有在需要由宿主机统一终止 TLS、接入已有网关或负载均衡时，才使用宿主机 Nginx。此时必须先调整 compose，避免容器内 Nginx 与宿主机同时占用 `80/443`。

建议做法：

```bash
# 1. 修改 docker-compose.prod.yml：移除 nginx 服务的 ports，改为 expose: ["80"]
# 2. 宿主机 Nginx 监听 80/443
# 3. 宿主机 Nginx 代理到容器网关所在地址
```

不要把宿主机 Nginx 配置为代理 `localhost:8000` 或 `localhost:9000`，默认生产 compose 没有发布这些端口。

### 6.3 HTTPS 加固预设

`docker-compose.production.yml` 直接把 `nginx/nginx.conf` 挂载到 frontend 容器，并发布 `80/443`。启用它前必须满足：

- 已存在 `nginx/ssl/fullchain.pem`
- 已存在 `nginx/ssl/privkey.pem`
- 已把 `nginx/nginx.conf` 中的 `server_name` 改成真实域名
- 已复核 backend 所需环境变量是否都在 compose 中透传

---

## 7. SSL 证书配置

### 7.1 默认部署启用 HTTPS

默认 `docker-compose.prod.yml` 使用 `nginx/prod.conf`，当前只提供 HTTP。要启用 HTTPS，有两种方式：

1. 使用宿主机或上游网关终止 TLS，再反代到容器 Nginx。
2. 基于 `docker-compose.production.yml` 的 HTTPS 加固预设部署，并按上一节准备证书。

### 7.2 使用 Let's Encrypt 申请证书

```bash
# 安装 Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 测试自动续期
sudo certbot renew --dry-run
```

### 7.3 自动续期

Certbot 会自动配置 cron 任务，也可以手动配置：

```bash
# 编辑 crontab
sudo crontab -e

# 添加以下行（每天凌晨 2 点检查续期）
0 2 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## 8. 监控与日志

### 8.1 查看容器日志

```bash
# 查看所有容器日志
docker compose -f docker-compose.prod.yml logs

# 实时跟踪日志
docker compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs frontend
docker compose -f docker-compose.prod.yml logs db

# 查看最近 100 行
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

### 8.2 日志轮转

生产环境配置已包含日志轮转（每个文件最大 10MB，保留 3 个文件）。

### 8.3 健康检查

```bash
# API 健康检查
curl http://localhost/health/ready

# 详细健康检查（包含数据库、Redis、MinIO）
curl http://localhost/health/detailed

# 预期输出：
# {
#   "status": "healthy",
#   "checks": { ... }
# }
```

### 8.4 性能监控

可选集成 Prometheus + Grafana：

```bash
# 暂不包含在默认部署中，需要自行配置
# 参考：https://prometheus.io/docs/introduction/overview/
```

---

## 9. 备份策略

### 9.1 数据库备份

**自动备份脚本**：

创建 `/opt/lh-contract/backup-db.sh`：

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/lh-contract"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/opt/lh-contract/LH_Contract_Docker"
CONTAINER_NAME="lh_contract_db_prod"

mkdir -p $BACKUP_DIR
set -a
. "$PROJECT_DIR/.env.production"
set +a

# 备份数据库
docker exec $CONTAINER_NAME pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# 保留最近 7 天的备份
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

**配置定时任务**：

```bash
# 编辑 crontab
sudo crontab -e

# 添加每日凌晨 3 点备份
0 3 * * * /opt/lh-contract/backup-db.sh >> /var/log/lh-contract-backup.log 2>&1
```

### 9.2 MinIO 数据备份

```bash
# 备份 MinIO 数据卷
docker run --rm -v lh_contract_docker_minio_data:/data \
  -v /var/backups/lh-contract:/backup \
  alpine tar czf /backup/minio_backup_$(date +%Y%m%d).tar.gz -C /data .
```

### 9.3 配置文件备份

```bash
# 备份 .env.production 和配置文件（注意安全性！）
tar czf /var/backups/lh-contract/config_backup_$(date +%Y%m%d).tar.gz \
  /path/to/LH_Contract_Docker/.env.production \
  /path/to/LH_Contract_Docker/docker-compose.prod.yml
```

### 9.4 恢复数据

**恢复数据库**：

```bash
# 解压备份
gunzip db_backup_20260624_030000.sql.gz

# 恢复到数据库
docker exec -i lh_contract_db_prod psql -U lh_admin lh_contract_db < db_backup_20260624_030000.sql
```

**恢复 MinIO 数据**：

```bash
# 停止 MinIO
docker compose -f docker-compose.prod.yml stop minio

# 恢复数据
docker run --rm -v lh_contract_docker_minio_data:/data \
  -v /var/backups/lh-contract:/backup \
  alpine sh -c "cd /data && tar xzf /backup/minio_backup_20260624.tar.gz"

# 启动 MinIO
docker compose -f docker-compose.prod.yml start minio
```

---

## 10. 升级指南

### 10.1 升级前准备

```bash
# 1. 备份数据
/opt/lh-contract/backup-db.sh

# 2. 备份当前版本配置
cp .env.production .env.production.backup
cp docker-compose.prod.yml docker-compose.prod.yml.backup

# 3. 查看当前版本
docker compose -f docker-compose.prod.yml exec backend python -c "from app.config import settings; print(settings.APP_VERSION)"
```

### 10.2 执行升级

```bash
# 1. 拉取最新代码
cd /path/to/LH_Contract_Docker
git fetch --all --tags

# 2. 查看可用分支和 tag
git branch -a
git tag -l

# 3. 切换到目标版本
git checkout release/1.8

# 4. 对比环境变量变化
diff .env.production.example .env.production

# 5. 停止服务
docker compose -f docker-compose.prod.yml down

# 6. 拉取新镜像（如果使用预构建镜像）
docker compose -f docker-compose.prod.yml pull

# 7. 启动服务
docker compose --env-file .env.production -f docker-compose.prod.yml up -d

# 8. 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 9. 验证升级
curl http://localhost/health/ready
```

### 10.3 数据库迁移

如果版本包含数据库迁移：

```bash
# 进入后端容器
docker compose -f docker-compose.prod.yml exec backend bash

# 运行迁移
alembic upgrade head

# 退出容器
exit
```

### 10.4 回滚

如果升级失败，回滚到之前版本：

```bash
# 停止服务
docker compose -f docker-compose.prod.yml down

# 切换回旧版本对应的分支、tag 或提交
git checkout <previous-ref>

# 恢复配置
cp .env.production.backup .env.production

# 启动服务
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

---

## 11. 故障排查

### 11.1 容器无法启动

**检查日志**：
```bash
docker compose -f docker-compose.prod.yml logs backend
```

**常见问题**：
- 端口被占用：`sudo ss -ltnp | grep -E ':80|:443'`
- 环境变量配置错误：检查 `.env.production` 文件
- 数据库连接失败：确认 `DATABASE_URL` 配置正确

### 11.2 数据库连接失败

```bash
# 检查数据库容器状态
docker compose -f docker-compose.prod.yml ps db

# 检查数据库日志
docker compose -f docker-compose.prod.yml logs db

# 手动测试连接
docker compose -f docker-compose.prod.yml exec db psql -U lh_admin -d lh_contract_db
```

### 11.3 前端无法访问

```bash
# 检查前端容器
docker compose -f docker-compose.prod.yml ps frontend

# 检查 Nginx 日志
docker compose -f docker-compose.prod.yml logs nginx

# 检查 CORS 配置
grep CORS_ORIGINS .env.production
```

### 11.4 MinIO 存储问题

```bash
# 检查 MinIO 状态
docker compose -f docker-compose.prod.yml ps minio

# 默认生产配置不暴露 MinIO 控制台

# 检查存储桶
docker compose -f docker-compose.prod.yml exec minio mc ls local/
```

### 11.5 性能问题

```bash
# 检查容器资源使用
docker stats

# 检查数据库查询性能
docker compose -f docker-compose.prod.yml exec db psql -U lh_admin -d lh_contract_db -c "SELECT * FROM pg_stat_activity;"

# 检查 Redis 状态
docker compose -f docker-compose.prod.yml exec redis redis-cli INFO
```

### 11.6 获取支持

如遇到无法解决的问题：

1. 收集日志：
   ```bash
   docker compose -f docker-compose.prod.yml logs > logs_$(date +%Y%m%d).txt
   ```

2. 检查系统状态：
   ```bash
   docker compose -f docker-compose.prod.yml ps > status.txt
   ```

3. 联系内部运维渠道。

---

## 附录

### A. 防火墙配置

**UFW (Ubuntu)**:
```bash
# 允许 SSH
sudo ufw allow 22/tcp

# 允许 HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable
```

### B. 系统优化

```bash
# 增加文件描述符限制
sudo tee -a /etc/security/limits.conf > /dev/null <<EOF
* soft nofile 65536
* hard nofile 65536
EOF

# 优化网络参数
sudo tee -a /etc/sysctl.conf > /dev/null <<EOF
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
EOF

sudo sysctl -p
```

### C. 常用命令速查

```bash
# 启动服务
docker compose --env-file .env.production -f docker-compose.prod.yml up -d

# 停止服务
docker compose -f docker-compose.prod.yml down

# 重启服务
docker compose -f docker-compose.prod.yml restart

# 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 进入容器
docker compose -f docker-compose.prod.yml exec backend bash

# 更新镜像
docker compose -f docker-compose.prod.yml pull
docker compose --env-file .env.production -f docker-compose.prod.yml up -d

# 清理未使用的镜像
docker system prune -a
```

---

**文档版本**: 1.9.1
**最后更新**: 2026-07-16
**维护者**: 技术团队
