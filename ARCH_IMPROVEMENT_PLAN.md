# LH_Contract_Docker 项目架构与代码改进计划 (V1.4.1+)

基于技术专家的深度审核，本项目架构成熟、功能完善，但在性能优化、安全性增强和工程化细节上仍有提升空间。

## 1. 核心架构优化意见

### 1.1 后端 (FastAPI & SQLAlchemy)
- **数据库 Session 管理改进**：目前 `get_db` 依赖项在 `yield` 后自动执行 `commit()`。
    - **问题**：可能导致不必要的写操作或在复杂的业务逻辑中难以精确控制事务边界。
    - **优化**：将 `commit` 逻辑移至 Service 层，`get_db` 仅负责 Session 的生命周期管理（创建与关闭）。
- **模型计算属性性能优化**：`ContractUpstream` 等模型使用 Python `property` 计算关联表总额（如 `total_received`）。
    - **问题**：随着数据量增加，访问这些属性会触发 N+1 查询问题或内存计算压力。
    - **优化**：在 Service 层使用数据库聚合函数（`func.sum`）进行统计，或者使用 SQLAlchemy 的 `hybrid_property` 配合表达式。
- **中间件与错误处理**：`main.py` 中提到处于 "Safe Mode" 并禁用了部分中间件。
    - **优化**：深入排查 `starlette.responses.Response` 冲突的根本原因，恢复完整的中间件链路（如详细的审计日志中间件、性能监控中间件）。

### 1.2 数据库 (PostgreSQL)
- **索引维护**：虽然已经设计了非常专业的覆盖索引（Covering Indexes），但需确保在 Docker 环境下有定期的 `ANALYZE` 任务。
- **审计日志脱离主库**：目前的 `audit_logs` 存储在主业务库中。
    - **优化**：长期看，建议对审计日志进行表分区（Partitioning）或迁移到专用的日志存储/文档数据库。

### 1.3 前端 (Vue 3)
- **状态管理规范化**：确保 Pinia store 中的数据同步逻辑严密，避免多页面数据不一致。
- **API 异常捕获**：在 `request.js` 中加强对特定错误码（如 401, 403, 429）的统一拦截与用户友好提示。

---

## 2. 工程化与部署优化

### 2.1 Docker 优化
- **多阶段构建 (Multi-stage Build)**：
    - **优化**：前端应在容器内构建后，仅保留 `dist` 静态文件交由 Nginx 托管；后端应区分开发和生产环境，减少生产镜像体积。
- **资源限制**：在 `docker-compose.yml` 中为各服务添加 `deploy.resources` 限制，防止内存泄漏导致宿主机崩溃。

### 2.2 安全性增强
- **敏感信息脱敏**：确保 `init_data.py` 和 `.env` 中的初始密码在生产环境中强制修改。
- **Nginx 安全配置**：添加 `Content-Security-Policy`, `X-Frame-Options` 等安全响应头。

---

## 3. 专项检查：Opus 4.5 无法使用原因

**诊断结果**：
通过分析系统日志 (`~/.claude/debug/latest`)，确认 `antigravity-opus-4-5` (Claude 4.5 Opus) 无法使用的根本原因是 **Anthropic API 账户余额不足**。
- **错误详情**：`400 Bad Request: "Your credit balance is too low to access the Anthropic API."`
- **解决建议**：请前往 Anthropic 控制台或通过提供商增加账户信用额度。在余额恢复前，建议将 Agent 模型临时切换为 `gemini-3-pro-high` 或 `claude-sonnet-4-5`。

---

## 4. 改进实施路径 (2026 Q1)

| 阶段 | 任务 | 优先级 |
| :--- | :--- | :--- |
| **P0 (紧急)** | 充值 API 余额或切换模型，恢复 AI 辅助功能 | 最高 |
| **P1 (优化)** | 优化 `get_db` 事务管理，移出自动 commit | 高 |
| **P1 (优化)** | 重构模型计算属性为数据库聚合查询 | 高 |
| **P2 (工程)** | 实施 Docker 多阶段构建，优化镜像体积 | 中 |
| **P2 (安全)** | 加强 Nginx 安全头配置与敏感数据审计 | 中 |

---
*审核人：Antigravity (Sisyphus)*
*日期：2026年1月10日*
