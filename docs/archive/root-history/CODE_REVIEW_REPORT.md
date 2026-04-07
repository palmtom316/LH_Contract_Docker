# Beta2 代码审查与优化报告

**审查时间**: 2025年12月15日  
**审查范围**: 前端、后端、数据库、Docker配置

---

## 🚨 1. 发现的严重错误 (Critical Issues)

### 1.1 数据库备份功能失效 (已确认)
**现象**: 后端日志显示 `Full backup error: 500: 未找到 pg_dump 工具`。  
**原因**: 后端 Docker 容器（基于 Python 基础镜像）未安装 PostgreSQL 客户端工具，导致 `pg_dump` 命令不可用。  
**影响**: 系统备份功能无法备份数据库，数据安全存在风险。  
**修复方案**: 修改 `backend/Dockerfile`，在构建阶段安装 `postgresql-client`。

### 1.2 前端 PDF 预览相对路径问题 (已修复)
**现象**: `window.open` 打开相对路径导致 404。  
**状态**: **已在 UpstreamList.vue 中修复**，引入了 `getFileUrl` 工具函数。建议全项目排查类似写法。

---

## 🛠 2. 代码质量与架构审查

### ✅ 优点 (Pros)
*   **后端架构**: 采用了清晰的 `Router -> Service -> Model` 分层架构，逻辑解耦良好。
*   **数据库性能**: 使用了 SQLAlchemy 的 `selectinload` 处理关联查询，避免了 N+1 查询性能问题。
*   **权限控制**: RBAC (Role-Based Access Control) 实现完整，覆盖了前端试图和后端 API 守卫。
*   **前端技术**: 使用 Vue 3 Composition API + Element Plus，代码风格现代。

### ⚠️ 改进项 (Improvements)

#### 2.1 后端 (Backend)
1.  **数据库迁移**: 目前依赖 `init_db`自动建表。建议引入 **Alembic** 进行数据库版本迁移管理，以便在不丢失数据的情况下修改表结构。
2.  **异常处理**: 部分 `try-except` 捕获过于宽泛 (`Exception`)。建议增加自定义异常类，区分业务逻辑错误和系统错误。
3.  **日志冗余**: 某些 CRUD 操作日志过于详细，生产环境可能导致日志文件过大。

#### 2.2 前端 (Frontend)
1.  **大文件组件**: `UpstreamList.vue` 代码量超过 1100 行。
    *   **建议**: 将 `Dialog` (新建/编辑弹窗) 拆分为独立的子组件。
    *   **建议**: 将长表格的渲染逻辑（如 `getSummaries`, `footerCellStyle`）提取为 hook (`composables`)。
2.  **样式硬编码**: 表格底部的黄色样式 (`#FFFF00`) 硬编码在组件中。建议提取到全局 SCSS 变量或主题配置中。
3.  **类型安全**: 项目目前是纯 JS。建议逐步引入 TypeScript 定义核心数据模型（如合同接口定义）。

#### 2.3 数据库 (Database)
1.  **字段类型**: 金额字段使用了 `Numeric(15, 2)`，这是正确的做法。
2.  **索引**: 主要查询字段 (`contract_code`, `party_a_name` 等) 已建立索引，设计良好。

---

## 🚀 3. 立即执行的修复计划

我将立即为您修复 **数据库备份失效** 的问题，这是当前最紧迫的系统风险。

### 修改 `backend/Dockerfile`

**原配置**:
```dockerfile
FROM python:3.11-slim
...
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
...
```

**修改后**:
```dockerfile
FROM python:3.11-slim
...
# 增加 postgresql-client 用于 pg_dump 备份
RUN apt-get update && apt-get install -y gcc libpq-dev postgresql-client && rm -rf /var/lib/apt/lists/*
...
```

---

## 📝 4. 优化建议清单

| 优先级 | 模块 | 建议内容 | 预期收益 |
|:---:|:---|:---|:---|
| 🔴 高 | Docker | 安装 postgresql-client | 修复数据库备份功能 |
| 🟠 中 | 前端 | 拆分 UpstreamList.vue | 提高代码可维护性 |
| 🟠 中 | 后端 | 配置 Alembic | 支持数据库平滑升级 |
| 🟢 低 | 前端 | 统一 API 错误提示 | 提升用户体验 |

---
