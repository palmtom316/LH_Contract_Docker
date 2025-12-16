# LH合同管理系统 - PVE LXC 快速部署参考卡

## 📋 硬件信息
- 服务器: 铭凡 MS-A2
- 内存: 32GB
- 硬盘: 2×2TB SSD
- 网口: 4个
- PVE主机IP: 192.168.72.100
- 容器IP: 192.168.72.101

---

## 🚀 快速部署流程

### 第一步：安装PVE系统
```bash
# 1. 下载 Proxmox VE ISO: https://www.proxmox.com/en/downloads
# 2. 制作U盘启动盘（Windows用Rufus，Linux用dd）
# 3. 从U盘启动，选择 "Install Proxmox VE"
# 4. 配置网络：IP=192.168.72.100, Gateway=192.168.72.1
# 5. 完成安装并重启
# 6. 访问: https://192.168.72.100:8006
```

### 第二步：创建LXC容器（PVE Web界面）
```
1. 登录PVE Web界面
2. 右上角点击"创建CT"
3. 配置:
   - CT ID: 100
   - 主机名: lh-contract
   - 模板: debian-12-standard
   - 磁盘: 50GB
   - CPU: 4核
   - 内存: 8192MB, SWAP: 2048MB
   - 网络: IP=192.168.72.101/24, GW=192.168.72.1
   - 特性: 勾选 nesting=1
4. 点击"完成"并启动容器
```

### 第三步：自动部署应用（推荐）
```bash
# SSH登录到容器
ssh root@192.168.72.101

# 下载并执行自动部署脚本
wget https://raw.githubusercontent.com/palmtom316/LH_Contract_Docker/release/v1.1/scripts/deploy_lxc.sh
chmod +x deploy_lxc.sh
./deploy_lxc.sh
```

### 第四步：访问应用
```
前端: http://192.168.72.101:3000
后端: http://192.168.72.101:8000
API文档: http://192.168.72.101:8000/docs
```

---

## 📝 手动部署步骤（如果不使用自动脚本）

### 1. 更新系统并安装基础工具
```bash
apt update && apt upgrade -y
apt install -y curl wget git vim htop net-tools ca-certificates gnupg lsb-release sudo ufw
```

### 2. 安装Docker
```bash
# 安装Docker
curl -fsSL https://get.docker.com | sh

# 启动Docker
systemctl start docker
systemctl enable docker

# 验证
docker --version
docker compose version
```

### 3. 部署应用
```bash
# 创建目录
mkdir -p /opt/lh-contract
cd /opt/lh-contract

# 克隆代码
git clone -b release/v1.1 https://github.com/palmtom316/LH_Contract_Docker.git .
git checkout v1.1.0

# 配置环境变量
cp .env.example .env
vim .env  # 编辑必要的配置项

# 启动服务
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### 4. 配置防火墙
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 3000/tcp
ufw allow 8000/tcp
ufw enable
```

---

## 🔧 常用命令

### 容器管理（在PVE主机上执行）
```bash
pct start 100      # 启动容器
pct stop 100       # 停止容器
pct restart 100    # 重启容器
pct status 100     # 查看状态
pct enter 100      # 进入容器
```

### 应用管理（在容器内执行）
```bash
cd /opt/lh-contract

# 查看服务状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 重启服务
docker compose -f docker-compose.prod.yml restart

# 停止服务
docker compose -f docker-compose.prod.yml down

# 启动服务
docker compose -f docker-compose.prod.yml up -d

# 重新构建
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### 查看单个服务日志
```bash
cd /opt/lh-contract
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f postgres
```

### 数据库管理
```bash
# 进入数据库
docker exec -it lh-contract-postgres psql -U lhuser -d lh_contract

# 备份数据库
docker exec lh-contract-postgres pg_dump -U lhuser lh_contract | gzip > backup_$(date +%Y%m%d).sql.gz

# 恢复数据库
gunzip < backup.sql.gz | docker exec -i lh-contract-postgres psql -U lhuser -d lh_contract
```

---

## 🔍 故障排查

### 检查服务状态
```bash
# 检查容器是否运行
docker ps

