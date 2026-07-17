# 合同管理系统

[![版本](https://img.shields.io/badge/版本-1.7.1-blue.svg)](https://github.com/palmtom316/LH_Contract_Docker)
[![许可证](https://img.shields.io/badge/许可证-专有-red.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](docker-compose.yml)

企业级合同全生命周期管理系统，提供合同台账、财务跟踪、文件存储、审计日志、报表分析与精细化权限管理。

[English](README.md) | **中文文档**

---

## ✨ 核心功能

- 📋 **合同管理** - 上游、下游、管理类合同全流程管理，支持多维度查询与筛选
- 💰 **财务跟踪** - 应收应付、开票收款、结算记录自动化管理
- 🔐 **权限控制** - 基于角色的访问控制（RBAC），管理员能力隔离
- 📎 **文件管理** - MinIO/S3 对象存储，支持合同附件上传、预览、版本管理
- 📊 **数据分析** - 可视化 Dashboard，多维度报表导出（Excel）
- 🔍 **审计日志** - 完整的操作追踪与审计记录
- 🚀 **高性能** - 异步架构 + Redis 缓存 + 数据库索引优化
- 🔒 **安全加固** - JWT 令牌轮换、刷新令牌吊销、密码策略、CORS 配置

---

## 🏗️ 技术架构

### 后端
- **框架**: FastAPI 0.115+ (Python 3.11)
- **ORM**: SQLAlchemy 2.0 (Async)
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **认证**: JWT + Refresh Token 轮换机制
- **对象存储**: MinIO / S3 兼容

### 前端
- **框架**: Vue 3.5 + Composition API
- **构建工具**: Vite 7
- **UI 组件库**: Element Plus 2.9
- **状态管理**: Pinia 2.3
- **路由**: Vue Router 4.5
- **图表**: ECharts 5.5

### 基础设施
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx（可选）
- **CI/CD**: GitHub Actions

---

## 🚀 快速开始

### 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ 内存（推荐 8GB）
- 40GB+ 硬盘空间

### 一键部署

```bash
# 1. 克隆项目
git clone https://github.com/palmtom316/LH_Contract_Docker.git
cd LH_Contract_Docker

# 2. 配置生产环境变量
cp .env.production.example .env.production
nano .env.production  # 修改关键配置（见下方）

# 3. 启动服务
docker compose --env-file .env.production -f docker-compose.prod.yml up -d

# 4. 查看日志
docker compose -f docker-compose.prod.yml logs -f
```

`docker-compose.production.yml` 是 HTTPS 加固预设，要求先准备 `nginx/ssl/fullchain.pem` 与 `nginx/ssl/privkey.pem`，并复核 backend 需要透传的环境变量；首次部署默认使用 `docker-compose.prod.yml`。

### 关键配置

**必须修改** `.env.production` 文件中的以下配置：

```bash
# 生成安全密钥（运行此命令）
python -c "import secrets; print(secrets.token_urlsafe(64))"

# 应用密钥（使用上述命令生成）
SECRET_KEY=<生成的密钥>
INIT_ADMIN_TOKEN=<生成的密钥>

# 数据库密码（设置强密码）
POSTGRES_PASSWORD=<强密码>
DATABASE_URL=postgresql+asyncpg://lh_admin:<密码>@db:5432/lh_contract_db

# MinIO 密码（至少 8 字符）
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=<强密码>

# CORS（替换为实际域名）
CORS_ORIGINS=https://your-domain.com

# 关闭调试模式
DEBUG=false
```

### 初始化管理员

```bash
curl -X POST http://localhost/api/v1/auth/init-admin \
  -H 'Content-Type: application/json' \
  -H 'X-Init-Admin-Token: <你的 INIT_ADMIN_TOKEN>' \
  -d '{
    "username": "admin",
    "password": "你的强密码",
    "email": "admin@example.com",
    "full_name": "系统管理员"
  }'
```

### 访问系统

- **前端**: http://localhost:80
- **后端 API**: http://localhost/api/v1
- **健康检查**: http://localhost/health/ready
- **API 文档**: 生产环境默认关闭
- **MinIO 控制台**: 默认生产配置不对外暴露

---

## 📂 项目结构

```
LH_Contract_Docker/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── core/        # 核心模块（配置、错误、缓存）
│   │   ├── models/      # 数据模型
│   │   ├── routers/     # API 路由
│   │   ├── schemas/     # 数据验证
│   │   ├── services/    # 业务逻辑
│   │   └── utils/       # 工具函数
│   ├── tests/           # 测试
│   ├── alembic/         # 数据库迁移
│   └── requirements.txt # 依赖
├── frontend/            # Vue 3 前端
│   ├── src/
│   │   ├── api/         # API 客户端
│   │   ├── components/  # 组件
│   │   ├── router/      # 路由
│   │   ├── stores/      # 状态管理
│   │   ├── utils/       # 工具
│   │   └── views/       # 页面
│   └── package.json
├── docs/                # 文档
├── docker-compose.prod.yml        # 默认生产环境（读取 .env.production）
├── docker-compose.production.yml  # HTTPS 加固预设
├── DEPLOYMENT.md        # 部署指南
├── .env.example         # 开发配置模板
└── .env.production.example # 生产配置模板
```

---

## 📚 完整文档

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - 详细的生产环境部署指南
- **[OPERATIONS_MANUAL.md](OPERATIONS_MANUAL.md)** - 日常运维与故障排查
- **[API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** - API 接口文档
- **[USER_OPERATION_MANUAL.md](docs/USER_OPERATION_MANUAL.md)** - 用户操作手册

---

## 🔐 安全注意事项

### ⚠️ 部署前必读

1. **更改所有默认密码和密钥**
   ```bash
   # 使用此命令生成强密钥
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

2. **禁止提交 `.env` 文件到 Git**
   - `.env` 已在 `.gitignore` 中
   - 切勿提交包含真实密码的配置文件

3. **生产环境配置检查清单**
   - [ ] `DEBUG=false`
   - [ ] `SECRET_KEY` 已修改为随机生成的密钥
   - [ ] `POSTGRES_PASSWORD` 已设置强密码（16+ 字符）
   - [ ] `MINIO_ROOT_PASSWORD` 已设置强密码（8+ 字符）
   - [ ] `CORS_ORIGINS` 已设置为实际域名
   - [ ] `ENABLE_API_DOCS=false`（生产环境关闭）
   - [ ] 配置 SSL 证书（HTTPS）
   - [ ] 配置防火墙，仅开放 80/443 端口
   - [ ] 配置定期数据库备份

4. **网络安全**
   - 内部服务端口（5432, 6379, 9000）不对外开放
   - 使用 Nginx 反向代理
   - 启用防火墙和 fail2ban

5. **定期更新**
   - 定期检查依赖更新
   - 关注安全公告
   - 测试后再升级生产环境

---

## 🛠️ 开发指南

### 本地开发

**后端开发**：
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 启动依赖服务
docker compose up -d db redis minio

# 运行开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端开发**：
```bash
cd frontend
npm install
npm run dev
```

### 运行测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test
```

---

## 🔄 版本历史

### v1.7.1 (2026-07-07) - 当前版本
- ✨ 新增上游合同挂账付款综合报表
- 🔖 系统版本号更新至 1.7.1

### v1.7.0 (2026-06-24)
- ✨ 增强付款报表分类筛选
- 🐛 修复生产环境前端加载异常
- 🔒 收敛内部服务端口暴露
- 🚀 优化前端打包性能
- 📦 发布 GitHub Container Registry 镜像

### v1.6.4 (2026-04)
- 🎨 前端 UI 全面升级
- 🐛 修复暗色模式显示问题
- 📊 改进报表导出功能

### v1.6.3 (2026-03)
- 🔐 认证安全加固
- ♻️ 统一错误处理
- 🧹 代码重构优化

---

## 📞 技术支持

- **技术支持**: 内部运维渠道
- **问题反馈**: [GitHub Issues](https://github.com/palmtom316/LH_Contract_Docker/issues)

---

## 📄 许可证

保留所有权利。未经授权不得复制、修改或分发。

---

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Element Plus](https://element-plus.org/) - Vue 3 组件库
- [PostgreSQL](https://www.postgresql.org/) - 强大的开源数据库
- [MinIO](https://min.io/) - 高性能对象存储

## 电子发票导入

系统支持上传电子发票批次压缩包。压缩包内每张发票应为一个独立 zip，包含 XML，并可包含 PDF/OFD。系统从 XML 解析发票字段，判断上游/下游，推荐合同候选，并在操作人确认分摊后写入正式挂账记录。

生产环境必须配置：

- `COMPANY_NAME`
- `COMPANY_TAX_NO`

第一期不支持无合同费用发票、OCR、自动拆分金额或自动确认入账。
