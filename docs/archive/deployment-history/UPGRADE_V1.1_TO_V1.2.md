# V1.1 → V1.2 版本升级指南

**适用场景**: 从 V1.1 版本升级到 V1.2 版本  
**目标服务器**: 192.168.72.101  
**更新日期**: 2025年12月23日

---

## 📋 升级前检查清单

> ⚠️ **重要**: 升级前请务必完成以下步骤

- [ ] 备份数据库
- [ ] 备份上传文件目录
- [ ] 记录当前版本信息
- [ ] 确保有足够磁盘空间（至少 2GB）
- [ ] 通知用户系统将暂时不可用

---

## 一、升级前准备（通用步骤）

### 1.1 SSH 连接到服务器

```bash
# 从您的电脑连接到服务器
ssh root@192.168.72.101

# 或使用普通用户
ssh your-user@192.168.72.101
```

### 1.2 备份数据库（必须！）

```bash
# 进入项目目录
cd /path/to/LH_Contract_Docker

# 方法1: 使用 Docker 备份
docker exec lh_contract_db pg_dump -U lh_admin lh_contract_db > backup_v1.1_$(date +%Y%m%d_%H%M%S).sql

# 方法2: 如果有 backups 目录
mkdir -p backups
docker exec lh_contract_db pg_dump -U lh_admin lh_contract_db > backups/backup_before_v1.2_$(date +%Y%m%d).sql

# 验证备份文件
ls -la backups/
head -20 backups/backup_before_v1.2_*.sql
```

### 1.3 备份上传文件

```bash
# 备份 uploads 目录
cp -r uploads uploads_backup_$(date +%Y%m%d)

# 或压缩备份
tar -czvf uploads_backup_v1.1.tar.gz uploads/
```

### 1.4 记录当前状态

```bash
# 查看当前版本
cat README.md | head -5

# 查看当前 Docker 容器状态
docker-compose ps

# 记录当前镜像
docker images | grep lh_contract
```

---

## 二、方式A：通过 GitHub 拉取升级

### 适用条件
- 服务器可以访问 GitHub
- 已配置 Git

### 2.1 拉取最新代码

```bash
# 进入项目目录
cd /path/to/LH_Contract_Docker

# 查看当前分支
git branch

# 暂存本地更改（如有）
git stash

# 获取远程更新
git fetch origin

# 切换到 release/V1.2 分支
git checkout release/V1.2

# 拉取最新代码
git pull origin release/V1.2
```

### 2.2 更新环境变量（如需要）

V1.2 新增了 `REFRESH_TOKEN_EXPIRE_DAYS` 配置，检查并更新 `.env` 文件：

```bash
# 查看新增的环境变量模板
cat .env.example

# 编辑 .env 文件添加新配置（如需要）
nano .env

# 添加以下行（可选，有默认值）
# REFRESH_TOKEN_EXPIRE_DAYS=7
# ACCESS_TOKEN_EXPIRE_MINUTES=120
```

### 2.3 重建并启动服务

```bash
# 停止当前服务
docker-compose down

# 重建镜像（使用新代码）
docker-compose build --no-cache

# 启动服务
docker-compose up -d

# 查看日志确认启动成功
docker-compose logs -f --tail=100
```

### 2.4 验证升级

```bash
# 检查所有容器运行状态
docker-compose ps

# 检查后端健康状态
curl http://localhost:8000/health

# 检查版本（如有版本API）
curl http://localhost:8000/api/v1/version
```

---

## 三、方式B：通过局域网直接升级

### 适用条件
- 服务器无法访问 GitHub
- 本地开发机（如您的 Windows 电脑）已有最新代码

### 3.1 在本地准备升级包

在您的 Windows 电脑上执行：

