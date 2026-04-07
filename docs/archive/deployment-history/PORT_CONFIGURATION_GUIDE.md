# 端口配置检查和修复指南

## 当前端口配置总览

### 开发环境端口映射

| 服务 | 容器内端口 | 主机端口 | 配置文件 | 状态 |
|------|----------|---------|---------|------|
| PostgreSQL | 5432 | 5432 | docker-compose.yml | ✅ 正确 |
| Redis | 6379 | 6379 | docker-compose.yml | ✅ 正确 |
| Backend | 8000 | 8000 | docker-compose.yml | ✅ 正确 |
| Frontend | 3000 | 3000 | docker-compose.yml | ⚠️ 需要验证 |

### 生产环境端口映射

| 服务 | 容器内端口 | 主机端口 | 配置文件 | 状态 |
|------|----------|---------|---------|------|
| PostgreSQL | 5432 | 不暴露 | docker-compose.prod.yml | ✅ 正确 |
| Redis | 6379 | 不暴露 | docker-compose.prod.yml | ✅ 正确 |
| Backend | 8000 | 不暴露 | docker-compose.prod.yml | ✅ 正确 |
| Nginx | 80/443 | 80/443 | docker-compose.prod.yml | ✅ 正确 |

---

## 问题 1：前端端口配置不一致

### 问题描述

- `docker-compose.yml` 配置：`3000:3000`
- `frontend/Dockerfile` CMD：`--port 3000`
- `frontend/vite.config.js` 配置：`port: 5173`

### 分析

虽然 `vite.config.js` 中配置的是 5173，但 Dockerfile 的 CMD 参数会覆盖配置文件：

```dockerfile
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
```

所以实际运行时使用的是 **3000 端口**。

### 建议修复方案

#### 选项 1：统一使用 3000 端口（推荐）

修改 `frontend/vite.config.js`，使配置文件与实际运行一致：

```javascript
// frontend/vite.config.js
export default defineConfig({
    // ...
    server: {
        host: '0.0.0.0',
        port: 3000,  // 修改为 3000
        hmr: {
            host: 'localhost',
            port: 3000  // 修改为 3000
        },
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure: false
            },
            '/uploads': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure: false
            }
        }
    }
})
```

**优点：**
- 配置文件与实际运行一致
- 不需要修改 Docker 配置
- 3000 是常见的前端开发端口

#### 选项 2：统一使用 5173 端口（Vite 默认）

如果想使用 Vite 的默认端口 5173：

1. 修改 `docker-compose.yml`：
```yaml
frontend:
  # ...
  ports:
    - "5173:5173"
```

2. 修改 `frontend/Dockerfile`：
```dockerfile
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
```

3. 修改 `.env.example` 和 `backend/app/config.py` 中的 CORS 配置：
```bash
CORS_ORIGINS=http://localhost:5173,http://localhost:8080,http://127.0.0.1:5173
```

**优点：**
- 使用 Vite 默认端口
- 与 Vite 生态保持一致

**缺点：**
- 需要修改多个文件
- 5173 不如 3000 常见

---

## 问题 2：本地开发环境数据库连接配置

### 问题描述

`.env` 和 `backend/.env` 文件中使用 `localhost:5432`：

```bash
DATABASE_URL=postgresql+asyncpg://lh_admin:LanHai2024Secure!@localhost:5432/lh_contract_db
```

这是本地开发配置，在 Docker 容器中应该使用 `db:5432`。

### 分析

- **本地开发**（不使用 Docker）：使用 `localhost:5432` ✅
- **Docker 开发**：应该使用 `db:5432` ✅
- **生产环境**：必须使用 `db:5432` ✅

### 建议

#### 方案 1：区分本地和 Docker 环境

创建两个配置文件：

```bash
# .env.local - 本地开发（不使用 Docker）
DATABASE_URL=postgresql+asyncpg://lh_admin:LanHai2024Secure!@localhost:5432/lh_contract_db
REDIS_URL=redis://localhost:6379/0

# .env.docker - Docker 开发
DATABASE_URL=postgresql+asyncpg://lh_admin:LanHai2024Secure!@db:5432/lh_contract_db
REDIS_URL=redis://redis:6379/0
```

使用时指定配置文件：

```bash
# 本地开发
cp .env.local .env
cd backend
python -m uvicorn app.main:app --reload

# Docker 开发
cp .env.docker .env
docker-compose up
```

#### 方案 2：使用环境变量覆盖（推荐）

保持 `.env` 文件为本地开发配置，在 `docker-compose.yml` 中覆盖：

