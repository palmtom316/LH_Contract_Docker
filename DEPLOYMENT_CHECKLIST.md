# 部署前检查清单 - LH Contract Management System

## 检查日期: 2025-12-18

---

## 1. Alembic 数据库迁移检查

### ❌ **重大问题：缺少 Alembic 配置**

**问题描述：**
- 项目中**没有找到 Alembic 配置文件**（alembic.ini, alembic/ 目录）
- 当前使用 `Base.metadata.create_all()` 直接创建表结构
- 存在手动 SQL 迁移文件（`backend/migrations/*.sql`），但被 .gitignore 忽略

**风险：**
- ⚠️ **高风险**：生产环境数据库结构变更无法追踪和回滚
- ⚠️ **高风险**：多环境部署时可能出现数据库结构不一致
- ⚠️ **中风险**：无法进行增量数据库迁移

**建议修复方案：**

#### 方案 1：集成 Alembic（推荐）
```bash
# 1. 安装 Alembic
cd backend
pip install alembic

# 2. 初始化 Alembic
alembic init alembic

# 3. 配置 alembic.ini 和 env.py
# 4. 创建初始迁移
alembic revision --autogenerate -m "Initial migration"

# 5. 应用迁移
alembic upgrade head
```

#### 方案 2：保持现状（仅适用于小型项目）
- 确保所有环境使用相同的模型定义
- 在部署文档中明确说明数据库初始化流程
- 定期备份数据库

---

## 2. 端口配置检查

### ✅ **数据库端口 (PostgreSQL: 5432)**

| 配置文件 | 端口配置 | 状态 | 备注 |
|---------|---------|------|------|
| `docker-compose.yml` | `5432:5432` | ✅ 正确 | 开发环境映射到主机 |
| `docker-compose.prod.yml` | 未映射 | ✅ 正确 | 生产环境仅内网访问 |
| `.env.example` | `@db:5432` | ✅ 正确 | 容器内部访问 |
| `backend/app/config.py` | `@db:5432` | ✅ 正确 | 默认配置 |
| `.env` (本地) | `@localhost:5432` | ⚠️ 注意 | 本地开发配置 |
| `backend/.env` (本地) | `@localhost:5432` | ⚠️ 注意 | 本地开发配置 |

**问题：**
- `.env` 和 `backend/.env` 使用 `localhost:5432`，这是本地开发配置
- 这些文件被 .gitignore 忽略，但需要确保生产环境使用正确的 `db:5432`

**建议：**
```bash
# 生产环境部署时，确保 .env 文件中使用容器服务名
DATABASE_URL=postgresql+asyncpg://lh_admin:STRONG_PASSWORD@db:5432/lh_contract_db
```

---

### ✅ **后端 API 端口 (FastAPI: 8000)**

| 配置文件 | 端口配置 | 状态 | 备注 |
|---------|---------|------|------|
| `docker-compose.yml` | `8000:8000` | ✅ 正确 | 开发环境映射 |
| `docker-compose.prod.yml` | 未映射 | ✅ 正确 | 通过 Nginx 反向代理 |
| `backend/Dockerfile` | `EXPOSE 8000` | ✅ 正确 | 容器内部端口 |
| `backend/app/main.py` | `port=8000` | ✅ 正确 | Uvicorn 配置 |
| `frontend/vite.config.js` | `target: 'http://localhost:8000'` | ⚠️ 注意 | 开发环境代理 |

**问题：**
- 前端 Vite 配置中硬编码了 `localhost:8000`
- 生产环境应通过 Nginx 反向代理，不直接访问 8000 端口

**状态：** ✅ 配置正确（生产环境使用 Nginx）

---

### ⚠️ **前端端口配置不一致**

| 配置文件 | 端口配置 | 状态 | 备注 |
|---------|---------|------|------|
| `docker-compose.yml` | `3000:3000` | ⚠️ 冲突 | Docker 配置使用 3000 |
| `frontend/Dockerfile` | `EXPOSE 3000` | ⚠️ 冲突 | Dockerfile 使用 3000 |
| `frontend/vite.config.js` | `port: 5173` | ⚠️ 冲突 | Vite 配置使用 5173 |
| `.env.example` | `CORS_ORIGINS=...3000...` | ⚠️ 冲突 | CORS 配置使用 3000 |

**问题：**
- **端口不一致**：Docker 配置使用 3000，但 Vite 默认配置使用 5173
- 这会导致容器启动失败或端口冲突