```powershell
# 进入项目目录
cd D:\LH_Contract_Docker

# 创建升级包（排除不需要的文件）
# 使用 7-Zip 或 tar
tar -czvf upgrade_v1.2.tar.gz `
    --exclude=".git" `
    --exclude="node_modules" `
    --exclude="__pycache__" `
    --exclude="*.pyc" `
    --exclude="venv" `
    --exclude="uploads/*" `
    --exclude="backend/app/logs/*" `
    .
```

或者使用 PowerShell 压缩：

```powershell
# 方式2：使用 PowerShell 创建 ZIP
Compress-Archive -Path @(
    "backend",
    "frontend", 
    "nginx",
    "docker-compose.yml",
    "docker-compose.prod.yml",
    ".env.example",
    "docs"
) -DestinationPath "upgrade_v1.2.zip" -Force
```

### 3.2 传输升级包到服务器

**方式1: 使用 SCP**

```powershell
# 在 Windows PowerShell 中
scp upgrade_v1.2.tar.gz root@192.168.72.101:/tmp/

# 或 ZIP 文件
scp upgrade_v1.2.zip root@192.168.72.101:/tmp/
```

**方式2: 使用 WinSCP/FileZilla**

1. 打开 WinSCP 或 FileZilla
2. 连接到 `192.168.72.101`
3. 将 `upgrade_v1.2.tar.gz` 上传到 `/tmp/` 目录

### 3.3 在服务器上解压并升级

SSH 连接到服务器后：

```bash
# 进入项目目录
cd /path/to/LH_Contract_Docker

# 停止服务
docker-compose down

# 备份当前代码
mkdir -p ~/backup_v1.1
cp -r backend frontend nginx docker-compose.yml ~/backup_v1.1/

# 解压升级包
# 如果是 tar.gz
cd /tmp
tar -xzvf upgrade_v1.2.tar.gz -C /path/to/LH_Contract_Docker

# 如果是 zip
unzip upgrade_v1.2.zip -d /path/to/LH_Contract_Docker

# 返回项目目录
cd /path/to/LH_Contract_Docker
```

### 3.4 更新配置并重建

```bash
# 检查 .env 文件（如需更新）
cat .env.example
nano .env

# 重建 Docker 镜像
docker-compose build --no-cache

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

---

## 四、数据库迁移（⚠️ 必须执行）

> ⚠️ **重要**: V1.2 版本包含数据库结构变更，**必须执行**以下迁移步骤，否则部分功能将无法正常使用！

### 4.1 执行完整迁移脚本

详细迁移指南请参考: [`docs/DATABASE_MIGRATION_V1.2.md`](docs/DATABASE_MIGRATION_V1.2.md)

```bash
# 连接到数据库
docker exec -it lh_contract_db psql -U lh_admin -d lh_contract_db
```

然后执行以下**关键** SQL（完整版本请查看迁移文档）:

```sql
-- ============================================================
-- V1.2 关键数据库迁移
-- ============================================================

BEGIN;

-- 1. 零星用工表新增列
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS dispatch_file_path VARCHAR(500);
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS skilled_unit_price NUMERIC(15, 2) DEFAULT 0;
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS skilled_quantity NUMERIC(15, 2) DEFAULT 0;
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS skilled_price_total NUMERIC(15, 2) DEFAULT 0;
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS general_unit_price NUMERIC(15, 2) DEFAULT 0;
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS general_quantity NUMERIC(15, 2) DEFAULT 0;
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS general_price_total NUMERIC(15, 2) DEFAULT 0;

-- 2. 创建零星用工材料表
CREATE TABLE IF NOT EXISTS zero_hour_labor_materials (
    id SERIAL PRIMARY KEY,
    zero_hour_labor_id INTEGER NOT NULL REFERENCES zero_hour_labor(id) ON DELETE CASCADE,
    material_name VARCHAR(200) NOT NULL,
    material_unit VARCHAR(50),
    material_quantity NUMERIC(15, 2) DEFAULT 0,
    material_unit_price NUMERIC(15, 2) DEFAULT 0,
    material_price_total NUMERIC(15, 2) DEFAULT 0
);

