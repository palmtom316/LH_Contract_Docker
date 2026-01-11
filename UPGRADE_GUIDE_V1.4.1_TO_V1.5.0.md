# LH Contract Management System - 升级指南

## 版本升级：V1.4.1 → V1.5.0

> **文档版本**: v1.0  
> **发布日期**: 2026-01-11  
> **预计升级时间**: 10-20 分钟  
> **预计停机时间**: ~5 分钟

---

## 📋 目录

1. [升级概述](#升级概述)
2. [新功能特性](#新功能特性)
3. [升级前准备](#升级前准备)
4. [升级步骤](#升级步骤)
5. [验证升级](#验证升级)
6. [故障回滚](#故障回滚)
7. [常见问题](#常见问题)
8. [后续优化建议](#后续优化建议)

---

## 升级概述

### 主要变更

V1.5.0 版本引入了以下重大改进：

- **🗄️ MinIO 对象存储集成**：支持分布式文件存储，提升文件管理能力
- **🔄 Alembic 数据库迁移**：版本化数据库 schema 管理，支持可回滚的升级
- **📁 双存储支持**：兼容本地文件系统和 MinIO 对象存储
- **🔒 生产环境安全增强**：强化配置验证，防止生产环境误配置
- **📊 改进的文件追踪**：数据库字段优化，支持 `file_key` 和 `storage_provider`

### 兼容性说明

- ✅ **向后兼容**：现有文件可继续使用本地存储
- ✅ **数据零丢失**：所有现有数据和文件将完整保留
- ✅ **可选迁移**：MinIO 迁移可在升级后执行，不影响系统运行
- ✅ **可回滚**：完整备份确保可以安全回退

---

## 新功能特性

### 1. MinIO 对象存储

- **分布式存储**：支持多节点部署，提升可用性
- **S3 兼容协议**：标准化接口，易于集成
- **版本控制**：支持文件版本管理
- **存储桶隔离**：
  - `contracts-active`：活跃合同文件
  - `contracts-archive`：归档合同文件

### 2. 数据库迁移管理

- **Alembic 集成**：自动化 schema 变更
- **版本追踪**：可查看和回滚历史迁移
- **安全迁移**：自动备份，支持回滚

### 3. 双存储模式

升级后系统支持两种存储模式并存：

| 特性         | 本地存储           | MinIO 对象存储    |
| :----------- | :----------------- | :---------------- |
| 部署复杂度   | 简单               | 中等              |
| 扩展性       | 受限于单机容量     | 可横向扩展        |
| 备份方案     | 文件系统级备份     | 对象级复制        |
| 访问方式     | 直接文件路径       | S3 API            |
| 适用场景     | 小型部署，快速启动 | 大规模部署，高可用 |

---

## 升级前准备

### 1. 系统要求

#### 最低配置

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 7+) / macOS
- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **磁盘空间**: 至少为当前数据库和文件总大小的 2 倍（用于备份）
- **内存**: 建议 4GB+

#### 检查命令

```bash
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本
docker-compose --version

# 检查磁盘空间
df -h .

# 检查当前数据大小
du -sh ./backend/uploads
docker-compose exec db psql -U lh_admin -d lh_contract_db -c "\l+"
```

### 2. 备份当前系统

> ⚠️ **重要**：升级脚本会自动执行备份，但建议提前手动创建额外备份作为双重保险。

#### 手动备份步骤

```bash
# 1. 创建备份目录
mkdir -p ./manual_backups/pre_v1.5_$(date +%Y%m%d)
BACKUP_DIR="./manual_backups/pre_v1.5_$(date +%Y%m%d)"

# 2. 备份数据库
docker-compose exec -T db pg_dump -U lh_admin lh_contract_db > "$BACKUP_DIR/database.sql"

# 3. 备份文件
cp -r ./backend/uploads "$BACKUP_DIR/uploads_backup"

# 4. 备份配置
cp .env "$BACKUP_DIR/.env.backup"
cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml.backup"

# 5. 验证备份完整性
ls -lh "$BACKUP_DIR"
```

### 3. 配置检查清单

在执行升级前，请确认以下配置项：

- [ ] `.env` 文件中 `DEBUG=false`（生产环境必须）
- [ ] `SECRET_KEY` 已设置为强密码（非默认值）
- [ ] `POSTGRES_PASSWORD` 已设置为强密码（非默认值）
- [ ] 网络连接正常，可访问 Docker Hub
- [ ] 当前没有用户在线操作系统（建议维护窗口执行）

---

## 升级步骤

### 方式一：自动化升级（推荐）

使用提供的升级脚本 `production_upgrade_1.4.1_to_1.5.0.sh` 进行自动化升级。

#### 1. 下载并准备脚本

```bash
# 进入项目根目录
cd /path/to/LH_Contract_Docker

# 检查脚本是否存在
ls -l scripts/production_upgrade_1.4.1_to_1.5.0.sh

# 添加执行权限
chmod +x scripts/production_upgrade_1.4.1_to_1.5.0.sh
```

#### 2. 执行升级

```bash
# 执行升级脚本
./scripts/production_upgrade_1.4.1_to_1.5.0.sh
```

#### 3. 升级脚本执行流程

脚本将按以下步骤自动执行：

1. **前置检查** ✓
   - 检查 Docker 和 Docker Compose 是否安装
   - 验证 `.env` 文件存在
   - 验证生产环境配置（DEBUG、密钥等）

2. **创建备份** ✓
   - 导出数据库到 `./backups/upgrade_YYYYMMDD_HHMMSS/database_backup.sql`
   - 备份 `./backend/uploads` 目录
   - 备份 `.env` 和 `docker-compose.yml` 文件

3. **验证备份** ✓
   - 检查备份文件大小
   - 统计备份文件数量

4. **更新配置** ✓
   - 添加 `ENV=production` 环境变量
   - 添加 MinIO 配置（如不存在）

5. **数据库迁移** ✓
   - 启动数据库服务
   - 运行 Alembic 迁移：`alembic upgrade head`
   - 验证迁移成功

6. **设置 MinIO** ✓
   - 启动 MinIO 服务
   - 创建存储桶：`contracts-active`, `contracts-archive`

7. **文件迁移选项** 📁
   ```
   Options:
     1) Keep files local (no migration) - RECOMMENDED for now
     2) Migrate files to MinIO (can be done later)
     3) Run dry-run to preview migration
   ```
   
   **建议**：首次升级选择 **选项 1**，保持文件本地存储，等系统稳定后再考虑迁移

8. **重建服务** ✓
   - 重新构建 backend 和 frontend 镜像
   - 重启所有服务

9. **验证升级** ✓
   - 检查后端健康状态
   - 验证数据库连接
   - 验证文件访问

#### 4. 交互式选项说明

##### 文件迁移选择

```bash
Choose option (1/2/3):
```

- **选项 1**（推荐）：保持文件在本地存储，不迁移到 MinIO
  - 优点：零风险，系统升级快速完成
  - 适用：首次升级，优先保证系统稳定
  
- **选项 2**：立即迁移文件到 MinIO
  - 会先运行 dry-run 预览
  - 需确认后才执行实际迁移
  - 适用：有充足时间，需要立即使用 MinIO 功能
  
- **选项 3**：仅运行 dry-run 模拟
  - 预览迁移计划，不实际迁移文件
  - 适用：了解迁移影响，规划后续操作

---

### 方式二：手动升级

如果自动脚本遇到问题，可以按以下步骤手动升级：

#### 1. 停止服务

```bash
docker-compose down
```

#### 2. 更新代码

```bash
git pull origin main
```

#### 3. 更新环境配置

编辑 `.env` 文件，添加以下配置：

```bash
# Environment
ENV=production

# MinIO Configuration
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=${MINIO_ROOT_USER:-minioadmin}
MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD:-minioadmin123}
MINIO_SECURE=false
MINIO_BUCKET_CONTRACTS=contracts-active
```

#### 4. 启动数据库和后端

```bash
docker-compose up -d db redis
sleep 5
docker-compose up -d backend
sleep 10
```

#### 5. 运行数据库迁移

```bash
docker-compose exec backend alembic upgrade head
```

#### 6. 启动 MinIO

```bash
docker-compose up -d minio
sleep 10
```

#### 7. 创建 MinIO 存储桶

```bash
docker-compose exec backend python -c "
from minio import Minio
import os

client = Minio(
    os.getenv('MINIO_ENDPOINT', 'minio:9000'),
    access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
    secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
    secure=False
)

for bucket in ['contracts-active', 'contracts-archive']:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f'Created bucket: {bucket}')
"
```

#### 8. 重建并启动所有服务

```bash
docker-compose build --no-cache backend frontend
docker-compose up -d
```

---

## 验证升级

### 1. 服务健康检查

```bash
# 检查所有容器状态
docker-compose ps

# 预期输出：所有服务状态为 "Up"
```

### 2. 后端 API 检查

```bash
# 检查健康端点
curl http://localhost:8000/health

# 预期输出：包含 "healthy" 的 JSON 响应
```

### 3. 数据库连接检查

```bash
# 测试数据库连接
docker-compose exec db psql -U lh_admin -d lh_contract_db -c "SELECT version();"

# 检查迁移版本
docker-compose exec backend alembic current
```

### 4. 文件访问检查

```bash
# 检查上传目录
docker-compose exec backend ls -la /app/uploads

# 统计文件数量
docker-compose exec backend find /app/uploads -type f | wc -l
```

### 5. MinIO 服务检查

```bash
# 访问 MinIO 管理界面
# 浏览器打开: http://localhost:9001
# 默认账号: minioadmin / minioadmin123

# 或通过 API 检查
curl http://localhost:9000/minio/health/live
```

### 6. 前端功能测试

在浏览器中访问系统，测试以下功能：

- [ ] 登录功能正常
- [ ] 合同列表显示正常
- [ ] 合同详情可以查看
- [ ] 文件上传功能正常
- [ ] 已上传文件可以预览和下载
- [ ] 数据统计图表显示正常

### 7. 日志检查

```bash
# 查看后端日志
docker-compose logs -f backend

# 查看数据库日志
docker-compose logs db

# 查看 MinIO 日志
docker-compose logs minio
```

---

## 故障回滚

如果升级后遇到严重问题，可以按以下步骤回滚到 V1.4.1：

### 自动备份回滚

升级脚本创建的备份位于 `./backups/upgrade_YYYYMMDD_HHMMSS/`

```bash
# 1. 设置备份目录变量（替换为实际备份目录）
BACKUP_DIR="./backups/upgrade_20260111_123456"

# 2. 停止所有服务
docker-compose down

# 3. 恢复数据库
docker-compose up -d db
sleep 5
docker-compose exec -T db psql -U lh_admin -d lh_contract_db < "$BACKUP_DIR/database_backup.sql"

# 4. 恢复文件
rm -rf ./backend/uploads
cp -r "$BACKUP_DIR/uploads_backup" ./backend/uploads

# 5. 恢复配置
cp "$BACKUP_DIR/.env.backup" .env
cp "$BACKUP_DIR/docker-compose.yml.backup" docker-compose.yml

# 6. 重启服务
docker-compose up -d

# 7. 验证回滚
docker-compose ps
curl http://localhost:8000/health
```

### 手动备份回滚

如果使用了手动备份：

```bash
# 使用手动备份目录
BACKUP_DIR="./manual_backups/pre_v1.5_20260111"

# 执行相同的回滚步骤（如上）
```

### 回滚验证

- [ ] 所有服务正常运行
- [ ] 可以正常登录
- [ ] 合同数据完整
- [ ] 文件可以正常访问
- [ ] 系统版本显示为 V1.4.1

---

## 常见问题

### Q1: 升级过程中断怎么办？

**A**: 升级脚本设置了 `set -e`，遇到错误会自动停止。查看日志文件 `upgrade_YYYYMMDD_HHMMSS.log`，定位错误原因后：

- 如果是网络问题，重新运行脚本
- 如果是配置问题，修正后重新运行
- 如果不确定，执行回滚操作

### Q2: MinIO 迁移失败，但系统已升级，怎么办？

**A**: 文件迁移是可选的，系统仍可使用本地存储正常运行：

```bash
# 1. 跳过 MinIO 迁移，系统继续使用本地文件
# 2. 后续可以手动执行迁移
docker-compose exec backend python /app/scripts/migrate_to_minio.py --dry-run
docker-compose exec backend python /app/scripts/migrate_to_minio.py
```

### Q3: 数据库迁移报错 "relation already exists"

**A**: 可能是迁移状态不一致，检查迁移历史：

```bash
# 查看当前迁移版本
docker-compose exec backend alembic current

# 查看迁移历史
docker-compose exec backend alembic history

# 如果需要，标记特定迁移为已执行（不实际运行 SQL）
docker-compose exec backend alembic stamp head
```

### Q4: 前端无法连接后端

**A**: 检查以下配置：

```bash
# 1. 检查后端是否启动
docker-compose logs backend

# 2. 检查环境变量
docker-compose exec backend env | grep -E "ENV|DEBUG"

# 3. 确保 .env 中配置正确
cat .env | grep -E "FRONTEND_URL|BACKEND_URL"
```

### Q5: MinIO 管理界面无法访问

**A**: 检查端口和服务状态：

```bash
# 检查 MinIO 容器状态
docker-compose ps minio

# 检查端口映射
docker-compose port minio 9001

# 检查日志
docker-compose logs minio

# 重启 MinIO
docker-compose restart minio
```

### Q6: 升级后文件预览失败

**A**: 检查文件路径和权限：

```bash
# 检查文件目录权限
docker-compose exec backend ls -la /app/uploads

# 检查数据库中的文件路径
docker-compose exec db psql -U lh_admin -d lh_contract_db -c "
  SELECT id, contract_file_path, storage_provider 
  FROM contracts_upstream 
  WHERE contract_file_path IS NOT NULL 
  LIMIT 5;
"

# 如果路径不正确，运行路径验证脚本
docker-compose exec backend python -c "
from pathlib import Path
upload_dir = Path('/app/uploads')
for f in upload_dir.rglob('*'):
    if f.is_file():
        print(f'✓ {f.relative_to(upload_dir)}')
"
```

---

## 后续优化建议

### 1. MinIO 文件迁移（可选）

如果升级时选择了保持本地存储，可以在系统稳定后执行迁移：

```bash
# 1. 运行 dry-run 预览
docker-compose exec backend python /app/scripts/migrate_to_minio.py --dry-run

# 2. 查看迁移报告，确认无误后执行
docker-compose exec backend python /app/scripts/migrate_to_minio.py

# 3. 验证迁移
docker-compose exec backend python /app/scripts/verify_migration.py
```

### 2. 性能监控

```bash
# 监控容器资源使用
docker stats

# 监控日志大小
du -sh ./logs

# 设置日志轮转（推荐）
# 编辑 docker-compose.yml，添加日志配置
```

### 3. 安全加固

```bash
# 更改 MinIO 默认密码
# 编辑 .env 文件：
MINIO_ROOT_USER=your_admin_user
MINIO_ROOT_PASSWORD=your_strong_password_here

# 重启 MinIO
docker-compose up -d minio
```

### 4. 备份策略

建议设置定期备份：

```bash
# 使用 scripts/backup.sh 脚本
./scripts/backup.sh

# 或设置 cron job（每天凌晨 2 点）
0 2 * * * cd /path/to/LH_Contract_Docker && ./scripts/backup.sh
```

### 5. 数据库优化

```bash
# 运行 VACUUM ANALYZE 优化数据库
docker-compose exec db psql -U lh_admin -d lh_contract_db -c "VACUUM ANALYZE;"

# 检查表大小
docker-compose exec db psql -U lh_admin -d lh_contract_db -c "
  SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables
  WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## 技术支持

### 升级日志位置

- **升级日志**: `./upgrade_YYYYMMDD_HHMMSS.log`
- **备份位置**: `./backups/upgrade_YYYYMMDD_HHMMSS/`
- **应用日志**: `docker-compose logs`

### 相关文档

- [Alembic 设置指南](./ALEMBIC_SETUP_GUIDE.md)
- [部署指南](./DEPLOYMENT.md)
- [运维手册](./OPERATIONS_MANUAL.md)
- [V1.5 升级指令书](./1.5%20版升级指令书.md)

### 问题反馈

如遇到未覆盖的问题，请：

1. 保留升级日志文件
2. 导出容器日志：`docker-compose logs > full_logs.txt`
3. 记录问题复现步骤
4. 联系技术支持团队

---

## 附录

### A. 升级脚本参数说明

升级脚本支持的环境变量：

```bash
# 数据库配置
POSTGRES_USER=lh_admin          # 数据库用户名
POSTGRES_DB=lh_contract_db      # 数据库名称
POSTGRES_PASSWORD=your_password # 数据库密码

# MinIO 配置
MINIO_ROOT_USER=minioadmin      # MinIO 管理员用户名
MINIO_ROOT_PASSWORD=minioadmin123  # MinIO 管理员密码
```

### B. 数据库 Schema 变更

V1.5.0 添加的数据库字段：

```sql
-- contracts_upstream, contracts_downstream, contracts_management 表
ALTER TABLE contracts_upstream ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(20) DEFAULT 'local';
ALTER TABLE contracts_upstream ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);

-- ZeroHourLabor 表（用于派工单附件）
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS dispatch_file_key VARCHAR(500);
```

### C. 文件命名规范

MinIO 中的文件 key 格式：

```
contracts/{contract_type}/{year}/{month}/{filename}

示例：
contracts/upstream/2026/01/contract_12345_20260111.pdf
```

### D. 检查清单

升级完成后的验收清单：

**功能测试**
- [ ] 用户登录正常
- [ ] 合同列表加载正常
- [ ] 合同详情显示正确
- [ ] 文件上传功能正常
- [ ] 文件预览功能正常
- [ ] 文件下载功能正常
- [ ] 数据统计准确
- [ ] 搜索功能正常

**服务检查**
- [ ] Database 服务运行正常
- [ ] Redis 服务运行正常
- [ ] Backend 服务运行正常
- [ ] Frontend 服务运行正常
- [ ] MinIO 服务运行正常
- [ ] Nginx 服务运行正常（如使用）

**数据完整性**
- [ ] 合同数量与升级前一致
- [ ] 文件数量与升级前一致
- [ ] 用户账号数据完整
- [ ] 权限配置正确

**性能基准**
- [ ] 页面加载时间与升级前相当或更快
- [ ] API 响应时间正常
- [ ] 数据库查询性能正常

---

**文档版本**: v1.0  
**最后更新**: 2026-01-11  
**维护者**: LH Contract Management Team
