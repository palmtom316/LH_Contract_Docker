# 蓝海合同管理系统 1.6

企业级合同全生命周期管理系统，覆盖合同台账、财务跟踪、文件上传、审计日志、报表与权限管理。

## 当前状态

- 当前开发基线：`1.6`
- 前端：`Vue 3` + `Vite` + `Element Plus` + `Pinia`
- 后端：`FastAPI` + `SQLAlchemy Async` + `PostgreSQL`
- 对象存储：本地上传目录，可选 `MinIO/S3`
- 缓存：`Redis`

## 核心能力

- 上游、下游、管理类合同全流程管理
- 应收、应付、开票、收付款、结算等财务记录管理
- 基于角色的访问控制与管理员能力隔离
- 合同附件上传、下载、预览
- 审计日志与关键操作追踪
- Dashboard 与报表查询

## 目录结构

```text
LH_Contract_Docker/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── core/              # 配置、错误、缓存、限流等基础设施
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── routers/           # API 路由
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── services/          # 业务服务层
│   │   └── utils/             # 工具函数
│   ├── tests/                 # Pytest 测试
│   ├── uploads/               # 本地运行期上传目录
│   └── requirements*.txt
├── frontend/                   # Vue 前端
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── router/
│   │   ├── stores/
│   │   ├── utils/
│   │   └── views/
│   ├── package.json
│   └── vite.config.js
├── docs/                       # 报告、计划、补充文档
├── docker-compose.yml          # 开发/联调环境
├── docker-compose.prod.yml     # 生产部署参考
└── README.md
```

## 开发启动

### 1. 准备环境变量

复制模板：

```bash
cp .env.example .env
```

至少确认以下变量已经配置：

- `SECRET_KEY`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `DATABASE_URL`
- `INIT_ADMIN_TOKEN`（建议在首次初始化管理员时设置）

### 2. 启动依赖服务

```bash
docker-compose up -d db redis minio
```

默认端口：

- PostgreSQL: `5432`
- Redis: `6379`
- MinIO API: `9000`
- MinIO Console: `9001`

### 3. 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端地址：

- API: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- 健康检查: `http://localhost:8000/health`

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：

- `http://localhost:3000`

## 管理员初始化

当前版本不会在启动时自动创建默认管理员账户。

首次初始化管理员时：

1. 在 `.env` 中设置 `INIT_ADMIN_TOKEN`
2. 保证系统中还没有任何用户
3. 调用 `POST /api/v1/auth/init-admin`
4. 在请求头中传入 `X-Init-Admin-Token`

示例：

```bash
curl -X POST http://localhost:8000/api/v1/auth/init-admin \
  -H 'Content-Type: application/json' \
  -H 'X-Init-Admin-Token: your-init-token' \
  -d '{
    "username": "admin",
    "password": "ChangeMe123!",
    "email": "admin@lanhai.com",
    "full_name": "系统管理员"
  }'
```

如果系统已有用户，再次初始化会被拒绝。

## 测试

### 前端

```bash
npm test --prefix frontend
```

### 后端纯单元/契约测试

这类测试不依赖本地 PostgreSQL：

```bash
./.venv39/bin/pytest \
  backend/tests/test_errors.py \
  backend/tests/test_audit_service.py \
  backend/tests/test_file_compatibility.py \
  backend/tests/test_test_infrastructure.py \
  -q
```

### 后端数据库/接口集成测试

这类测试依赖本地 PostgreSQL。若测试环境不可连接，测试会明确 `skip`。

```bash
./.venv39/bin/pytest backend/tests/test_api_integration.py -q
```

## 部署说明

当前仓库提供多套部署资料，但适用范围不同：

- [`docker-compose.yml`](docker-compose.yml)：本地开发/联调
- [`docker-compose.prod.yml`](docker-compose.prod.yml)：生产部署参考
- [`DEPLOYMENT.md`](DEPLOYMENT.md)：通用部署说明
- [`OPERATIONS_MANUAL.md`](OPERATIONS_MANUAL.md)：运维与排障
- [`docs/archive/deployment-history/PVE_LXC_DEPLOYMENT_GUIDE.md`](docs/archive/deployment-history/PVE_LXC_DEPLOYMENT_GUIDE.md)：历史 LXC 部署参考

使用历史部署文档前，先核对版本、环境变量和依赖版本，不要直接套用旧版本说明。

## 关键配置说明

- `SECRET_KEY`：生产环境必须设置
- `DATABASE_URL`：后端数据库连接串
- `REDIS_URL`：Redis 连接串
- `UPLOAD_DIR`：本地上传目录
- `INIT_ADMIN_TOKEN`：首次管理员初始化令牌
- `TRUSTED_PROXIES`：客户端 IP 提取时使用的可信代理列表
- `MINIO_ENDPOINT` / `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY`：对象存储配置

## 文档索引

### 当前可直接参考

- [`DEPLOYMENT.md`](DEPLOYMENT.md)
- [`OPERATIONS_MANUAL.md`](OPERATIONS_MANUAL.md)
- [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md)
- [`backend/docs/N+1_QUERY_OPTIMIZATION.md`](backend/docs/N+1_QUERY_OPTIMIZATION.md)
- [`frontend/docs/COMPONENT_REFACTORING_GUIDE.md`](frontend/docs/COMPONENT_REFACTORING_GUIDE.md)
- [`docs/reports/2026-04-07-code-review-report.md`](docs/reports/2026-04-07-code-review-report.md)
- [`docs/reports/2026-04-07-remediation-optimization-report.md`](docs/reports/2026-04-07-remediation-optimization-report.md)

### 历史资料

以下文档用于追溯版本演进，不应直接视为 1.6 的当前操作手册：

- 历史发布说明：[`docs/archive/root-history/RELEASE_NOTES_V1.1.md`](docs/archive/root-history/RELEASE_NOTES_V1.1.md)、[`docs/archive/root-history/RELEASE_NOTES_V1.1.1.md`](docs/archive/root-history/RELEASE_NOTES_V1.1.1.md)、[`docs/archive/root-history/RELEASE_NOTES_V1.2.md`](docs/archive/root-history/RELEASE_NOTES_V1.2.md)
- 历史升级与部署资料：[`docs/archive/deployment-history/`](docs/archive/deployment-history/)
- 历史阶段总结、审计与专项记录：[`docs/archive/root-history/`](docs/archive/root-history/)

## 当前已知说明

- `backend/uploads/` 现在只作为本地运行期目录，不再跟踪上传产物
- 后端错误响应已统一为结构化对象
- 测试已区分纯单元场景与数据库集成场景

## 许可证

保留所有权利。
