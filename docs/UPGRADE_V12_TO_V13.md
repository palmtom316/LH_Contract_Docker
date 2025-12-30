# LH 合同管理系统升级指南
# V1.2 → V1.3 升级方案

## 📋 升级概述

| 项目 | 说明 |
|------|------|
| 源版本 | V1.2 |
| 目标版本 | V1.3 |
| 服务器 | 192.168.72.101 |
| 预计时间 | 15-30 分钟 |
| 数据保留 | ✅ 完整保留数据库和上传文件 |

---

## ⚠️ 升级前检查清单

- [ ] 确认服务器可访问 (`ssh user@192.168.72.101`)
- [ ] 确认有足够磁盘空间 (`df -h`)
- [ ] 确认数据库正常运行
- [ ] 通知用户系统将暂停服务
- [ ] 记录当前运行的容器 (`docker ps`)

---

## 📦 第一步：备份现有数据

### 1.1 SSH 登录服务器
```bash
ssh user@192.168.72.101
```

### 1.2 进入项目目录
```bash
cd /path/to/LH_Contract_Docker
# 通常是: cd ~/LH_Contract_Docker 或 cd /opt/LH_Contract_Docker
```

### 1.3 创建完整备份
```bash
# 创建备份目录
mkdir -p ~/backups/v1.2_backup_$(date +%Y%m%d)
BACKUP_DIR=~/backups/v1.2_backup_$(date +%Y%m%d)

# 备份数据库
docker exec lh_db pg_dump -U postgres lh_contract > $BACKUP_DIR/database_backup.sql
echo "✅ 数据库备份完成"

# 备份上传文件
docker cp lh_backend:/app/uploads $BACKUP_DIR/uploads_backup
echo "✅ 上传文件备份完成"

# 备份当前配置
cp .env $BACKUP_DIR/.env.backup 2>/dev/null || true
cp docker-compose.yml $BACKUP_DIR/docker-compose.yml.backup
echo "✅ 配置文件备份完成"

# 验证备份
ls -la $BACKUP_DIR/
echo "备份文件列表如上，请确认完整性"
```

---

## 🔄 第二步：拉取新版本代码

### 2.1 停止当前服务
```bash
# 停止容器（不删除数据卷）
docker-compose down
echo "✅ 服务已停止"
```

### 2.2 拉取最新代码
```bash
# 保存本地修改（如果有）
git stash

# 切换到 V1.3 分支并拉取
git fetch origin
git checkout release/V1.3
git pull origin release/V1.3

echo "✅ 代码已更新到 V1.3"
```

### 2.3 检查更新内容
```bash
# 查看更新日志
git log --oneline -10
```

---

## ⚙️ 第三步：更新配置

### 3.1 检查环境变量
```bash
# 查看当前 .env 文件
cat .env

# 确保以下关键配置存在:
# SECRET_KEY=your-secure-key-here  (V1.3 生产环境必须设置)
# DEBUG=false
# DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/lh_contract
```

### 3.2 如果 SECRET_KEY 未设置，生成一个
```bash
# 生成安全的 SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"

# 将生成的 SECRET_KEY 添加到 .env 文件
# nano .env  或  vi .env
```

### 3.3 确认配置文件
```bash
# 检查 docker-compose.yml 是否正确
cat docker-compose.yml | head -50
```

---

## 🔨 第四步：重建并启动服务

### 方案A：使用开发环境 Dockerfile（推荐用于首次升级）
```bash
# 重建镜像并启动
docker-compose build --no-cache
docker-compose up -d

echo "✅ 服务启动中..."
```

### 方案B：使用生产环境 Dockerfile（镜像更小）
```bash
# 使用生产版本 Dockerfile
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d

echo "✅ 生产环境服务启动中..."
```

---

## ✅ 第五步：验证升级

### 5.1 检查容器状态
```bash
# 查看所有容器状态
docker-compose ps

# 期望输出：所有容器状态为 Up (healthy)
```

### 5.2 检查日志
```bash
# 查看后端日志
docker-compose logs --tail=50 backend

# 查看前端日志
docker-compose logs --tail=20 frontend

# 如有错误，查看详细日志
docker-compose logs -f
```

### 5.3 验证数据完整性
```bash
# 检查数据库连接
docker exec lh_backend python -c "
from app.database import engine
import asyncio
async def test():
    async with engine.connect() as conn:
        result = await conn.execute('SELECT COUNT(*) FROM contracts_upstream')
        print(f'上游合同数量: {result.scalar()}')
asyncio.run(test())
"
```

### 5.4 验证上传文件
```bash
# 检查上传目录
docker exec lh_backend ls -la /app/uploads/

# 验证文件可访问
curl -I http://localhost/uploads/contracts/ 2>/dev/null | head -3
```

### 5.5 浏览器验证
在浏览器中访问:
- 系统首页: http://192.168.72.101
- 登录测试: 使用已有账号登录
- 数据验证: 检查合同列表、费用记录等是否完整
- 文件测试: 打开一个已上传的PDF文件

---

## 🔙 回滚方案（如升级失败）

### 6.1 停止新版本
```bash
docker-compose down
```

### 6.2 恢复代码
```bash
git checkout release/V1.2
# 或指定之前的提交
git checkout <previous_commit_hash>
```

### 6.3 恢复数据库（如需要）
```bash
# 启动数据库容器
docker-compose up -d db

# 等待数据库就绪
sleep 10

# 恢复数据库
cat $BACKUP_DIR/database_backup.sql | docker exec -i lh_db psql -U postgres lh_contract
```

### 6.4 恢复上传文件（如需要）
```bash
docker cp $BACKUP_DIR/uploads_backup/. lh_backend:/app/uploads/
```

### 6.5 重启服务
```bash
docker-compose up -d
```

---

## 📝 升级后检查清单

- [ ] 系统可正常访问
- [ ] 用户可正常登录
- [ ] 合同数据完整
- [ ] 上传的PDF文件可查看
- [ ] 财务记录正确
- [ ] 报表功能正常
- [ ] 导出功能正常

---

## 🆕 V1.3 新功能说明

| 功能 | 说明 |
|------|------|
| 安全增强 | 登录接口速率限制（5次/分钟） |
| 错误处理 | 统一的错误响应格式 |
| 审计归档 | 支持自动归档老旧审计日志 |
| 性能优化 | 新增数据库索引和虚拟滚动 |

---

## ❓ 常见问题

### Q1: SECRET_KEY 错误
**错误**: `ValueError: SECRET_KEY 环境变量在生产环境中必须设置`
**解决**: 在 `.env` 文件中添加 `SECRET_KEY=your-secure-key`

### Q2: 数据库连接失败
**错误**: `Connection refused`
**解决**: 确保数据库容器正在运行 `docker-compose up -d db`

### Q3: 上传文件无法访问
**解决**: 检查 uploads 目录权限和 Nginx 配置
```bash
docker exec lh_backend chmod -R 755 /app/uploads
```

### Q4: 前端页面空白
**解决**: 清除浏览器缓存，或使用 Ctrl+Shift+R 强制刷新

---

## 📞 支持信息

如遇问题，请保存以下信息用于排查：
```bash
# 收集诊断信息
echo "=== Docker 状态 ===" > ~/upgrade_debug.log
docker-compose ps >> ~/upgrade_debug.log
echo "=== 后端日志 ===" >> ~/upgrade_debug.log
docker-compose logs --tail=100 backend >> ~/upgrade_debug.log
echo "=== 前端日志 ===" >> ~/upgrade_debug.log
docker-compose logs --tail=50 frontend >> ~/upgrade_debug.log
```