# 检查端口占用
netstat -tulnp | grep -E '3000|8000|5432'

# 检查防火墙
ufw status

# 检查系统资源
htop
docker stats
```

### 查看日志
```bash
# 应用日志
cd /opt/lh-contract
docker compose -f docker-compose.prod.yml logs --tail=100

# 系统日志
journalctl -xe

# Docker日志
journalctl -u docker -n 50
```

### 重启所有组件
```bash
# 1. 重启容器（在PVE主机上）
pct restart 100

# 2. 重启Docker（在容器内）
systemctl restart docker

# 3. 重启应用（在容器内）
cd /opt/lh-contract
docker compose -f docker-compose.prod.yml restart
```

---

## 📦 备份与恢复

### 数据库备份
```bash
# 手动备份
/opt/lh-contract/scripts/backup_db.sh

# 自动备份（已配置每天2点执行）
crontab -l
```

### 完整备份
```bash
# 停止服务
cd /opt/lh-contract
docker compose -f docker-compose.prod.yml down

# 备份数据
tar -czf /root/lh-contract-backup-$(date +%Y%m%d).tar.gz \
  /opt/lh-contract/data \
  /opt/lh-contract/.env \
  /opt/lh-contract/logs

# 启动服务
docker compose -f docker-compose.prod.yml up -d
```

### LXC容器快照（在PVE主机上）
```bash
# 停止容器
pct stop 100

# 创建备份
vzdump 100 --compress gzip --mode snapshot

# 启动容器
pct start 100

# 备份文件位于: /var/lib/vz/dump/
```

---

## 🔐 安全检查清单

- [ ] 修改默认密码
- [ ] 配置SSH密钥认证
- [ ] 禁用root直接SSH登录
- [ ] 启用UFW防火墙
- [ ] 定期更新系统 `apt update && apt upgrade`
- [ ] 配置自动备份
- [ ] 检查.env文件权限 `chmod 600 /opt/lh-contract/.env`
- [ ] 设置强数据库密码
- [ ] 定期检查日志

---

## 📊 性能监控

### 实时监控
```bash
# 容器资源使用
docker stats

# 系统资源
htop

# 网络连接
netstat -tulnp

# 磁盘使用
df -h
du -sh /opt/lh-contract/*
```

### 数据库性能
```bash
docker exec -it lh-contract-postgres psql -U lhuser -d lh_contract -c "SELECT * FROM pg_stat_activity;"
```

---

## 🆘 紧急联系

**常见问题文档**: `PVE_LXC_DEPLOYMENT_GUIDE.md`

**GitHub Issues**: https://github.com/palmtom316/LH_Contract_Docker/issues

**日志位置**:
- 应用日志: `/opt/lh-contract/logs/`
- Docker日志: `journalctl -u docker`
- 系统日志: `journalctl -xe`

---

## 📈 升级流程

### 升级到新版本
```bash
cd /opt/lh-contract

# 备份当前版本
docker compose -f docker-compose.prod.yml down
tar -czf ~/backup-before-upgrade-$(date +%Y%m%d).tar.gz data/ .env

# 拉取新版本代码
git fetch --tags
git checkout v1.1.1  # 替换为目标版本

# 重新构建和启动
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 检查服务状态
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
```

---

## ✅ 部署验证清单

部署完成后，请检查以下项目：

- [ ] PVE Web界面可访问 (https://192.168.72.100:8006)
- [ ] LXC容器正常运行
- [ ] 可以SSH登录容器 (192.168.72.101)
- [ ] Docker服务运行正常 `systemctl status docker`
- [ ] 所有容器都在运行 `docker ps`
- [ ] 前端网页可访问 (http://192.168.72.101:3000)
- [ ] 后端API可访问 (http://192.168.72.101:8000)
- [ ] 数据库连接正常
- [ ] 可以登录系统
- [ ] 防火墙已配置 `ufw status`
- [ ] 自动启动已配置 `systemctl status lh-contract`
- [ ] 备份脚本已创建 `ls /opt/lh-contract/scripts/`
- [ ] 定时任务已配置 `crontab -l`

---

**祝部署顺利！** 🎉
