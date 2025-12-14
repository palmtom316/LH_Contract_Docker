# 蓝海合同管理系统 - Proxmox VE LXC 部署文档

## 版本信息

- **版本号**: v1.0.0-beta
- **分支**: release/v1.0.0-beta
- **发布日期**: 2024-12-14
- **部署环境**: Proxmox VE 7.x / 8.x LXC 容器

---

## 目录

1. [环境说明](#1-环境说明)
2. [创建 LXC 容器](#2-创建-lxc-容器)
3. [容器初始化配置](#3-容器初始化配置)
4. [安装 Docker](#4-安装-docker)
5. [部署应用](#5-部署应用)
6. [网络配置](#6-网络配置)
7. [存储配置](#7-存储配置)
8. [资源监控](#8-资源监控)
9. [容器备份](#9-容器备份)
10. [常见问题](#10-常见问题)

---

## 1. 环境说明

### 1.1 Proxmox VE 版本要求

| 组件 | 版本要求 |
|------|----------|
| Proxmox VE | 7.0+ 或 8.0+ |
| 宿主机内核 | 5.15+ |
| LXC 模板 | Ubuntu 22.04 / Debian 12 |

### 1.2 推荐配置

| 配置项 | 最低要求 | 推荐配置 |
|--------|----------|----------|
| CPU 核心 | 2核 | 4核 |
| 内存 | 2GB | 4GB |
| 交换空间 | 512MB | 1GB |
| 根文件系统 | 20GB | 40GB |
| 数据存储 | 20GB | 50GB |

### 1.3 网络规划

| 用途 | 端口 | 说明 |
|------|------|------|
| HTTP | 80 | Web 访问 |
| HTTPS | 443 | 加密访问 |
| API | 8000 | 后端 API (内部) |
| 数据库 | 5432 | PostgreSQL (内部) |

---

## 2. 创建 LXC 容器

### 2.1 下载容器模板

通过 PVE Web 界面：

1. 登录 Proxmox VE Web 界面
2. 选择目标存储 → CT Templates
3. 点击 "Templates" 按钮
4. 下载 `ubuntu-22.04-standard` 或 `debian-12-standard`

或通过命令行：

```bash
# 在 PVE 宿主机上执行
pveam update
pveam available | grep ubuntu-22
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst
```

### 2.2 通过 Web 界面创建容器

1. 点击右上角 "Create CT"
2. 填写基本信息：
   - **CT ID**: 200 (或其他可用ID)
   - **Hostname**: lh-contract
   - **Password**: 设置 root 密码
   - **SSH public key**: (可选) 粘贴公钥

3. 选择模板：
   - **Template**: ubuntu-22.04-standard

4. 配置磁盘：
   - **Root Disk**: 40GB (local-lvm)

5. 配置 CPU：
   - **Cores**: 4

6. 配置内存：
   - **Memory**: 4096 MB
   - **Swap**: 1024 MB

7. 配置网络：
   - **Bridge**: vmbr0
   - **IPv4**: DHCP 或静态 IP
   - **IPv6**: 可选

8. 确认并创建

### 2.3 通过命令行创建容器

```bash
# 在 PVE 宿主机上执行

# 创建容器
pct create 200 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname lh-contract \
  --memory 4096 \
  --swap 1024 \
  --cores 4 \
  --rootfs local-lvm:40 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --unprivileged 0 \
  --features nesting=1 \
  --password

# 查看创建的容器
pct list
```

### 2.4 关键配置：启用 Docker 支持

**重要**: 在 LXC 中运行 Docker 需要特殊配置。

编辑容器配置文件（在 PVE 宿主机上）：

```bash
# 编辑容器配置
nano /etc/pve/lxc/200.conf
```

添加以下配置：

```ini
# 基本配置
arch: amd64
cores: 4
hostname: lh-contract
memory: 4096
swap: 1024
net0: name=eth0,bridge=vmbr0,ip=dhcp
ostype: ubuntu
rootfs: local-lvm:vm-200-disk-0,size=40G

# Docker 支持配置 (关键!)
unprivileged: 0
features: nesting=1,keyctl=1

# 设备访问权限
lxc.apparmor.profile: unconfined
lxc.cgroup2.devices.allow: a
lxc.cap.drop:
lxc.mount.auto: proc:rw sys:rw
```

### 2.5 启动容器

```bash
# 启动容器
pct start 200

# 查看状态
pct status 200

# 进入容器控制台
pct enter 200
```

---

## 3. 容器初始化配置

进入容器后（`pct enter 200`），执行以下配置：

### 3.1 更新系统

```bash
# 更新包列表
apt update && apt upgrade -y

# 安装基础工具
apt install -y curl wget git vim nano htop net-tools
```

### 3.2 设置时区

```bash
# 设置时区为上海
timedatectl set-timezone Asia/Shanghai

# 验证
date
```

### 3.3 配置 SSH（可选）

```bash
# 安装 SSH 服务
apt install -y openssh-server

# 允许 root 登录（可选，不推荐生产环境）
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# 重启 SSH
systemctl restart sshd
systemctl enable sshd
```

### 3.4 创建普通用户（推荐）

```bash
# 创建用户
adduser lhadmin

# 添加到 sudo 组
usermod -aG sudo lhadmin

# 切换到新用户
su - lhadmin
```

---

## 4. 安装 Docker

### 4.1 安装 Docker Engine

```bash
# 安装依赖
apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 添加 Docker GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
systemctl start docker
systemctl enable docker
```

### 4.2 验证 Docker 安装

```bash
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本
docker compose version

# 运行测试容器
docker run --rm hello-world
```

### 4.3 Docker 无法启动的解决方案

如果 Docker 无法启动，检查以下内容：

```bash
# 查看 Docker 状态
systemctl status docker

# 查看详细日志
journalctl -xeu docker

# 常见问题: cgroup v2 兼容性
# 如果出现 cgroup 错误，编辑 Docker 配置
cat > /etc/docker/daemon.json << EOF
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

# 重启 Docker
systemctl restart docker
```

---

## 5. 部署应用

### 5.1 克隆项目

```bash
# 创建应用目录
mkdir -p /opt/lh-contract
cd /opt/lh-contract

# 克隆代码
git clone https://github.com/palmtom316/LH_Contract_Docker.git .

# 切换到部署分支
git checkout release/v1.0.0-beta
```

### 5.2 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
nano .env
```

修改关键配置：

```bash
# 数据库配置
POSTGRES_USER=lh_admin
POSTGRES_PASSWORD=您的强密码_请修改
POSTGRES_DB=lh_contract_db

# 应用配置
SECRET_KEY=生成的随机密钥
DEBUG=false
APP_ENV=production

# 数据库连接
DATABASE_URL=postgresql+asyncpg://lh_admin:您的数据库密码@db:5432/lh_contract_db
```

### 5.3 创建必要目录

```bash
mkdir -p uploads backups
chmod 755 uploads backups
```

### 5.4 构建并启动服务

```bash
# 构建并启动（后台运行）
docker compose up -d --build

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 5.5 验证部署

```bash
# 检查服务健康状态
curl http://localhost:8000/api/v1/health

# 测试登录
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

---

## 6. 网络配置

### 6.1 LXC 容器网络模式

#### 方式一：DHCP（默认）

容器配置已使用 DHCP，会自动获取 IP。

```bash
# 在容器内查看 IP
ip addr show eth0
```

#### 方式二：静态 IP

编辑 PVE 宿主机上的容器配置：

```bash
# 在 PVE 宿主机执行
nano /etc/pve/lxc/200.conf
```

修改网络配置：

```ini
net0: name=eth0,bridge=vmbr0,ip=192.168.1.100/24,gw=192.168.1.1
```

重启容器：

```bash
pct reboot 200
```

### 6.2 端口转发（NAT 模式）

如果容器使用内网 IP，需要在 PVE 宿主机配置端口转发：

```bash
# 在 PVE 宿主机执行
# 假设容器 IP 为 192.168.1.100

# 转发 80 端口
iptables -t nat -A PREROUTING -i vmbr0 -p tcp --dport 80 -j DNAT --to 192.168.1.100:80

# 转发 443 端口
iptables -t nat -A PREROUTING -i vmbr0 -p tcp --dport 443 -j DNAT --to 192.168.1.100:443

# 保存规则
apt install iptables-persistent
netfilter-persistent save
```

### 6.3 容器内 Nginx 配置（可选）

如果需要在容器内配置 Nginx 反向代理：

```bash
# 安装 Nginx
apt install -y nginx

# 创建配置
cat > /etc/nginx/sites-available/lh-contract << 'EOF'
server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /uploads/ {
        proxy_pass http://127.0.0.1:8000/uploads/;
    }
}
EOF

# 启用配置
ln -s /etc/nginx/sites-available/lh-contract /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default

# 测试并重启
nginx -t
systemctl restart nginx
systemctl enable nginx
```

---

## 7. 存储配置

### 7.1 添加额外磁盘（用于数据存储）

在 PVE 宿主机上：

```bash
# 添加磁盘到容器
pct set 200 -mp0 /mnt/data/lh-contract,mp=/data,size=50G

# 或创建新的虚拟磁盘
pct set 200 -mp0 local-lvm:50,mp=/data
```

### 7.2 挂载点配置

编辑容器配置 `/etc/pve/lxc/200.conf`：

```ini
# 添加数据磁盘挂载点
mp0: local-lvm:vm-200-disk-1,mp=/data,size=50G
```

### 7.3 使用宿主机目录（Bind Mount）

如果要使用宿主机目录：

```bash
# 在 PVE 宿主机创建目录
mkdir -p /mnt/lh-contract-data

# 编辑容器配置
# /etc/pve/lxc/200.conf
mp0: /mnt/lh-contract-data,mp=/data
```

### 7.4 配置 Docker 使用独立存储

```bash
# 在容器内，修改 docker-compose.yml
# 将数据卷指向 /data 目录

# 或修改 Docker 数据目录
cat > /etc/docker/daemon.json << EOF
{
  "data-root": "/data/docker",
  "storage-driver": "overlay2"
}
EOF

systemctl restart docker
```

---

## 8. 资源监控

### 8.1 容器资源限制

在 PVE 宿主机编辑容器配置：

```bash
nano /etc/pve/lxc/200.conf
```

添加资源限制：

```ini
# CPU 限制
cores: 4
cpulimit: 4

# 内存限制
memory: 4096
swap: 1024

# IO 限制（可选）
# mp0: local-lvm:vm-200-disk-0,mp=/,size=40G,backup=0
```

### 8.2 容器内监控

```bash
# 安装监控工具
apt install -y htop iotop

# 查看资源使用
htop

# Docker 资源统计
docker stats

# 磁盘使用
df -h
```

### 8.3 PVE 监控

通过 PVE Web 界面：
1. 选择容器 200
2. 查看 "Summary" 页面的资源图表
3. 查看 "Monitor" 页面的实时监控

---

## 9. 容器备份

### 9.1 通过 PVE 备份

**Web 界面操作：**

1. 选择容器 200
2. 点击 "Backup"
3. 选择存储和压缩方式
4. 点击 "Backup" 开始备份

**命令行备份：**

```bash
# 在 PVE 宿主机执行

# 创建备份
vzdump 200 --storage local --compress zstd --mode snapshot

# 查看备份
ls /var/lib/vz/dump/

# 计划任务备份
cat >> /etc/cron.d/vzdump << EOF
0 2 * * * root vzdump 200 --storage local --compress zstd --mode snapshot --quiet
EOF
```

### 9.2 应用数据备份

在容器内创建备份脚本：

```bash
cat > /opt/lh-contract/scripts/backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/data/backups"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=7

mkdir -p $BACKUP_DIR

# 备份数据库
docker exec lh_contract_db pg_dump -U lh_admin -d lh_contract_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 备份上传文件
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz -C /opt/lh-contract uploads/

# 删除旧备份
find $BACKUP_DIR -type f -mtime +$KEEP_DAYS -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/lh-contract/scripts/backup.sh

# 添加定时任务
echo "0 3 * * * root /opt/lh-contract/scripts/backup.sh" >> /etc/crontab
```

### 9.3 恢复容器

```bash
# 在 PVE 宿主机执行

# 列出可用备份
ls /var/lib/vz/dump/

# 恢复到新容器
pct restore 201 /var/lib/vz/dump/vzdump-lxc-200-2024_12_14-02_00_00.tar.zst

# 或覆盖现有容器（危险操作）
pct restore 200 /var/lib/vz/dump/vzdump-lxc-200-2024_12_14-02_00_00.tar.zst --force
```

---

## 10. 常见问题

### 10.1 Docker 无法启动

**症状**: `systemctl start docker` 失败

**解决方案**:

```bash
# 检查配置
cat /etc/pve/lxc/200.conf | grep -E "nesting|unprivileged|apparmor"

# 确保包含:
# unprivileged: 0
# features: nesting=1,keyctl=1
# lxc.apparmor.profile: unconfined

# 重启容器后重试
pct reboot 200  # 在 PVE 宿主机执行
```

### 10.2 网络不通

**症状**: 容器内无法访问外网

**解决方案**:

```bash
# 检查网络配置
ip addr
ip route

# 检查 DNS
cat /etc/resolv.conf

# 手动添加 DNS
echo "nameserver 8.8.8.8" >> /etc/resolv.conf

# 测试
ping -c 3 google.com
```

### 10.3 存储空间不足

**症状**: `No space left on device`

**解决方案**:

```bash
# 检查磁盘使用
df -h

# 清理 Docker
docker system prune -a

# 在 PVE 扩展磁盘
pct resize 200 rootfs +20G  # 在 PVE 宿主机执行

# 容器内扩展文件系统
resize2fs /dev/sda1
```

### 10.4 权限问题

**症状**: `Permission denied` 错误

**解决方案**:

```bash
# 确保容器为特权模式
# /etc/pve/lxc/200.conf
unprivileged: 0

# 或修复目录权限
chown -R root:root /opt/lh-contract
chmod -R 755 /opt/lh-contract/uploads
```

### 10.5 容器自动启动

```bash
# 在 PVE 宿主机执行
pct set 200 --onboot 1

# 或编辑配置
# /etc/pve/lxc/200.conf
onboot: 1
```

---

## 快速部署清单

### PVE 宿主机操作

```bash
# 1. 下载模板
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst

# 2. 创建容器
pct create 200 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname lh-contract \
  --memory 4096 \
  --swap 1024 \
  --cores 4 \
  --rootfs local-lvm:40 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --unprivileged 0 \
  --features nesting=1,keyctl=1 \
  --password

# 3. 启用 Docker 支持
cat >> /etc/pve/lxc/200.conf << EOF
lxc.apparmor.profile: unconfined
lxc.cgroup2.devices.allow: a
lxc.cap.drop:
lxc.mount.auto: proc:rw sys:rw
EOF

# 4. 启动容器
pct start 200
```

### 容器内操作

```bash
# 1. 更新系统
apt update && apt upgrade -y
apt install -y curl wget git

# 2. 安装 Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker

# 3. 部署应用
mkdir -p /opt/lh-contract && cd /opt/lh-contract
git clone https://github.com/palmtom316/LH_Contract_Docker.git .
git checkout release/v1.0.0-beta
cp .env.example .env
nano .env  # 修改配置

# 4. 启动
docker compose up -d --build
```

---

**文档版本**: 1.0  
**最后更新**: 2024-12-14  
**适用版本**: v1.0.0-beta  
**部署环境**: Proxmox VE 7.x / 8.x LXC
