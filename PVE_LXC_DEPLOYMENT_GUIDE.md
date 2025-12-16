# LH合同管理系统 - PVE LXC部署指南 v1.1.0

## 服务器信息
- **服务器型号**: 铭凡 MS-A2
- **硬件配置**: 32GB内存, 2×2TB SSD, 4网口
- **目标IP**: 192.168.72.100
- **部署方式**: Proxmox VE (PVE) + LXC容器
- **应用版本**: v1.1.0

---

## 目录
1. [Proxmox VE 安装](#1-proxmox-ve-安装)
2. [PVE 基础配置](#2-pve-基础配置)
3. [创建 LXC 容器](#3-创建-lxc-容器)
4. [容器基础环境配置](#4-容器基础环境配置)
5. [安装 Docker 环境](#5-安装-docker-环境)
6. [部署合同管理系统](#6-部署合同管理系统)
7. [网络与防火墙配置](#7-网络与防火墙配置)
8. [系统优化与监控](#8-系统优化与监控)
9. [备份与恢复](#9-备份与恢复)
10. [故障排查](#10-故障排查)

---

## 1. Proxmox VE 安装

### 1.1 下载 Proxmox VE ISO
```bash
# 访问官网下载最新版本
https://www.proxmox.com/en/downloads

# 推荐版本: Proxmox VE 8.x
# 下载 ISO: proxmox-ve_8.x-x.iso
```

### 1.2 制作启动U盘
```bash
# Windows 使用 Rufus 或 Etcher
# Linux 使用 dd 命令
dd if=proxmox-ve_8.x-x.iso of=/dev/sdX bs=4M status=progress
sync
```

### 1.3 安装 Proxmox VE

**启动安装程序**:
1. 插入U盘，从U盘启动
2. 选择 "Install Proxmox VE"

**安装配置**:
```
目标磁盘: 第一块2TB SSD (用于系统和虚拟机)
文件系统: ext4 或 ZFS (推荐 ZFS RAID1 镜像)
国家: China
时区: Asia/Shanghai
键盘布局: U.S.

管理员密码: [设置强密码]
邮箱地址: admin@yourdomain.com

主机名(FQDN): pve.local
IP地址: 192.168.72.100
网关: 192.168.72.1
DNS: 192.168.72.1 (或 114.114.114.114)
```

**完成安装后重启**

### 1.4 访问 PVE Web 界面
```
打开浏览器访问: https://192.168.72.100:8006
用户名: root
密码: [安装时设置的密码]
```

---

## 2. PVE 基础配置

### 2.1 更新系统源（可选，国内加速）

SSH 登录到 PVE 主机:
```bash
ssh root@192.168.72.100
```

**备份原有源**:
```bash
cp /etc/apt/sources.list /etc/apt/sources.list.bak
cp /etc/apt/sources.list.d/pve-enterprise.list /etc/apt/sources.list.d/pve-enterprise.list.bak
```

**修改为国内源**:
```bash
# 编辑 /etc/apt/sources.list
cat > /etc/apt/sources.list << 'EOF'
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-backports main contrib non-free non-free-firmware
deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware
EOF

# 禁用企业订阅源
echo "# deb https://enterprise.proxmox.com/debian/pve bookworm pve-enterprise" > /etc/apt/sources.list.d/pve-enterprise.list

# 添加 PVE 无订阅源
cat > /etc/apt/sources.list.d/pve-no-subscription.list << 'EOF'
deb https://mirrors.tuna.tsinghua.edu.cn/proxmox/debian/pve bookworm pve-no-subscription
EOF
```

**更新系统**:
```bash
apt update
apt upgrade -y
apt dist-upgrade -y
```

### 2.2 配置存储

**查看磁盘**:
```bash
lsblk
fdisk -l
```

**配置第二块SSD作为数据存储**:
```bash
# 假设第二块磁盘为 /dev/sdb
# 创建分区
fdisk /dev/sdb
# 输入: n -> p -> 1 -> Enter -> Enter -> w

# 格式化
mkfs.ext4 /dev/sdb1

# 创建挂载点
mkdir -p /mnt/data

# 获取UUID
blkid /dev/sdb1

# 添加到 fstab 自动挂载
echo "UUID=<your-uuid> /mnt/data ext4 defaults 0 2" >> /etc/fstab

# 挂载
mount -a

# 在PVE中添加存储
pvesm add dir data --path /mnt/data --content images,rootdir,vztmpl,backup
```

### 2.3 下载 LXC 模板

```bash
# 进入模板存储目录
cd /var/lib/vz/template/cache/

# 下载 Debian 12 模板（推荐）
pveam update
pveam available | grep debian-12
pveam download local debian-12-standard_12.2-1_amd64.tar.zst

# 或下载 Ubuntu 22.04 模板
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst
```

---

## 3. 创建 LXC 容器

### 3.1 通过 Web 界面创建

1. 登录 PVE Web 界面 (https://192.168.72.100:8006)
2. 点击右上角 "创建 CT"
3. 配置如下:

**常规**:
- 节点: pve
- CT ID: 100
- 主机名: lh-contract
- 密码: [设置容器root密码]
- SSH公钥: [可选]

**模板**:
- 存储: local
- 模板: debian-12-standard_12.2-1_amd64.tar.zst

**根磁盘**:
- 存储: local-lvm (或 data)
- 磁盘大小: 50GB

**CPU**:
- 核心数: 4

**内存**:
- 内存: 8192 MB
- 交换: 2048 MB

**网络**:
- 名称: eth0
- 桥接: vmbr0
- IPv4: 静态
- IPv4/CIDR: 192.168.72.101/24
- 网关: 192.168.72.1

**DNS**:
- DNS域: local
- DNS服务器: 192.168.72.1

4. 点击 "完成" 创建容器

### 3.2 通过命令行创建（可选）

```bash
# 创建LXC容器
pct create 100 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
  --hostname lh-contract \
  --password <your-password> \
  --cores 4 \
  --memory 8192 \
  --swap 2048 \
  --rootfs local-lvm:50 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.72.101/24,gw=192.168.72.1 \
  --nameserver 192.168.72.1 \
  --features nesting=1,keyctl=1 \
  --unprivileged 1 \
  --start 1
```

### 3.3 启动容器

```bash
# 启动容器
pct start 100

# 查看容器状态
pct status 100

# 进入容器
pct enter 100
```

---

## 4. 容器基础环境配置

### 4.1 进入容器

```bash
# 从PVE主机进入容器
pct enter 100

# 或通过SSH
ssh root@192.168.72.101
```

### 4.2 更新系统

```bash
# 更新软件包列表
apt update
apt upgrade -y

# 安装基础工具
apt install -y \
  curl \
  wget \
  git \
  vim \
  htop \
  net-tools \
  ca-certificates \
  gnupg \
  lsb-release \
  sudo \
  ufw
```

### 4.3 配置时区和语言

```bash
# 设置时区
timedatectl set-timezone Asia/Shanghai

# 验证时区
date

# 配置语言（可选）
apt install -y locales
dpkg-reconfigure locales
# 选择: zh_CN.UTF-8
```

### 4.4 创建应用用户（可选，更安全）

```bash
# 创建应用用户
adduser appuser
usermod -aG sudo appuser

# 切换到应用用户
su - appuser
```

---

## 5. 安装 Docker 环境

### 5.1 安装 Docker Engine

```bash
# 卸载旧版本（如果存在）
apt remove -y docker docker-engine docker.io containerd runc

# 设置Docker官方GPG密钥
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

# 添加Docker仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# 更新软件包索引
apt update

# 安装Docker
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 启动Docker服务
systemctl start docker
systemctl enable docker

# 验证安装
docker --version
docker compose version
```

### 5.2 配置 Docker（可选优化）

```bash
# 创建Docker配置目录
mkdir -p /etc/docker

# 配置Docker镜像加速（国内）
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF

# 重启Docker
systemctl daemon-reload
systemctl restart docker

# 验证配置
docker info | grep -A 10 "Registry Mirrors"
```

### 5.3 配置 Docker 用户权限（可选）

```bash
# 将当前用户添加到docker组（如果使用appuser）
usermod -aG docker $USER
newgrp docker

# 测试无需sudo运行docker
docker ps
```

---

## 6. 部署合同管理系统

### 6.1 创建应用目录

```bash
# 创建应用根目录
mkdir -p /opt/lh-contract
cd /opt/lh-contract

# 创建数据目录
mkdir -p data/postgres data/uploads logs
```

### 6.2 克隆项目代码

```bash
# 从GitHub克隆项目
git clone -b release/v1.1 https://github.com/palmtom316/LH_Contract_Docker.git .

# 或者如果仓库是私有的，使用token
git clone https://<your-token>@github.com/palmtom316/LH_Contract_Docker.git .

# 检出v1.1.0标签
git checkout v1.1.0

# 查看项目结构
ls -la
```

### 6.3 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑环境变量
vim .env
```

**编辑 `.env` 文件**:
```env
# 应用配置
APP_ENV=production
APP_NAME=LH合同管理系统
APP_VERSION=1.1.0

# 数据库配置
POSTGRES_DB=lh_contract
POSTGRES_USER=lhuser
POSTGRES_PASSWORD=your_secure_password_here_123!
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# 应用密钥（重要：生成强密钥）
SECRET_KEY=your_very_long_random_secret_key_minimum_32_characters_here
JWT_SECRET_KEY=your_jwt_secret_key_minimum_32_characters_here

# 后端配置
BACKEND_CORS_ORIGINS=["http://192.168.72.101:3000","http://192.168.72.101"]
API_V1_PREFIX=/api/v1

# 前端配置
VITE_API_BASE_URL=http://192.168.72.101:8000
VITE_APP_TITLE=LH合同管理系统

# Redis配置（如果使用）
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# 文件上传配置
MAX_UPLOAD_SIZE=50MB
UPLOAD_DIR=/app/uploads

# 日志配置
LOG_LEVEL=INFO
```

**生成安全密钥**:
```bash
# 生成SECRET_KEY
openssl rand -hex 32

# 生成JWT_SECRET_KEY
openssl rand -hex 32

# 生成强数据库密码
openssl rand -base64 24
```

### 6.4 配置 Docker Compose

检查 `docker-compose.prod.yml` 文件，确保配置正确:

```bash
vim docker-compose.prod.yml
```

确保包含以下内容（示例）:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: lh-contract-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - lh-contract-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: lh-contract-backend
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - BACKEND_CORS_ORIGINS=${BACKEND_CORS_ORIGINS}
    volumes:
      - ./data/uploads:/app/uploads
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - lh-contract-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_BASE_URL=${VITE_API_BASE_URL}
    container_name: lh-contract-frontend
    restart: unless-stopped
    ports:
      - "3000:80"
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - lh-contract-network

networks:
  lh-contract-network:
    driver: bridge

volumes:
  postgres_data:
```

### 6.5 构建和启动服务

```bash
# 确保在项目根目录
cd /opt/lh-contract

# 构建镜像（首次部署）
docker compose -f docker-compose.prod.yml build

# 启动服务
docker compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 单独查看某个服务的日志
docker compose -f docker-compose.prod.yml logs -f backend
```

### 6.6 初始化数据库

```bash
# 进入后端容器
docker exec -it lh-contract-backend bash

# 运行数据库迁移（如果有）
python -m alembic upgrade head

# 创建初始管理员用户（如果有seed脚本）
python -m app.seed_admin

# 退出容器
exit
```

### 6.7 验证部署

```bash
# 测试后端API
curl http://192.168.72.101:8000/health
curl http://192.168.72.101:8000/api/v1/ping

# 访问前端
# 浏览器打开: http://192.168.72.101:3000

# 检查所有容器状态
docker compose -f docker-compose.prod.yml ps

# 检查容器日志
docker compose -f docker-compose.prod.yml logs --tail=100
```

---

## 7. 网络与防火墙配置

### 7.1 配置 UFW 防火墙

```bash
# 启用UFW
ufw enable

# 允许SSH（重要！）
ufw allow 22/tcp

# 允许HTTP
ufw allow 80/tcp

# 允许HTTPS
ufw allow 443/tcp

# 允许前端端口
ufw allow 3000/tcp

# 允许后端API端口
ufw allow 8000/tcp

# 仅允许内网访问数据库（可选，更安全）
ufw allow from 192.168.72.0/24 to any port 5432

# 查看防火墙状态
ufw status verbose

# 查看规则编号
ufw status numbered
```

### 7.2 配置 Nginx 反向代理（可选，推荐生产环境）

```bash
# 安装Nginx
apt install -y nginx

# 创建配置文件
vim /etc/nginx/sites-available/lh-contract
```

**Nginx 配置内容**:
```nginx
# HTTP 配置
server {
    listen 80;
    server_name 192.168.72.101;

    client_max_body_size 50M;

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # 后端API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 文件上传
    location /uploads {
        proxy_pass http://localhost:8000/uploads;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 健康检查
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

**启用配置**:
```bash
# 创建软链接
ln -s /etc/nginx/sites-available/lh-contract /etc/nginx/sites-enabled/

# 删除默认配置
rm /etc/nginx/sites-enabled/default

# 测试配置
nginx -t

# 重启Nginx
systemctl restart nginx
systemctl enable nginx

# 检查状态
systemctl status nginx
```

### 7.3 配置 HTTPS（可选，如果有域名和证书）

```bash
# 安装certbot
apt install -y certbot python3-certbot-nginx

# 获取SSL证书（需要域名）
certbot --nginx -d your-domain.com

# 自动续签测试
certbot renew --dry-run
```

---

## 8. 系统优化与监控

### 8.1 配置系统资源限制

编辑 LXC 容器配置（在PVE主机上）:
```bash
# 在PVE主机上执行
vim /etc/pve/lxc/100.conf
```

添加资源限制:
```
# CPU限制
cores: 4
cpulimit: 4

# 内存限制
memory: 8192
swap: 2048

# IO限制
rootfs: local-lvm:vm-100-disk-0,size=50G
```

### 8.2 安装监控工具

```bash
# 在容器内安装监控工具
apt install -y htop iotop nethogs

# 安装docker stats监控
# 实时查看容器资源使用
docker stats

# 或使用ctop
wget https://github.com/bcicen/ctop/releases/download/v0.7.7/ctop-0.7.7-linux-amd64 -O /usr/local/bin/ctop
chmod +x /usr/local/bin/ctop
ctop
```

### 8.3 配置日志轮转

```bash
# 创建日志轮转配置
cat > /etc/logrotate.d/lh-contract << 'EOF'
/opt/lh-contract/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        docker compose -f /opt/lh-contract/docker-compose.prod.yml restart backend > /dev/null 2>&1 || true
    endscript
}
EOF

# 手动测试轮转
logrotate -f /etc/logrotate.d/lh-contract
```

### 8.4 配置数据库自动备份

```bash
# 创建备份脚本
cat > /opt/lh-contract/scripts/backup_db.sh << 'EOF'
#!/bin/bash

# 配置
BACKUP_DIR="/opt/lh-contract/backups"
DB_CONTAINER="lh-contract-postgres"
DB_NAME="lh_contract"
DB_USER="lhuser"
RETENTION_DAYS=30

# 创建备份目录
mkdir -p $BACKUP_DIR

# 生成备份文件名
BACKUP_FILE="$BACKUP_DIR/lh_contract_$(date +%Y%m%d_%H%M%S).sql.gz"

# 执行备份
docker exec $DB_CONTAINER pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_FILE

# 删除旧备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# 记录日志
echo "[$(date)] Backup completed: $BACKUP_FILE" >> /opt/lh-contract/logs/backup.log
EOF

# 设置执行权限
chmod +x /opt/lh-contract/scripts/backup_db.sh

# 添加定时任务（每天凌晨2点执行）
crontab -e
# 添加以下行:
# 0 2 * * * /opt/lh-contract/scripts/backup_db.sh
```

### 8.5 配置自动启动

```bash
# 创建systemd服务文件
cat > /etc/systemd/system/lh-contract.service << 'EOF'
[Unit]
Description=LH Contract Management System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/lh-contract
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
systemctl daemon-reload

# 启用服务
systemctl enable lh-contract.service

# 启动服务
systemctl start lh-contract.service

# 查看状态
systemctl status lh-contract.service
```

---

## 9. 备份与恢复

### 9.1 完整备份

```bash
# 创建完整备份脚本
cat > /opt/lh-contract/scripts/full_backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/lh-contract/backups/full"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="lh_contract_full_$TIMESTAMP"

mkdir -p $BACKUP_DIR

# 停止服务
cd /opt/lh-contract
docker compose -f docker-compose.prod.yml down

# 备份数据
tar -czf $BACKUP_DIR/$BACKUP_NAME.tar.gz \
  data/ \
  logs/ \
  .env \
  docker-compose.prod.yml

# 重启服务
docker compose -f docker-compose.prod.yml up -d

echo "[$(date)] Full backup completed: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
EOF

chmod +x /opt/lh-contract/scripts/full_backup.sh
```

### 9.2 数据库恢复

```bash
# 恢复数据库备份
gunzip < /opt/lh-contract/backups/lh_contract_20241216_020000.sql.gz | \
  docker exec -i lh-contract-postgres psql -U lhuser -d lh_contract
```

### 9.3 LXC容器备份（在PVE主机上）

```bash
# 在PVE主机上执行

# 停止容器
pct stop 100

# 备份容器
vzdump 100 --compress gzip --mode snapshot --storage local

# 启动容器
pct start 100

# 备份文件位于: /var/lib/vz/dump/
```

---

## 10. 故障排查

### 10.1 常见问题

**问题1: 容器无法启动**
```bash
# 检查容器状态
pct status 100

# 查看容器日志
pct enter 100
journalctl -xe

# 检查资源限制
pct config 100
```

**问题2: Docker服务无法启动**
```bash
# 检查Docker状态
systemctl status docker

# 查看Docker日志
journalctl -u docker -n 50

# 重启Docker
systemctl restart docker
```

**问题3: 应用无法访问**
```bash
# 检查容器是否运行
docker compose -f docker-compose.prod.yml ps

# 检查端口占用
netstat -tulnp | grep -E '3000|8000|5432'

# 检查防火墙
ufw status

# 检查服务日志
docker compose -f docker-compose.prod.yml logs
```

**问题4: 数据库连接失败**
```bash
# 进入postgres容器
docker exec -it lh-contract-postgres bash

# 测试数据库连接
psql -U lhuser -d lh_contract

# 检查数据库日志
docker logs lh-contract-postgres
```

**问题5: 前端无法连接后端**
```bash
# 检查环境变量
cat /opt/lh-contract/.env | grep VITE_API_BASE_URL

# 检查CORS配置
cat /opt/lh-contract/.env | grep BACKEND_CORS_ORIGINS

# 重新构建前端
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

### 10.2 日志查看

```bash
# 查看所有容器日志
docker compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f postgres

# 查看最近100行日志
docker compose -f docker-compose.prod.yml logs --tail=100

# 查看实时日志（持续跟踪）
docker compose -f docker-compose.prod.yml logs -f --tail=50
```

### 10.3 性能监控

```bash
# 容器资源使用情况
docker stats

# 系统资源使用
htop

# 网络连接
netstat -tulnp

# 磁盘使用
df -h
du -sh /opt/lh-contract/*

# 数据库性能
docker exec -it lh-contract-postgres psql -U lhuser -d lh_contract -c "SELECT * FROM pg_stat_activity;"
```

---

## 11. 维护命令速查

### 11.1 日常维护

```bash
# 重启所有服务
cd /opt/lh-contract
docker compose -f docker-compose.prod.yml restart

# 重启单个服务
docker compose -f docker-compose.prod.yml restart backend

# 停止所有服务
docker compose -f docker-compose.prod.yml down

# 启动所有服务
docker compose -f docker-compose.prod.yml up -d

# 更新镜像
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# 清理未使用的资源
docker system prune -a --volumes
```

### 11.2 更新应用

```bash
# 拉取最新代码
cd /opt/lh-contract
git pull origin release/v1.1

# 或切换到新版本
git fetch --tags
git checkout v1.1.1

# 重新构建
docker compose -f docker-compose.prod.yml build

# 重启服务
docker compose -f docker-compose.prod.yml up -d
```

### 11.3 数据库维护

```bash
# 进入数据库
docker exec -it lh-contract-postgres psql -U lhuser -d lh_contract

# 备份数据库
docker exec lh-contract-postgres pg_dump -U lhuser lh_contract | gzip > backup.sql.gz

# 恢复数据库
gunzip < backup.sql.gz | docker exec -i lh-contract-postgres psql -U lhuser -d lh_contract

# 清理数据库
docker exec -it lh-contract-postgres psql -U lhuser -d lh_contract -c "VACUUM ANALYZE;"
```

---

## 12. 安全加固建议

### 12.1 SSH 安全配置

```bash
# 编辑SSH配置
vim /etc/ssh/sshd_config

# 推荐配置:
# Port 22 # 可以改为非标准端口
# PermitRootLogin no # 禁止root直接登录
# PasswordAuthentication no # 使用密钥认证
# PubkeyAuthentication yes

# 重启SSH
systemctl restart sshd
```

### 12.2 定期更新

```bash
# 自动安全更新
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

### 12.3 监控异常登录

```bash
# 安装fail2ban
apt install -y fail2ban

# 启用fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# 查看状态
fail2ban-client status
```

---

## 13. 联系与支持

如遇到问题，请检查:
1. 系统日志: `journalctl -xe`
2. Docker日志: `docker compose logs`
3. 应用日志: `/opt/lh-contract/logs/`
4. GitHub Issues: https://github.com/palmtom316/LH_Contract_Docker/issues

---

**部署完成！**

访问地址:
- 前端: http://192.168.72.101:3000 (或 http://192.168.72.101 如果配置了Nginx)
- 后端API: http://192.168.72.101:8000
- API文档: http://192.168.72.101:8000/docs

默认管理员账号（如果有初始化）:
- 用户名: admin
- 密码: [查看初始化脚本或文档]
