# 合同管理系统 - 服务器部署文档

## 版本信息

- **版本号**: v1.0.0-beta
- **分支**: release/v1.0.0-beta
- **发布日期**: 2024-12-14
- **状态**: 试运行版本

---

## 目录

1. [系统要求](#1-系统要求)
2. [服务器准备](#2-服务器准备)
3. [项目部署](#3-项目部署)
4. [环境配置](#4-环境配置)
5. [数据库初始化](#5-数据库初始化)
6. [启动服务](#6-启动服务)
7. [验证部署](#7-验证部署)
8. [Nginx反向代理配置](#8-nginx反向代理配置)
9. [SSL证书配置](#9-ssl证书配置)
10. [日常运维](#10-日常运维)
11. [故障排查](#11-故障排查)
12. [备份与恢复](#12-备份与恢复)

---

## 1. 系统要求

### 1.1 硬件要求

| 配置项 | 最低要求 | 推荐配置 |
|--------|----------|----------|
| CPU | 2核 | 4核及以上 |
| 内存 | 4GB | 8GB及以上 |
| 硬盘 | 40GB | 100GB SSD |
| 带宽 | 5Mbps | 10Mbps及以上 |

### 1.2 软件要求

| 软件 | 版本要求 |
|------|----------|
| 操作系统 | Ubuntu 20.04/22.04 LTS 或 CentOS 7/8 |
| Docker | 20.10+ |
| Docker Compose | 2.0+ |
| Git | 2.0+ |

---

## 2. 服务器准备

### 2.1 安装 Docker

**Ubuntu/Debian:**

```bash
# 更新包索引
sudo apt-get update

# 安装依赖
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker 并设置开机启动
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户加入 docker 组（可选，免 sudo）
sudo usermod -aG docker $USER
```

**CentOS/RHEL:**

```bash
# 安装依赖
sudo yum install -y yum-utils

# 添加 Docker 仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker
```

### 2.2 验证 Docker 安装

```bash
docker --version
docker compose version
```

### 2.3 安装 Git

```bash
# Ubuntu/Debian
sudo apt-get install -y git

# CentOS/RHEL
sudo yum install -y git
```

### 2.4 配置防火墙

```bash
# Ubuntu (ufw)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable

# CentOS (firewalld)
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

---

## 3. 项目部署

### 3.1 创建部署目录

```bash
# 创建应用目录
sudo mkdir -p /opt/lh-contract
cd /opt/lh-contract
```

### 3.2 克隆项目代码

```bash
# 克隆仓库
git clone https://github.com/palmtom316/LH_Contract_Docker.git .

# 切换到试运行分支
git checkout release/v1.0.0-beta

# 查看当前分支
git branch
```

### 3.3 目录结构说明

```
/opt/lh-contract/
├── backend/                 # 后端代码 (FastAPI)
│   ├── app/                # 应用代码
│   ├── Dockerfile          # 后端容器配置
│   ├── requirements.txt    # Python 依赖
│   └── migrations/         # 数据库迁移脚本
├── frontend/               # 前端代码 (Vue.js)
│   ├── src/               # 源代码
│   ├── Dockerfile         # 前端容器配置
│   └── nginx.conf         # Nginx 配置
├── docker-compose.yml     # Docker Compose 配置
├── .env.example           # 环境变量模板
└── uploads/               # 文件上传目录
```

---

## 4. 环境配置

### 4.1 创建环境变量文件

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

### 4.2 配置环境变量

编辑 `.env` 文件，修改以下关键配置：

```bash
# ============== 数据库配置 ==============
POSTGRES_USER=lh_admin
POSTGRES_PASSWORD=您的强密码_请修改此处
POSTGRES_DB=lh_contract_db

# ============== 应用配置 ==============
SECRET_KEY=您的JWT密钥_建议使用随机字符串_至少32位
DEBUG=false
APP_ENV=production

# ============== 后端配置 ==============
DATABASE_URL=postgresql+asyncpg://lh_admin:您的数据库密码@db:5432/lh_contract_db
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ============== 前端配置 ==============
VITE_API_BASE_URL=/api/v1
```

### 4.3 生成安全密钥

```bash
# 生成随机 SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 或使用 openssl
openssl rand -base64 32
```

### 4.4 创建上传目录

```bash
mkdir -p uploads
chmod 755 uploads
```

---

## 5. 数据库初始化

### 5.1 首次部署（全新安装）

如果是全新安装，Docker Compose 启动时会自动：
1. 创建数据库
2. 初始化表结构
3. 创建默认管理员账号

### 5.2 从旧版本升级

如果是从旧版本升级，需要运行数据库迁移：

```bash
# 启动数据库容器
docker compose up -d db

# 等待数据库启动
sleep 10

# 运行迁移脚本（更新用户角色枚举）
docker exec -i lh_contract_db psql -U lh_admin -d lh_contract_db < backend/migrations/update_user_roles.sql
```

---

## 6. 启动服务

### 6.1 构建并启动所有服务

```bash
# 构建并启动（后台运行）
docker compose up -d --build

# 查看启动状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 6.2 服务端口说明

| 服务 | 容器名称 | 内部端口 | 宿主机端口 |
|------|----------|----------|------------|
| 数据库 | lh_contract_db | 5432 | 5432 (可选关闭) |
| 后端 API | lh_contract_backend | 8000 | 8000 |
| 前端 | lh_contract_frontend | 80 | 3000 |

### 6.3 单独管理服务

```bash
# 重启后端
docker compose restart backend

# 重启前端
docker compose restart frontend

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend

# 停止所有服务
docker compose down

# 停止并删除数据卷（慎用！会删除数据库数据）
docker compose down -v
```

---

## 7. 验证部署

### 7.1 检查服务状态

```bash
# 检查所有容器运行状态
docker compose ps

# 预期输出：
# NAME                    STATUS      PORTS
# lh_contract_db          running     0.0.0.0:5432->5432/tcp
# lh_contract_backend     running     0.0.0.0:8000->8000/tcp  
# lh_contract_frontend    running     0.0.0.0:3000->80/tcp
```

### 7.2 检查后端 API

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 预期输出：{"status":"healthy",...}

# 测试登录
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### 7.3 检查前端页面

```bash
# 使用浏览器访问
http://服务器IP:3000

# 或使用 curl 检查
curl -I http://localhost:3000
```

### 7.4 默认管理员账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |

> ⚠️ **重要提示**: 首次登录后请立即修改默认密码！

---

## 8. Nginx反向代理配置

### 8.1 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt-get install -y nginx

# CentOS/RHEL
sudo yum install -y nginx
```

### 8.2 配置反向代理

创建配置文件 `/etc/nginx/sites-available/lh-contract`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为您的域名
    
    # 文件上传大小限制
    client_max_body_size 100M;
    
    # 前端静态文件
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 上传文件访问
    location /uploads/ {
        proxy_pass http://127.0.0.1:8000/uploads/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 8.3 启用配置

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/lh-contract /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## 9. SSL证书配置

### 9.1 使用 Let's Encrypt 免费证书

```bash
# 安装 Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

### 9.2 手动 SSL 配置

修改 Nginx 配置：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    # ... 其他配置同上
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 10. 日常运维

### 10.1 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看最近100行后端日志
docker compose logs --tail=100 backend

# 查看前端日志
docker compose logs --tail=100 frontend

# 查看数据库日志
docker compose logs --tail=100 db
```

### 10.2 更新部署

```bash
# 进入项目目录
cd /opt/lh-contract

# 拉取最新代码
git pull origin release/v1.0.0-beta

# 重新构建并启动
docker compose up -d --build

# 查看更新后的状态
docker compose ps
```

### 10.3 服务管理

```bash
# 重启所有服务
docker compose restart

# 停止服务（不删除容器）
docker compose stop

# 启动已停止的服务
docker compose start

# 完全停止并删除容器
docker compose down

# 查看资源使用
docker stats
```

### 10.4 清理磁盘空间

```bash
# 清理未使用的镜像
docker image prune -a

# 清理构建缓存
docker builder prune

# 清理未使用的卷（慎用）
docker volume prune
```

---

## 11. 故障排查

### 11.1 服务无法启动

```bash
# 查看详细日志
docker compose logs backend
docker compose logs frontend
docker compose logs db

# 检查端口占用
sudo netstat -tlnp | grep -E '3000|8000|5432'

# 检查容器状态
docker compose ps -a
```

### 11.2 数据库连接失败

```bash
# 检查数据库容器
docker compose logs db

# 手动连接测试
docker exec -it lh_contract_db psql -U lh_admin -d lh_contract_db

# 检查数据库是否就绪
docker exec lh_contract_db pg_isready -U lh_admin
```

### 11.3 前端页面无法访问

```bash
# 检查前端容器
docker compose logs frontend

# 检查 Nginx 配置
docker exec lh_contract_frontend nginx -t

# 重启前端
docker compose restart frontend
```

### 11.4 API 返回 500 错误

```bash
# 查看后端详细日志
docker compose logs -f backend

# 进入后端容器调试
docker exec -it lh_contract_backend /bin/sh

# 检查 Python 依赖
docker exec lh_contract_backend pip list
```

### 11.5 常见错误及解决方案

| 错误信息 | 可能原因 | 解决方案 |
|----------|----------|----------|
| `port already in use` | 端口被占用 | 修改 docker-compose.yml 中的端口映射 |
| `database connection refused` | 数据库未启动 | `docker compose up -d db` 等待启动 |
| `permission denied` | 权限问题 | `sudo chmod -R 755 uploads` |
| `out of memory` | 内存不足 | 增加服务器内存或调整容器资源限制 |

---

## 12. 备份与恢复

### 12.1 数据库备份

```bash
# 创建备份目录
mkdir -p /opt/lh-contract/backups

# 备份数据库
docker exec lh_contract_db pg_dump -U lh_admin -d lh_contract_db > /opt/lh-contract/backups/db_backup_$(date +%Y%m%d_%H%M%S).sql

# 压缩备份
gzip /opt/lh-contract/backups/db_backup_*.sql
```

### 12.2 自动备份脚本

创建 `/opt/lh-contract/scripts/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/opt/lh-contract/backups"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=7

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
docker exec lh_contract_db pg_dump -U lh_admin -d lh_contract_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 备份上传文件
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz -C /opt/lh-contract uploads/

# 删除旧备份
find $BACKUP_DIR -type f -mtime +$KEEP_DAYS -delete

echo "Backup completed: $DATE"
```

设置定时任务：

```bash
# 编辑 crontab
crontab -e

# 添加每日凌晨2点执行备份
0 2 * * * /bin/bash /opt/lh-contract/scripts/backup.sh >> /var/log/lh-contract-backup.log 2>&1
```

### 12.3 数据库恢复

```bash
# 解压备份文件
gunzip db_backup_20241214.sql.gz

# 恢复数据库
docker exec -i lh_contract_db psql -U lh_admin -d lh_contract_db < db_backup_20241214.sql
```

### 12.4 完整恢复流程

```bash
# 1. 停止服务
docker compose down

# 2. 恢复数据库
docker compose up -d db
sleep 10
docker exec -i lh_contract_db psql -U lh_admin -d lh_contract_db < backup.sql

# 3. 恢复上传文件
tar -xzf uploads_backup.tar.gz -C /opt/lh-contract/

# 4. 启动所有服务
docker compose up -d
```

---

## 附录

### A. 默认账号信息

| 用户名 | 初始密码 | 角色 | 权限说明 |
|--------|----------|------|----------|
| admin | admin123 | 管理员 | 系统全部权限 |

### B. 系统用户角色说明

| 角色 | 说明 |
|------|------|
| 管理员 | 系统全部权限 |
| 公司领导 | 查看报表、下载报表 |
| 合同管理 | 合同CRUD、财务CRUD、查看报表 |
| 财务部 | 财务记录CRUD、费用CRUD、查看报表 |
| 工程部 | 查看合同、应收应付CRUD、费用CRUD |
| 审计部 | 查看合同、结算记录CRUD |
| 投标部 | 仅查看上游合同基本信息 |
| 综合部 | 费用CRUD、管理合同财务CRUD |

### C. 技术支持

如遇到问题，请联系技术支持或查看项目 GitHub Issues。

---

**文档版本**: 1.0  
**最后更新**: 2024-12-14  
**适用版本**: v1.0.0-beta
