# 安全最佳实践指南

**项目**: LH 合同管理系统
**版本**: 1.7.1
**更新日期**: 2026-06-24

---

## 目录

1. [环境变量安全](#1-环境变量安全)
2. [密码策略](#2-密码策略)
3. [网络安全](#3-网络安全)
4. [数据保护](#4-数据保护)
5. [访问控制](#5-访问控制)
6. [审计日志](#6-审计日志)
7. [定期维护](#7-定期维护)
8. [应急响应](#8-应急响应)

---

## 1. 环境变量安全

### 1.1 密钥生成

**切勿使用默认密钥或简单密码！**

生成强密钥：
```bash
# 生成 SECRET_KEY、INIT_ADMIN_TOKEN
python -c "import secrets; print(secrets.token_urlsafe(64))"

# 或使用 OpenSSL
openssl rand -base64 64
```

### 1.2 环境变量管理

```bash
# ✅ 正确做法
# .env 和 .env.production 文件已在 .gitignore 中
SECRET_KEY=<64字节随机密钥>
POSTGRES_PASSWORD=<16+字符强密码>

# ❌ 错误做法
# 不要使用简单密码
SECRET_KEY=123456
POSTGRES_PASSWORD=password

# 不要在代码中硬编码
# 不要提交 .env 或 .env.production 文件到 Git
```

### 1.3 验证配置安全性

```bash
# 检查敏感环境文件是否被 Git 跟踪
git ls-files .env .env.production

# 应该无输出，如果有输出则执行：
git rm --cached --ignore-unmatch .env .env.production
```

---

## 2. 密码策略

### 2.1 管理员密码要求

- **最低长度**: 12 字符
- **复杂度**: 包含大小写字母、数字、特殊字符
- **禁止**: 字典词汇、连续字符、重复密码

**示例**：
```
✅ 强密码: Xk9#mP2$vL8@wQ5!
❌ 弱密码: admin123, Password1, 123456
```

### 2.2 数据库密码

```bash
# PostgreSQL 密码（16+ 字符）
POSTGRES_PASSWORD=$(openssl rand -base64 24)

# MinIO 密码（8+ 字符）
MINIO_ROOT_PASSWORD=$(openssl rand -base64 16)
```

### 2.3 密码轮换

- **管理员密码**: 每 90 天更换
- **数据库密码**: 每 180 天更换
- **API 密钥**: 每年更换或在离职时立即更换

---

## 3. 网络安全

### 3.1 防火墙配置

**仅开放必要端口**：

```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# 验证规则
sudo ufw status
```

### 3.2 内部服务隔离

Docker Compose 已配置内部网络，确保以下端口**不对外开放**：

- **5432** (PostgreSQL)
- **6379** (Redis)
- **9000** (MinIO API)
- **8000** (Backend - 通过 Nginx 代理)

### 3.3 HTTPS 配置

**生产环境必须启用 HTTPS**：

```bash
# 使用 Let's Encrypt
sudo certbot --nginx -d your-domain.com

# 验证证书
sudo certbot certificates
```

### 3.4 CORS 配置

```bash
# .env.production 文件中设置
CORS_ORIGINS=https://your-domain.com

# ❌ 不要使用通配符
CORS_ORIGINS=*  # 危险！
```

---

## 4. 数据保护

### 4.1 数据库备份

**自动化备份脚本**：

```bash
#!/bin/bash
# /opt/lh-contract/backup-db.sh

BACKUP_DIR="/var/backups/lh-contract/db"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30
PROJECT_DIR="/opt/lh-contract/LH_Contract_Docker"
CONTAINER_NAME="lh_contract_db_prod"

mkdir -p $BACKUP_DIR
set -a
. "$PROJECT_DIR/.env.production"
set +a

# 备份数据库
docker exec "$CONTAINER_NAME" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | \
  gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 加密备份（可选）
gpg --symmetric --cipher-algo AES256 $BACKUP_DIR/db_$DATE.sql.gz

# 清理旧备份
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] Backup completed: db_$DATE.sql.gz"
```

**配置定时任务**：
```bash
sudo crontab -e

# 每天凌晨 3 点备份
0 3 * * * /opt/lh-contract/backup-db.sh >> /var/log/lh-backup.log 2>&1
```

### 4.2 MinIO 数据备份

```bash
# 备份 MinIO 存储
docker run --rm \
  -v lh_contract_docker_minio_data:/data \
  -v /var/backups/lh-contract/minio:/backup \
  alpine tar czf /backup/minio_$(date +%Y%m%d).tar.gz -C /data .
```

### 4.3 备份存储安全

- **异地备份**: 将备份文件同步到远程服务器或云存储
- **加密备份**: 使用 GPG 或 AES 加密备份文件
- **访问控制**: 备份目录权限设置为 700

```bash
# 设置备份目录权限
sudo chmod 700 /var/backups/lh-contract
sudo chown root:root /var/backups/lh-contract
```

---

## 5. 访问控制

### 5.1 最小权限原则

- **管理员账户**: 仅授予必要人员
- **普通用户**: 根据职责分配权限
- **审计员**: 只读访问审计日志

### 5.2 SSH 安全

```bash
# 禁用 root 登录
sudo nano /etc/ssh/sshd_config

# 修改以下配置
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
Port 2222  # 更改默认端口

# 重启 SSH
sudo systemctl restart sshd
```

### 5.3 Docker 权限

```bash
# 避免使用 root 运行容器
# 后端生产镜像已配置非 root 用户

# 限制 Docker Socket 访问
sudo chmod 660 /var/run/docker.sock
```

---

## 6. 审计日志

### 6.1 启用日志记录

系统已内置审计日志，记录以下操作：

- 用户登录/登出
- 合同创建/修改/删除
- 财务记录变更
- 文件上传/下载
- 权限变更

### 6.2 日志查看

```bash
# 通过 API 查看审计日志（管理员权限）
curl -H "Authorization: Bearer <token>" \
  "http://localhost/api/v1/audit/?page_size=50"
```

### 6.3 日志保留

- **在线日志**: 保留 90 天
- **归档日志**: 保留 3 年（根据合规要求）
- **敏感操作**: 永久保留

---

## 7. 定期维护

### 7.1 安全更新检查清单

**每月**：
- [ ] 检查并安装系统安全更新
  ```bash
  sudo apt-get update
  sudo apt-get upgrade
  ```

- [ ] 更新 Docker 镜像
  ```bash
  docker compose -f docker-compose.prod.yml pull
  docker compose --env-file .env.production -f docker-compose.prod.yml up -d
  ```

- [ ] 检查后端依赖漏洞
  ```bash
  cd backend
  pip list --outdated
  # 或使用 safety
  pip install safety
  safety check
  ```

- [ ] 检查前端依赖漏洞
  ```bash
  cd frontend
  npm audit
  npm audit fix
  ```

**每季度**：
- [ ] 审查用户权限
- [ ] 检查异常登录记录
- [ ] 测试备份恢复流程
- [ ] 审查审计日志

**每年**：
- [ ] 更换主要密钥
- [ ] 进行渗透测试
- [ ] 更新安全策略
- [ ] 培训安全意识

### 7.2 漏洞扫描

```bash
# 使用 Trivy 扫描 Docker 镜像
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image lh_contract_backend:latest

# 使用 OWASP Dependency-Check
# https://owasp.org/www-project-dependency-check/
```

---

## 8. 应急响应

### 8.1 安全事件响应流程

**发现安全事件时**：

1. **立即隔离**
   ```bash
   # 停止受影响的服务
   docker compose -f docker-compose.prod.yml stop

   # 断开网络（极端情况）
   sudo ufw deny in from any to any
   ```

2. **保留证据**
   ```bash
   # 导出所有日志
   docker compose -f docker-compose.prod.yml logs > incident_logs_$(date +%Y%m%d).txt

   # 备份当前数据库
   set -a
   . .env.production
   set +a
   docker exec lh_contract_db_prod pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > incident_db_$(date +%Y%m%d).sql
   ```

3. **通知相关人员**
   - 技术负责人
   - 安全团队
   - 管理层（如涉及数据泄露）

4. **分析和修复**
   - 分析攻击向量
   - 修复漏洞
   - 更换受影响的密钥

5. **恢复服务**
   ```bash
   # 从备份恢复（如需要）
   # 启动服务
   docker compose --env-file .env.production -f docker-compose.prod.yml up -d
   ```

6. **事后总结**
   - 记录事件详情
   - 更新安全策略
   - 加强监控

### 8.2 常见安全事件

**密码泄露**：
```bash
# 1. 立即重置受影响账户密码
# 2. 吊销所有 JWT 令牌
docker compose -f docker-compose.prod.yml exec redis redis-cli FLUSHDB

# 3. 更换 SECRET_KEY
# 4. 通知所有用户重新登录
```

**SQL 注入攻击**：
```bash
# 1. 检查审计日志
# 2. 恢复到攻击前的备份
# 3. 更新代码修复漏洞
# 4. 加强输入验证
```

**DDoS 攻击**：
```bash
# 1. 启用 Cloudflare 或其他 DDoS 防护
# 2. 配置速率限制
# 3. 联系 ISP 或云服务商
```

---

## 附录：安全检查脚本

```bash
#!/bin/bash
# security-check.sh - 安全配置检查脚本

echo "=== LH 合同管理系统安全检查 ==="
echo ""

# 检查 .env.production 文件权限
ENV_FILE=".env.production"
if [ -f "$ENV_FILE" ]; then
    PERM=$(stat -c %a "$ENV_FILE")
    if [ "$PERM" != "600" ]; then
        echo "⚠️  警告: $ENV_FILE 文件权限不安全 ($PERM)，建议设置为 600"
        echo "   修复: chmod 600 $ENV_FILE"
    else
        echo "✅ $ENV_FILE 文件权限正确"
    fi
fi

# 检查 DEBUG 模式
if grep -q "DEBUG=true" "$ENV_FILE" 2>/dev/null; then
    echo "⚠️  警告: DEBUG 模式已启用，生产环境应设置为 false"
else
    echo "✅ DEBUG 模式已关闭"
fi

# 检查 SECRET_KEY
if grep -q "SECRET_KEY=<" "$ENV_FILE" 2>/dev/null; then
    echo "❌ 错误: SECRET_KEY 未设置或使用默认值"
else
    echo "✅ SECRET_KEY 已配置"
fi

# 检查容器是否运行
if docker compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "✅ Docker 容器正在运行"
else
    echo "⚠️  警告: Docker 容器未运行"
fi

# 检查防火墙
if sudo ufw status | grep -q "Status: active"; then
    echo "✅ 防火墙已启用"
else
    echo "⚠️  警告: 防火墙未启用"
fi

# 检查备份
BACKUP_COUNT=$(find /var/backups/lh-contract -name "db_*.sql.gz" 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 0 ]; then
    echo "✅ 找到 $BACKUP_COUNT 个数据库备份"
else
    echo "⚠️  警告: 未找到数据库备份"
fi

echo ""
echo "=== 检查完成 ==="
```

**使用方法**：
```bash
chmod +x security-check.sh
./security-check.sh
```

---

## 联系方式

如发现安全漏洞，请立即联系：

- **安全联系人**: 内部安全/运维渠道

**请勿在公开渠道（如 GitHub Issues）报告安全漏洞！**

---

**文档版本**: 1.0
**最后更新**: 2026-06-24
**维护者**: 安全团队