**建议修复：**

#### 选项 1：统一使用 3000 端口（推荐）
保持 Docker 配置不变，Vite 配置已经在 Dockerfile CMD 中覆盖为 3000

#### 选项 2：统一使用 5173 端口
```yaml
# docker-compose.yml
frontend:
  ports:
    - "5173:5173"
```

```dockerfile
# frontend/Dockerfile
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
```

**当前状态：** ✅ 实际运行时使用 3000（Dockerfile CMD 覆盖）

---

### ✅ **Redis 端口 (6379)**

| 配置文件 | 端口配置 | 状态 | 备注 |
|---------|---------|------|------|
| `docker-compose.yml` | `6379:6379` | ✅ 正确 | 开发环境映射 |
| `docker-compose.prod.yml` | 未映射 | ✅ 正确 | 仅内网访问 |
| `backend/app/config.py` | `redis://localhost:6379/0` | ⚠️ 注意 | 默认配置 |

**建议：**
```bash
# 生产环境 .env 配置
REDIS_URL=redis://redis:6379/0
```

---

## 3. 环境变量配置检查

### ⚠️ **关键安全配置**

| 环境变量 | 开发环境 | 生产环境要求 | 状态 |
|---------|---------|------------|------|
| `SECRET_KEY` | 自动生成 | ❌ **必须设置** | 需要配置 |
| `POSTGRES_PASSWORD` | 默认密码 | ❌ **必须修改** | 需要修改 |
| `DEBUG` | `false` | ✅ `false` | 正确 |
| `DATABASE_URL` | 包含密码 | ❌ **必须修改** | 需要修改 |

**生产环境必须配置：**

```bash
# .env.production
SECRET_KEY=<使用以下命令生成>
# python -c "import secrets; print(secrets.token_urlsafe(64))"

POSTGRES_USER=lh_admin
POSTGRES_PASSWORD=<强密码，至少16位，包含大小写字母、数字、特殊字符>
POSTGRES_DB=lh_contract_db

DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
REDIS_URL=redis://redis:6379/0

DEBUG=false
CORS_ORIGINS=<生产环境域名>
```

---

## 4. Docker 配置检查

### ✅ **开发环境 (docker-compose.yml)**

**优点：**
- ✅ 端口映射完整，便于调试
- ✅ 包含健康检查
- ✅ 使用卷挂载，支持热重载

**问题：**
- ⚠️ 包含默认密码（开发环境可接受）
- ⚠️ `--reload` 模式不适合生产环境

---

### ✅ **生产环境 (docker-compose.prod.yml)**

**优点：**
- ✅ 使用 Nginx 反向代理
- ✅ 配置了资源限制
- ✅ 配置了日志轮转
- ✅ 健康检查完善
- ✅ 数据库和 Redis 不对外暴露端口

**问题：**
- ⚠️ 需要单独的 `.env.production` 文件
- ⚠️ 需要构建前端生产版本（`frontend/dist`）
- ⚠️ 需要 Nginx 配置文件（`nginx/nginx.conf`）
- ⚠️ 需要 SSL 证书（`nginx/ssl/`）

---

## 5. 数据库初始化流程检查

### 当前流程：

```python
# backend/app/database.py
async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

**问题：**
- ⚠️ `create_all()` 不会修改已存在的表结构
- ⚠️ 无法处理字段重命名、类型变更等复杂迁移
- ⚠️ 无法回滚数据库变更

**建议：**
- 集成 Alembic 进行数据库迁移管理
- 或者在部署文档中明确说明数据库初始化和更新流程

---

## 6. 前后端通信配置检查

### ✅ **CORS 配置**

```python
# backend/app/config.py
CORS_ORIGINS: str = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000"
)
```

**生产环境需要修改：**
```bash
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

### ✅ **前端 API 配置**

```javascript
// frontend/vite.config.js
proxy: {
    '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
    }
}
```

**状态：** ✅ 开发环境配置正确，生产环境通过 Nginx 代理

---

## 7. 文件上传配置检查

### ✅ **上传目录配置**

```python
# backend/app/config.py
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
```

**Docker 卷挂载：**
```yaml
# docker-compose.yml
volumes:
  - ./backend/uploads:/app/uploads  # 开发环境

# docker-compose.prod.yml
volumes:
  - ./uploads:/app/uploads  # 生产环境
```

