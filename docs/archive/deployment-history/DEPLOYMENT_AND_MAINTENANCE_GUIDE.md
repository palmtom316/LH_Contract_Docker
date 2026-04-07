# 蓝海电气合同管理系统 - 部署与维护手册

本文档详细说明了系统的部署、迁移、维护和升级流程。

## 1. 系统要求

- **操作系统**: Ubuntu 20.04/22.04 LTS (推荐) 或 Debian 11+
- **软件依赖**:
  - Docker (20.10+)
  - Docker Compose (v2.0+)
  - Git

## 2. 新服务器部署流程 (从零开始)

### 2.1 获取代码
登录到服务器，拉取项目代码：

```bash
cd /opt
# 假设已有 git 权限，或者使用 https
git clone <repository_url> lh-contract
cd lh-contract
```

### 2.2 环境配置
复制生产环境配置文件：

```bash
cp .env.example .env.production
```

**关键配置项修改** (`nano .env.production`):
- `POSTGRES_PASSWORD`: 设置强密码
- `SECRET_KEY`: 生成随机密钥
- `ALLOWED_HOSTS`: 设置为 `["*"]` (或具体的服务器IP/域名)
- `CORS_ORIGINS`: 设置为 `["*"]` (或前端访问地址)

### 2.3 准备前端配置
修改前端连接地址，指向 Nginx 入口 (即服务器 IP 或域名，端口 80)：

```bash
# 假设服务器 IP 为 192.168.72.35
echo "VITE_API_BASE_URL=http://192.168.72.35/api/v1" > frontend/.env.local
```

### 2.4 启动服务
使用生产环境 compose 文件构建并启动：

```bash
# 确保 nginx 配置目录存在 (代码库中应包含 nginx/prod.conf)
# 启动所有服务
docker compose -f docker-compose.prod.yml up -d --build
```

### 2.5 初始化数据 (首次运行)
如果是全新的数据库，系统启动时会自动创建表结构。
如果需要初始化基础数据 (如管理员账户)，请参考 `backend/app/init_data.py` 或直接通过 API 注册/初始化。

## 3. 版本升级流程

当代码有更新时，请按照以下步骤操作：

### 3.1 拉取最新代码

```bash
cd /opt/lh-contract
git pull origin release/v1.1.1
```

### 3.2 检查配置变更
检查 `.env.example` 或更新日志，看是否有新增的环境变量需要添加到 `.env.production`。

### 3.3 重建并重启服务
这一步会重新构建 Docker 镜像并应用最新代码：

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

*注：`--build` 参数确保镜像被重新构建，包括依赖更新。*

### 3.4 验证
访问浏览器，Ctrl+F5 强制刷新，确认版本号和功能正常。

## 4. 常见问题与故障排除

### 4.1 "Network Error" 或 500 错误
- **检查后端日志**: `docker compose -f docker-compose.prod.yml logs --tail=50 backend`
- **检查 Nginx 状态**: `docker compose -f docker-compose.prod.yml logs nginx`
- **CORS 问题**: 确认 `.env.production` 中的 `ALLOWED_HOSTS` 和 `CORS_ORIGINS` 包含当前访问的 IP/域名。

### 4.2 构建速度慢
- 后端 Dockerfile 已内置国内源 (阿里云/清华/中科大)，通常不需要通过代理翻墙。
- 确保服务器 DNS 正常 (`ping mirrors.ustc.edu.cn`).

### 4.3 数据库连接失败
- 确认 `.env.production` 中的数据库密码与 `docker-compose.prod.yml` 中的一致。

## 5. 备份与恢复

### 5.1 数据库备份

```bash
# 在宿主机执行
docker exec -t lh_contract_db_prod pg_dumpall -c -U <db_user> > dump_`date +%d-%m-%Y"_"%H_%M_%S`.sql
```

### 5.2 文件备份
定期备份 `uploads` 目录：

```bash
tar -czvf uploads_backup.tar.gz ./uploads
```

