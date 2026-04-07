# LH_Contract_Docker 项目全面架构与安全修订计划

基于对项目的深度安全扫描与架构审核，以下是针对 V1.4.1+ 版本的详细修订计划。本计划旨在消除硬编码凭证、强化生产环境安全性、并优化核心架构设计。

## 1. 安全性专项修订 (优先级: P0)

### 1.1 消除硬编码凭证
目前在 `backend/app/config.py` 和 `docker-compose.yml` 中发现了 `dev_password_change_me` 作为默认回退值。这在生产环境中极度危险。

- **行动**:
    - **强制环境变量**: 修改 `config.py`，在 `_IS_PRODUCTION` 为 True 时，如果检测到默认密码或空密码，直接抛出 `ValueError` 阻止启动。
    - **Docker 配置清洗**: 从 `docker-compose.prod.yml` 中移除所有 `environment` 块下的默认值（如 `:-dev_password_change_me`），强制要求从 `.env` 文件读取。
    - **Git 过滤**: 确保 `.env.production` 永远不会被提交到版本控制。

### 1.2 收紧网络安全策略 (CORS & Hosts)
后端 `main.py` 和 Docker 配置目前过于宽泛。

- **行动**:
    - **后端 CORS**: 修改 `main.py`，不再默认允许 `allow_methods=["*"]` 和 `allow_headers=["*"]`。仅开放必要的 HTTP 方法 (GET, POST, PUT, DELETE, OPTIONS) 和 Headers (Authorization, Content-Type)。
    - **主机白名单**: 在 `docker-compose.prod.yml` 中，将 `ALLOWED_HOSTS` 从 `["*"]` 修改为具体的域名列表变量，如 `["${DOMAIN_NAME}"]`。

### 1.3 数据库初始化安全
`init.sql` 当前授予了 `lh_admin` 所有权限。

- **行动**:
    - 仅授予业务所需的最小权限（如 CRUD），禁止 DDL 权限（生产环境应通过迁移脚本由更高权限账户执行，或严格控制 DDL 执行窗口）。

---

## 2. 后端架构优化 (优先级: P1)

### 2.1 数据库会话管理重构
当前 `app/database.py` 中的 `get_db` 依赖项使用“隐式提交”模式 (`await session.commit()`)。

- **问题**: 在复杂业务逻辑中（如跨 Service 调用），隐式提交可能导致事务过早结束或状态不一致。
- **优化方案**:
    - 将 `commit` 逻辑移出 `get_db`。
    - 在 Service 层（如 `ContractUpstreamService`）的方法末尾显式调用 `await self.db.commit()`。
    - 引入 `UnitOfWork` 模式或上下文管理器来管理事务边界。

### 2.2 恢复中间件链路
`main.py` 处于 "Safe Mode"，禁用了部分中间件。

- **行动**:
    - 逐一排查被禁用的中间件（如审计日志、性能监控）。
    - 修复与 `starlette.responses.Response` 的冲突（通常是由于中间件修改了已响应的 Response 对象）。
    - 恢复完整的请求链路追踪。

---

## 3. 数据库迁移与运维 (优先级: P1)

### 3.1 引入 Alembic 迁移管理
项目目前依赖 `init.sql` 和分散的 `.sql` 脚本，缺乏版本控制。

- **行动**:
    - 初始化 Alembic: `alembic init alembic`。
    - 配置 `alembic.ini` 连接异步引擎。
    - 为现有模型生成初始迁移版本 (`alembic revision --autogenerate`)。
    - 废弃手动 SQL 脚本执行方式。

### 3.2 索引维护自动化
虽然设计了 `db_indexes.py`，但依赖手动运行。

- **行动**:
    - 将索引创建逻辑集成到 Alembic 迁移脚本中。
    - 在 Docker 启动脚本中添加 `alembic upgrade head` 自动执行检查。

---

## 4. 前端与构建优化 (优先级: P2)

### 4.1 构建配置审查
`vite.config.js` 配置基本正确，但需确保生产构建时移除 `console.log` 和调试信息。

- **行动**:
    - 在 `vite.config.js` 的 `build` 选项中添加 `terserOptions` 去除 `drop_console` 和 `drop_debugger`。

### 4.2 API 异常统一处理
`request.js` 已包含基础拦截器。建议增强对 `401` Token 过期的无感刷新逻辑（目前已有基础实现，需确保并发请求时的队列处理）。

---

## 5. 实施路线图

| 阶段 | 任务描述 | 预计耗时 |
| :--- | :--- | :--- |
| **第一阶段: 安全加固** | 清洗 Config/Docker 默认凭证，收紧 CORS，强制 ENV 检查 | 1 天 |
| **第二阶段: 数据库治理** | 引入 Alembic，重构 `get_db` 事务逻辑 | 2-3 天 |
| **第三阶段: 架构复原** | 退出 Safe Mode，修复并启用中间件，优化 Docker 构建 | 2 天 |
| **第四阶段: 全面测试** | 针对 API 进行安全渗透测试与压力测试 | 1 天 |

---
*生成时间: 2026-01-10*
*执行人: Antigravity Agent*
