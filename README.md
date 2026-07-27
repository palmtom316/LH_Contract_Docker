# 合同管理系统 / Contract Management System

[![Version](https://img.shields.io/badge/version-1.9.1-blue.svg)](https://github.com/palmtom316/LH_Contract_Docker)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](docker-compose.yml)

企业级合同全生命周期管理系统，提供合同台账、财务跟踪、文件存储、审计日志、报表分析与精细化权限管理。

**English** | [中文文档](README_CN.md)

---

## ✨ 特性

- 📋 **合同管理** - 上游、下游、管理类合同全流程管理，支持多维度查询与筛选
- 💰 **财务跟踪** - 应收应付、开票收款、结算记录自动化管理
- 🔐 **权限控制** - 基于角色的访问控制（RBAC），管理员能力隔离
- 📎 **文件管理** - MinIO/S3 对象存储，支持合同附件上传、预览、版本管理
- 📊 **数据分析** - 可视化 Dashboard，多维度报表导出
- 🔍 **审计日志** - 完整的操作追踪与审计记录
- 🚀 **高性能** - 异步架构 + Redis 缓存 + 数据库索引优化
- 🔒 **安全加固** - JWT 令牌轮换、刷新令牌吊销、密码策略、CORS 配置

---

## 🏗️ 技术栈

### 后端
- **框架**: FastAPI 0.115+ (Python 3.11)
- **ORM**: SQLAlchemy 2.0 (Async)
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **认证**: JWT (PyJWT) + Refresh Token 轮换
- **对象存储**: MinIO / S3 兼容

### 前端
- **框架**: Vue 3.5 + Composition API
- **构建工具**: Vite 7
- **UI 库**: Element Plus 2.9
- **状态管理**: Pinia 2.3
- **路由**: Vue Router 4.5
- **图表**: ECharts 5.5

### 基础设施
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx (可选)
- **CI/CD**: GitHub Actions

---

## 📦 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- Git 2.0+

### 1. 克隆项目

```bash
git clone https://github.com/palmtom316/LH_Contract_Docker.git
cd LH_Contract_Docker
```

### 2. 配置环境变量

**开发环境**：
```bash
cp .env.example .env
```

**生产环境**（默认部署路径）：
```bash
cp .env.production.example .env.production
```

**重要**: 编辑对应的环境文件，至少修改以下配置：

```bash
# 生产环境必须使用强密码！
SECRET_KEY=<使用下方命令生成>
INIT_ADMIN_TOKEN=<使用下方命令生成>

# 数据库
POSTGRES_PASSWORD=<生成强密码>
DATABASE_URL=postgresql+asyncpg://lh_admin:<密码>@db:5432/lh_contract_db

# MinIO 对象存储
MINIO_ROOT_USER=<自定义用户名>
MINIO_ROOT_PASSWORD=<生成强密码，至少8字符>

# CORS（生产环境替换为实际域名）
CORS_ORIGINS=http://localhost:80,https://your-domain.com
```

**生成密钥**：
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 3. 启动服务

**开发环境**：
```bash
docker compose up -d
```

**生产环境（默认推荐）**：
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

`docker-compose.production.yml` 是 HTTPS 加固预设，要求先准备 `nginx/ssl/fullchain.pem` 与 `nginx/ssl/privkey.pem`，并复核 backend 需要透传的环境变量；不建议作为首次部署的 quick start。

### 4. 初始化管理员账户

系统不会自动创建默认管理员，首次部署需手动初始化：

```bash
curl -X POST http://localhost/api/v1/auth/init-admin \
  -H 'Content-Type: application/json' \
  -H 'X-Init-Admin-Token: <你的INIT_ADMIN_TOKEN>' \
  -d '{
    "username": "admin",
    "password": "YourStrongPassword123!",
    "email": "admin@example.com",
    "full_name": "系统管理员"
  }'
```

**安全提示**：初始化后建议删除 `INIT_ADMIN_TOKEN` 环境变量。

### 5. 访问系统

- **前端界面**: http://localhost:80
- **后端 API**: http://localhost/api/v1
- **健康检查**: http://localhost/health/ready
- **API 文档**: 生产环境默认关闭
- **MinIO 控制台**: 默认生产配置不对外暴露

---

## 📂 项目结构

```text
LH_Contract_Docker/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── core/              # 核心模块（配置、错误、缓存、限流）
│   │   ├── models/            # SQLAlchemy 数据模型
│   │   ├── routers/           # API 路由（20+ 端点）
│   │   ├── schemas/           # Pydantic 验证模型
│   │   ├── services/          # 业务逻辑层
│   │   └── utils/             # 工具函数
│   ├── tests/                 # Pytest 测试套件
│   ├── alembic/               # 数据库迁移
│   ├── requirements.txt       # Python 依赖
│   └── Dockerfile             # 后端容器镜像
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── api/               # API 客户端
│   │   ├── components/        # Vue 组件
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── utils/             # 工具函数
│   │   └── views/             # 页面视图（23+ 页面）
│   ├── package.json           # npm 依赖
│   ├── vite.config.js         # Vite 构建配置
│   └── Dockerfile             # 前端容器镜像
├── docs/                       # 项目文档
│   ├── API_DOCUMENTATION.md   # API 接口文档
│   ├── USER_OPERATION_MANUAL.md # 用户操作手册
│   └── PVE_BACKUP_GUIDE.md    # 备份恢复指南
├── docker-compose.yml          # 开发环境编排
├── docker-compose.prod.yml       # 默认生产环境编排（读取 .env.production）
├── docker-compose.production.yml # HTTPS 加固预设（需证书与配置复核）
├── DEPLOYMENT.md               # 详细部署指南
├── OPERATIONS_MANUAL.md        # 运维手册
├── .env.example                # 开发环境变量模板
└── .env.production.example     # 生产环境变量模板
```

---

## 🔧 开发指南

### 本地开发（不使用 Docker）

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动数据库和 Redis（Docker）
docker compose up -d db redis minio

# 运行开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**后端地址**：
- API: http://localhost:8000
- Swagger 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

**前端地址**: http://localhost:5173

### 运行测试

**后端测试**：
```bash
cd backend
source .venv/bin/activate

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_auth_hardening.py -v

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

**前端测试**：
```bash
cd frontend
npm run test
```

---

## 🚀 部署

详细部署说明请参考：

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - 完整的生产环境部署指南
- **[OPERATIONS_MANUAL.md](OPERATIONS_MANUAL.md)** - 日常运维与故障排查

### 快速部署检查清单

- [ ] 修改所有默认密码和密钥
- [ ] 配置 CORS 为实际域名
- [ ] 设置 `DEBUG=false`
- [ ] 配置 SSL 证书（生产环境）
- [ ] 设置防火墙规则
- [ ] 配置数据库定期备份
- [ ] 配置日志轮转
- [ ] 性能测试和压力测试
- [ ] 配置监控告警

---

## 🔐 安全注意事项

⚠️ **在生产环境部署前，请务必：**

1. **更改所有密钥和密码**
   - 使用 `python -c "import secrets; print(secrets.token_urlsafe(64))"` 生成强密钥
   - 数据库密码至少 16 字符，包含大小写字母、数字、特殊字符

2. **禁止提交敏感文件**
   - `.env` 文件已在 `.gitignore` 中，切勿提交
   - 定期检查：`git log --all --full-history -- ".env"`

3. **配置网络安全**
   - 仅暴露必要端口（80/443）
   - 内部服务端口（PostgreSQL, Redis, MinIO）不对外开放
   - 使用防火墙限制访问

4. **启用 HTTPS**
   - 生产环境必须配置 SSL 证书
   - 推荐使用 Let's Encrypt 免费证书

5. **定期更新依赖**
   ```bash
   # 检查后端依赖更新
   cd backend && pip list --outdated

   # 检查前端依赖更新
   cd frontend && npm outdated
   ```

6. **备份策略**
   - 数据库每日自动备份
   - MinIO 数据定期备份
   - 测试备份恢复流程

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx Gateway (80/443)                 │
│                  (only public entrypoint)                 │
└────────────────────┬─────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│   Frontend   │          │   Backend    │
│   (Vue 3)    │◄────────►│  (FastAPI)   │
│   Port: 80   │          │  Port: 8000  │
└──────────────┘          └───────┬──────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
            ┌──────────┐  ┌──────────┐  ┌──────────┐
            │PostgreSQL│  │  Redis   │  │  MinIO   │
            │Port: 5432│  │Port: 6379│  │Port: 9000│
            └──────────┘  └──────────┘  └──────────┘
```

---

## 🛠️ 配置说明

### 关键环境变量

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `APP_VERSION` | 应用版本号 | 1.9.1 | 否 |
| `DEBUG` | 调试模式 | false | 否 |
| `SECRET_KEY` | 应用密钥 | - | **是** |
| `DATABASE_URL` | 数据库连接字符串 | - | **是** |
| `REDIS_URL` | Redis 连接字符串 | redis://redis:6379/0 | 否 |
| `MINIO_ENDPOINT` | MinIO 内部端点 | minio:9000 | 否 |
| `COMPANY_TAX_NO` | 本公司纳税人识别号，用于电子发票方向识别 | - | **是** |
| `CORS_ORIGINS` | 允许的跨域源 | - | **是** |
| `INIT_ADMIN_TOKEN` | 管理员初始化令牌 | - | **是**（首次） |
| `ENABLE_API_DOCS` | 是否启用 API 文档 | false（生产） | 否 |
| `TRUSTED_PROXIES` | 可信代理 IP | - | 否 |

开发配置请参考 [.env.example](.env.example)，生产配置请参考 [.env.production.example](.env.production.example)。

---

## 📚 文档索引

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - 生产环境部署指南
- **[OPERATIONS_MANUAL.md](OPERATIONS_MANUAL.md)** - 运维手册
- **[API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** - API 接口文档
- **[USER_OPERATION_MANUAL.md](docs/USER_OPERATION_MANUAL.md)** - 用户操作手册
- **[PVE_BACKUP_GUIDE.md](docs/PVE_BACKUP_GUIDE.md)** - 备份恢复指南
- **[PVE_1.7.1_TO_1.8.md](docs/PVE_1.7.1_TO_1.8.md)** - PVE 1.7.1 升级到 1.8.0
- **[upgrade-1.9.0-to-1.9.1.md](docs/deployment/upgrade-1.9.0-to-1.9.1.md)** - PVE 1.9.0 升级到 1.9.1
- **[N+1_QUERY_OPTIMIZATION.md](backend/docs/N+1_QUERY_OPTIMIZATION.md)** - 数据库查询优化

---

## 🔄 版本历史

### v1.9.1 (2026-07-27)
- 🔖 PVE 镜像、CI 发布版本和应用版本号更新至 1.9.1
- 🧪 PVE 升级预检改为校验 1.9.1 镜像

### v1.8.0 (2026-07-16)
- ✨ 新增电子发票批量导入、合同匹配、人工分摊与确认挂账
- 📊 扩展成本报表周期并新增结算报表
- 🔒 加固发票确认幂等性、压缩包解析与 PVE 网络暴露
- 🔖 系统版本号更新至 1.8.0

### v1.7.1 (2026-07-07)
- ✨ 新增上游合同挂账付款综合报表
- 🔖 系统版本号更新至 1.7.1

### v1.7.0 (2026-06-24)
- ✨ 增强付款报表分类筛选功能
- 🐛 修复生产环境前端加载异常
- 🔒 收敛内部服务端口暴露
- 🚀 优化前端打包和加载性能
- 📦 发布 GitHub Container Registry 镜像

### v1.6.4 (2026-04)
- 🎨 前端 UI 全面升级（极简 SaaS 风格）
- 🐛 修复暗色模式表格显示问题
- 🔧 优化 Element Plus 打包分割
- 📊 改进合同报表导出功能

### v1.6.3 (2026-03)
- 🔐 实施认证安全加固（JTI 绕过修复）
- ♻️ 统一错误处理机制
- 🧹 移除死代码和未使用路由
- 🧪 改进测试基础设施

### v1.6.1-1.6.2
- 🔒 实现 Refresh Token 轮换和吊销
- 📝 完善审计日志
- 🐛 修复多项安全漏洞

查看完整历史：[CHANGELOG.md](CHANGELOG.md)

---

## 🤝 贡献

本项目暂不接受外部贡献。

---

## 📄 许可证

保留所有权利。未经授权不得复制、修改或分发。

---

## 💬 支持

如有问题，请联系：

- **技术支持**: 内部运维渠道
- **问题跟踪**: [GitHub Issues](https://github.com/palmtom316/LH_Contract_Docker/issues)

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue.js](https://vuejs.org/)
- [Element Plus](https://element-plus.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [MinIO](https://min.io/)

## Electronic Invoice Import

The system supports uploading an electronic invoice batch archive. Each invoice inside the batch should be an individual zip containing XML and may include PDF/OFD attachments. The system parses invoice fields from XML, detects upstream/downstream direction, recommends contract candidates, and posts formal invoice records only after an operator confirms allocations.

Production environments must configure:

- `COMPANY_NAME`
- `COMPANY_TAX_NO`

The first release does not support non-contract expense invoices, OCR, automatic amount splitting, or automatic posting without operator confirmation.