-- 3. 创建系统配置表
CREATE TABLE IF NOT EXISTS sys_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 4. 创建系统字典表
CREATE TABLE IF NOT EXISTS sys_dictionaries (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL,
    value VARCHAR(200) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

COMMIT;

-- 退出
\q
```

### 4.2 验证迁移结果

```bash
# 检查 zero_hour_labor 表结构
docker exec -it lh_contract_db psql -U lh_admin -d lh_contract_db -c "\d zero_hour_labor"

# 检查新表是否存在
docker exec -it lh_contract_db psql -U lh_admin -d lh_contract_db -c "\dt"
```

---


## 五、验证升级成功

### 5.1 服务状态检查

```bash
# 检查所有容器
docker-compose ps

# 预期输出：所有容器状态为 Up
# NAME                    STATUS
# lh_contract_backend     Up (healthy)
# lh_contract_frontend    Up
# lh_contract_db          Up (healthy)
# lh_contract_redis       Up
# lh_contract_nginx       Up
```

### 5.2 功能测试

1. **登录测试**
   - 打开浏览器访问 `http://192.168.72.101`
   - 使用管理员账号登录
   - ✅ 确认能正常登录

2. **数据完整性**
   - 检查之前录入的合同是否存在
   - 检查财务记录是否完整
   - 检查上传的文件是否可访问

3. **新功能验证**（V1.2 特性）
   - 登录后检查 Token 刷新是否正常
   - 访问报表页面，确认缓存正常工作

### 5.3 日志检查

```bash
# 检查后端日志是否有错误
docker-compose logs backend --tail=200

# 检查 Nginx 日志
docker-compose logs nginx --tail=100
```

---

## 六、回滚指南（如升级失败）

如果升级后出现问题，可以回滚到 V1.1：

### 6.1 恢复代码

```bash
# 方式A（使用 Git）
git checkout release/v1.1
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 方式B（从备份恢复）
cd /path/to/LH_Contract_Docker
rm -rf backend frontend nginx docker-compose.yml
cp -r ~/backup_v1.1/* ./
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 6.2 恢复数据库（如需要）

```bash
# 恢复数据库
docker exec -i lh_contract_db psql -U lh_admin -d lh_contract_db < backups/backup_before_v1.2_*.sql
```

---

## 七、升级后配置优化（可选）

### 7.1 配置 CORS（生产环境）

编辑 `.env` 文件，确保 CORS 配置正确：

```bash
# 编辑 .env
nano .env

# 确保有以下配置
CORS_ORIGINS=http://192.168.72.101,http://192.168.72.101:80
```

### 7.2 重启服务应用新配置

```bash
docker-compose down
docker-compose up -d
```

---

## 八、V1.2 新功能说明

| 功能 | 说明 | 影响 |
|------|------|------|
| Refresh Token | 登录后 Token 2小时过期，可自动刷新 | 用户体验优化，无需频繁重新登录 |
| 报表缓存 | Dashboard 和报表数据缓存 5-10 分钟 | 访问速度显著提升 |
| 数据库索引 | 新增多个查询优化索引 | 查询性能提升 30-50% |
| 操作手册 | 新增用户操作文档 | 培训资料 |

---

## 九、常见问题

### Q1: 升级后无法登录？

1. 检查后端日志: `docker-compose logs backend`
2. 确认数据库连接正常
3. 清除浏览器缓存和 Cookie

### Q2: 上传的文件找不到？

确保 `uploads` 目录未被覆盖：
```bash
ls -la uploads/
# 如果为空，从备份恢复
cp -r uploads_backup_*/* uploads/
```

### Q3: 容器无法启动？

```bash
# 查看详细日志
docker-compose logs

# 检查端口占用
netstat -tlnp | grep -E '80|8000|5432|6379'

# 强制重建
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

---

## 联系支持

如遇升级问题，请联系技术支持。

---

**文档结束**

*最后更新: 2025年12月23日*