## 6. Docker 清理维护

### 6.1 查看 Docker 磁盘使用情况

```bash
# 查看 Docker 占用的磁盘空间概览
docker system df

# 查看详细信息
docker system df -v
```

### 6.2 安全清理（推荐日常使用）

```bash
# 方式一：使用清理脚本（推荐）
cd /opt/lh-contract
chmod +x scripts/docker_cleanup.sh
./scripts/docker_cleanup.sh

# 方式二：手动清理悬空资源
docker system prune -f
```

**此命令会清理：**
- 已停止的容器
- 悬空镜像（未标记的中间层）
- 未使用的网络
- 构建缓存

**此命令不会清理：**
- 正在运行的容器
- 有标签的镜像
- 数据卷（postgres_data, redis_data）

### 6.3 深度清理（版本升级后）

```bash
# 清理所有未使用的镜像（包括旧版本）
docker system prune -a -f

# 或使用脚本的深度模式
./scripts/docker_cleanup.sh --aggressive
```

⚠️ **警告**：深度清理会删除所有未被容器使用的镜像，下次启动需要重新拉取或构建。

### 6.4 清理日志文件

系统已配置日志轮转，但如遇日志过大：

```bash
# 查看各容器日志大小
sudo du -sh /var/lib/docker/containers/*/

# 清空特定容器的日志（保留文件）
sudo truncate -s 0 $(docker inspect --format='{{.LogPath}}' lh_contract_backend_prod)
```

### 6.5 ⚠️ 危险操作（谨慎使用）

```bash
# 清理未使用的卷 - 可能删除数据！
# 仅在确认数据已备份后执行
docker volume prune -f

# 彻底清理 - 删除所有未使用资源包括卷
# 极度危险，仅用于重新部署场景
docker system prune -a --volumes -f
```

### 6.6 定时清理（可选）

添加 cron 任务自动清理：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每周日凌晨3点执行安全清理）
0 3 * * 0 cd /opt/lh-contract && ./scripts/docker_cleanup.sh >> /var/log/docker_cleanup.log 2>&1
```

## 7. 内存优化

### 7.1 查看当前内存使用

```bash
# 查看系统总内存
free -h

# 查看各容器内存使用
sudo docker stats --no-stream
```

### 7.2 使用低内存配置

对于内存受限的环境（4-8GB RAM），可以使用低内存版本的配置：

```bash
# 停止当前服务
cd /opt/lh-contract
docker compose -f docker-compose.prod.yml down

# 使用低内存配置启动
docker compose -f docker-compose.prod.lowmem.yml up -d
```

### 7.3 内存配置对比

| 服务 | 标准配置 | 低内存配置 | 说明 |
|------|----------|------------|------|
| PostgreSQL | 2G | 512M | 优化了 shared_buffers, work_mem 等参数 |
| Redis | 512M | 128M | 减少缓存上限，禁用RDB快照 |
| Backend | 2G | 512M | 减少 worker 数量到 2 个 |
| Frontend | 无限制 | 384M | 限制 Node.js 堆内存 |
| Nginx | 无限制 | 64M | Nginx 本身很轻量 |
| **总计** | **~6.5G** | **~1.7G** | 降低约 **74%** |

### 7.4 手动调整内存限制

如需自定义内存限制，编辑 `docker-compose.prod.yml` 中的 `deploy.resources.limits.memory`：

```yaml
deploy:
  resources:
    limits:
      memory: 512M    # 调整此值
    reservations:
      memory: 256M    # 最低保证内存
```

修改后重启服务：
```bash
docker compose -f docker-compose.prod.yml up -d
```

### 7.5 其他内存优化建议

1. **减少 Backend Worker 数量**：编辑 `.env.production`，设置 `WORKERS=2`
2. **启用 Swap**（应急）：
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```
3. **监控内存使用**：
   ```bash
   # 实时监控
   watch -n 2 'free -h && echo "" && docker stats --no-stream'
   ```