**状态：** ✅ 配置正确

---

## 8. 部署前必做清单

### 🔴 **高优先级（必须完成）**

- [ ] **集成 Alembic** 或明确数据库迁移策略
- [ ] **生成强 SECRET_KEY** 并配置到 `.env.production`
- [ ] **修改数据库密码** 为强密码
- [ ] **配置生产环境 CORS_ORIGINS** 为实际域名
- [ ] **创建 `.env.production`** 文件（不要提交到 Git）
- [ ] **构建前端生产版本** (`npm run build`)
- [ ] **配置 Nginx** 反向代理和 SSL 证书
- [ ] **测试健康检查端点** (`/health`, `/health/detailed`)

### 🟡 **中优先级（建议完成）**

- [ ] 配置数据库备份策略
- [ ] 配置日志收集和监控
- [ ] 压力测试和性能优化
- [ ] 配置防火墙规则
- [ ] 准备回滚方案

### 🟢 **低优先级（可选）**

- [ ] 配置 CI/CD 自动部署
- [ ] 配置容器编排（Kubernetes）
- [ ] 配置 CDN 加速静态资源
- [ ] 配置多环境部署（staging, production）

---

## 9. 端口总结表

| 服务 | 开发环境端口 | 生产环境端口 | 访问方式 |
|------|------------|------------|---------|
| PostgreSQL | 5432 (映射) | 5432 (内网) | 容器内 `db:5432` |
| Redis | 6379 (映射) | 6379 (内网) | 容器内 `redis:6379` |
| Backend API | 8000 (映射) | 8000 (内网) | 通过 Nginx 代理 |
| Frontend | 3000 (映射) | 80/443 | 通过 Nginx 提供静态文件 |
| Nginx | - | 80, 443 | 公网访问 |

---

## 10. 关键配置文件检查

### ✅ **已存在的配置文件**
- `docker-compose.yml` - 开发环境配置
- `docker-compose.prod.yml` - 生产环境配置
- `.env.example` - 环境变量模板
- `backend/Dockerfile` - 后端容器配置
- `frontend/Dockerfile` - 前端容器配置

### ❌ **缺少的配置文件**
- `.env.production` - 生产环境变量（需要创建）
- `nginx/nginx.conf` - Nginx 配置（需要创建）
- `nginx/ssl/` - SSL 证书目录（需要创建）
- `alembic.ini` - Alembic 配置（建议创建）
- `alembic/` - Alembic 迁移目录（建议创建）

---

## 11. 建议的部署流程

### 步骤 1：准备环境
```bash
# 1. 克隆代码到生产服务器
git clone <repository> /opt/lh_contract

# 2. 创建生产环境配置
cd /opt/lh_contract
cp .env.example .env.production
# 编辑 .env.production，设置强密码和密钥

# 3. 创建必要的目录
mkdir -p nginx/ssl uploads backups logs
```

### 步骤 2：配置 Nginx
```bash
# 创建 nginx/nginx.conf
# 配置 SSL 证书
# 配置反向代理
```

### 步骤 3：构建前端
```bash
cd frontend
npm install
npm run build
# 确保 dist/ 目录生成
```

### 步骤 4：启动服务
```bash
cd /opt/lh_contract
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
```

### 步骤 5：初始化数据库
```bash
# 等待数据库健康检查通过
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"

# 创建初始管理员用户
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.init_data import init_data; import asyncio; asyncio.run(init_data())"
```

### 步骤 6：验证部署
```bash
# 检查健康状态
curl http://localhost/health

# 检查日志
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 12. 总结

### ✅ **配置正确的部分**
- Docker 容器化配置完善
- 端口配置基本正确
- 健康检查配置完整
- 生产环境资源限制合理
- 日志轮转配置正确

### ⚠️ **需要注意的部分**
- 前端端口配置有冲突（但实际运行正确）
- 本地开发环境使用 localhost，需要确保生产环境使用容器服务名
- 环境变量需要在生产环境重新配置

### ❌ **需要修复的部分**
- **缺少 Alembic 数据库迁移工具**（高优先级）
- 缺少生产环境配置文件
- 缺少 Nginx 配置文件
- 需要生成强密钥和密码

---

## 联系信息

如有问题，请参考：
- `DEPLOYMENT.md` - 部署文档
- `OPERATIONS_MANUAL.md` - 运维手册
- `TROUBLESHOOTING.md` - 故障排查指南