```yaml
# docker-compose.yml
backend:
  # ...
  environment:
    DATABASE_URL: ${DATABASE_URL:-postgresql+asyncpg://lh_admin:LanHai2024Secure!@db:5432/lh_contract_db}
    REDIS_URL: ${REDIS_URL:-redis://redis:6379/0}
```

这样：
- 本地开发：使用 `.env` 中的 `localhost`
- Docker 开发：使用 `docker-compose.yml` 中的 `db`
- 生产环境：使用 `.env.production` 中的配置

---

## 问题 3：CORS 配置需要根据环境调整

### 当前配置

```python
# backend/app/config.py
CORS_ORIGINS: str = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000"
)
```

### 不同环境的 CORS 配置

#### 开发环境（本地）
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000
```

#### 开发环境（Docker）
```bash
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

#### 生产环境
```bash
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 建议

在不同的 `.env` 文件中配置：

```bash
# .env.local
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000

# .env.docker
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# .env.production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## 问题 4：前端 API 代理配置

### 当前配置

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

### 分析

- **本地开发**：`http://localhost:8000` ✅
- **Docker 开发**：应该使用 `http://backend:8000` ❌

但是，由于前端是在浏览器中运行的，代理请求是从浏览器发出的，所以：

- **开发环境**（无论是否 Docker）：使用 `http://localhost:8000` ✅
- **生产环境**：前端是静态文件，通过 Nginx 代理到后端 ✅

### 结论

当前配置正确，无需修改。

---

## 端口配置快速修复脚本

### 修复前端端口配置一致性

```bash
# 选项 1：统一使用 3000 端口
cat > frontend/vite.config.js << 'EOF'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [
        vue(),
    ],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    },
    server: {
        host: '0.0.0.0',
        port: 3000,
        hmr: {
            host: 'localhost',
            port: 3000
        },
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure: false
            },
            '/uploads': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure: false
            }
        }
    }
})
EOF

echo "✅ 前端端口配置已统一为 3000"
```

---

## 验证端口配置

### 检查 Docker 容器端口映射

```bash
# 启动服务
docker-compose up -d

# 检查端口映射
docker-compose ps

# 预期输出：
# lh_contract_db        5432/tcp -> 0.0.0.0:5432
# lh_contract_redis     6379/tcp -> 0.0.0.0:6379
# lh_contract_backend   8000/tcp -> 0.0.0.0:8000
# lh_contract_frontend  3000/tcp -> 0.0.0.0:3000
```

### 测试端口连通性

```bash
# 测试数据库端口
nc -zv localhost 5432

# 测试 Redis 端口
nc -zv localhost 6379

# 测试后端 API 端口
curl http://localhost:8000/health

# 测试前端端口
curl http://localhost:3000
```

### 检查容器内部网络

```bash
# 进入后端容器
docker-compose exec backend bash

# 测试数据库连接（使用容器服务名）
nc -zv db 5432

# 测试 Redis 连接（使用容器服务名）
nc -zv redis 6379
```

---

## 生产环境端口配置检查清单

### ✅ 必须完成的配置

- [ ] **数据库不对外暴露**：`docker-compose.prod.yml` 中不映射 5432 端口
- [ ] **Redis 不对外暴露**：`docker-compose.prod.yml` 中不映射 6379 端口
- [ ] **后端不对外暴露**：`docker-compose.prod.yml` 中不映射 8000 端口
- [ ] **Nginx 配置正确**：映射 80 和 443 端口
- [ ] **环境变量使用容器服务名**：`db:5432`, `redis:6379`
- [ ] **CORS 配置生产域名**：`https://yourdomain.com`
- [ ] **防火墙规则**：只开放 80 和 443 端口

### ⚠️ 安全建议

- [ ] 使用强密码
- [ ] 配置 SSL 证书
- [ ] 启用 HTTPS
- [ ] 配置 Nginx 安全头
- [ ] 限制数据库和 Redis 只能从后端容器访问
- [ ] 定期更新 Docker 镜像

---

## 总结

### 需要修复的配置

1. **前端端口配置**：修改 `vite.config.js` 使其与 Dockerfile 一致（3000 端口）
2. **环境变量管理**：创建不同环境的 `.env` 文件
3. **CORS 配置**：根据环境配置不同的允许源

### 配置正确的部分

1. ✅ Docker 端口映射配置正确
2. ✅ 生产环境安全配置合理（不暴露内部服务端口）
3. ✅ 健康检查配置完善
4. ✅ 前端代理配置正确

### 下一步行动

1. **立即修复**：前端端口配置一致性
2. **建议完成**：创建不同环境的 `.env` 文件
3. **生产部署前**：配置生产环境 CORS 和 SSL 证书
