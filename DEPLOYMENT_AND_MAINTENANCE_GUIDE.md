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
