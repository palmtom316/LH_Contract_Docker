# LH Contract System Hardening Upgrade Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不丢失任何历史合同记录、费用记录、审计数据、上传文件和数据字典配置的前提下，完成系统安全修复、升级稳定性加固和前端可用性整改。

**Architecture:** 采用“先保兼容、再加约束、最后收敛旧行为”的分阶段升级路线。所有影响数据库和文件访问链路的修订必须遵循“双读兼容、增量迁移、可回滚、默认保守”的原则，避免对已运行半年的生产数据和上传文件造成破坏。

**Tech Stack:** FastAPI, SQLAlchemy Async, Alembic, PostgreSQL, MinIO/local uploads, Vue 3, Element Plus, Vant, Docker Compose

---

## Upgrade Constraints

- 绝不删除现有业务表中的历史记录，不执行破坏性 DDL。
- 绝不批量重写现有文件路径，文件访问链路必须先支持旧路径与新路径并存。
- 所有字典值变更必须先做“引用扫描”，尤其是 `expense_type` / 费用类别相关数据。
- 字典项不再允许直接硬删除已被引用的值，改为软停用或受控替换。
- 安全修复优先采用“收口新增风险、保留存量兼容”的方式，避免一次性切断现有生产流程。
- 每一阶段都必须具备独立回滚点和验证清单。

## Program Structure

本次修订拆成 5 个顺序执行的工作流：

1. 生产基线保护与升级护栏
2. 鉴权与高风险后端漏洞修复
3. 文件访问与字典数据兼容治理
4. 前端稳定性、可访问性和移动端整改
5. 发布、灰度、回滚与验收

这些工作流必须按顺序推进；其中第 2 和第 3 阶段完成并通过验证后，才允许进入正式上线窗口。

---

### Task 1: 生产基线保护与升级护栏

**Files:**
- Create: `docs/superpowers/plans/2026-04-04-system-hardening-upgrade-plan.md`
- Create: `docs/release/upgrade-runbook-v1.6-hardening.md`
- Create: `backend/tests/integration/test_upgrade_safety.py`
- Modify: `scripts/backup.sh`
- Modify: `scripts/verify_migration.py`
- Modify: `docker-compose.production.yml`

- [ ] **Step 1: 定义升级前必须采集的生产基线**

记录并固化以下升级前检查项：

```text
1. PostgreSQL 全库备份
2. uploads 目录完整备份
3. MinIO bucket 对象数量与总大小快照
4. sys_dictionaries 导出快照
5. 用户总数 / 合同总数 / 费用总数 / 审计日志总数
6. 最近 30 天新增记录数
7. 当前启用中的数据字典值清单
```

- [ ] **Step 2: 为升级验证编写安全性集成测试清单**

测试文件需要覆盖：

```python
def test_existing_expense_records_remain_queryable_after_upgrade():
    ...

def test_existing_dictionary_values_remain_renderable_after_upgrade():
    ...

def test_legacy_upload_paths_remain_downloadable_after_upgrade():
    ...

def test_refresh_token_and_login_upgrade_do_not_modify_business_data():
    ...
```

- [ ] **Step 3: 增强备份脚本，加入字典和对象存储校验**

脚本目标：

```bash
./scripts/backup.sh
# 应同时产出：
# - PostgreSQL dump
# - uploads 归档
# - sys_dictionaries 导出 CSV/JSON
# - 对象存储清单摘要
```

- [ ] **Step 4: 为所有后续数据库变更建立“只增不删”的校验器**

`scripts/verify_migration.py` 需要校验：

```python
assert no_drop_table_statements
assert no_drop_column_statements
assert no_update_rewrites_of_file_paths_without_backup_marker
assert no_hard_delete_of_dictionary_values_in_migration
```

- [ ] **Step 5: 形成升级运行手册并提交**

```bash
git add docs/release/upgrade-runbook-v1.6-hardening.md scripts/backup.sh scripts/verify_migration.py backend/tests/integration/test_upgrade_safety.py
git commit -m "docs: add upgrade safety runbook and baseline checks"
```

---

### Task 2: 鉴权与高风险后端漏洞修复

**Files:**
- Modify: `backend/app/routers/auth.py`
- Modify: `backend/app/init_data.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/services/auth.py`
- Modify: `backend/tests/test_auth.py`
- Modify: `backend/tests/test_refresh_token.py`
- Create: `backend/tests/test_auth_hardening.py`

- [ ] **Step 1: 写失败测试，锁定公开注册提权漏洞**

```python
async def test_public_register_cannot_create_admin_role(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "evil",
            "password": "ValidPass123",
            "role": "ADMIN",
        },
    )
    assert response.status_code in (400, 403)
```

- [ ] **Step 2: 收口注册策略，但保留已存在账号与数据**

实现原则：

```text
1. 禁止匿名注册管理员或高权限角色
2. 更保守的方案：完全关闭公开注册，仅保留管理员创建用户
3. 不修改现有 users 表已有数据
4. 不影响已有账号登录
```

- [ ] **Step 3: 去除启动时自动创建默认管理员**

目标行为：

```text
- init_data 不再自动落地 admin/admin123
- /auth/init-admin 仅在明确初始化窗口可用
- 生产环境必须要求 INIT_ADMIN_TOKEN
- README 和登录页不再引导默认管理员初始化
```

- [ ] **Step 4: 修复 refresh token 轮换契约并更新测试**

后端保持：

```python
return {
    "access_token": access_token,
    "refresh_token": new_refresh_token,
    "token_type": "bearer",
}
```

测试必须覆盖：

```python
async def test_old_refresh_token_is_revoked_after_rotation(...):
    ...

async def test_logout_revokes_all_refresh_tokens(...):
    ...
```

- [ ] **Step 5: 统一异常响应，避免 500 泄漏内部错误**

约束：

```text
- 生产环境 500 不返回原始异常字符串
- 日志保留详细堆栈
- 客户端拿到统一错误结构
```

- [ ] **Step 6: 运行鉴权测试并提交**

Run:

```bash
PYTHONPATH=backend pytest backend/tests/test_auth.py backend/tests/test_refresh_token.py backend/tests/test_auth_hardening.py -v
```

Expected:

```text
PASS
```

Commit:

```bash
git add backend/app/routers/auth.py backend/app/init_data.py backend/app/main.py backend/app/services/auth.py backend/tests/test_auth.py backend/tests/test_refresh_token.py backend/tests/test_auth_hardening.py
git commit -m "fix: harden auth flows and remove unsafe bootstrap paths"
```

---

### Task 3: 文件访问与字典数据兼容治理

**Files:**
- Modify: `backend/app/routers/common.py`
- Modify: `frontend/src/utils/common.js`
- Modify: `frontend/src/api/auth.js`
- Modify: `frontend/src/stores/user.js`
- Modify: `backend/app/routers/system.py`
- Modify: `backend/app/models/system.py`
- Modify: `backend/app/models/expense.py`
- Create: `backend/app/services/dictionary_usage_service.py`
- Create: `backend/tests/test_dictionary_safety.py`
- Create: `backend/tests/test_file_compatibility.py`

- [ ] **Step 1: 为文件访问写兼容性测试**

```python
async def test_legacy_uploads_path_still_downloads_with_auth_header(...):
    ...

async def test_minio_key_download_works_without_query_token(...):
    ...
```

- [ ] **Step 2: 移除前端 URL query token 依赖，但保持旧文件可读**

实施原则：

```text
1. 前端不再把 token 拼到文件 URL 上
2. 优先改为受控下载接口或 fetch/blob 模式
3. 后端保留短期兼容读取旧路径
4. 不迁移现有 file_path / file_key 数据
```

- [ ] **Step 3: 修复前端 logout / refresh token 持久化契约**

前端目标：

```text
- logout 调用 /auth/logout
- refresh 成功后覆盖本地 refresh_token
- 老会话升级后可继续使用，不影响已有业务记录
```

- [ ] **Step 4: 为字典删除建立引用扫描服务**

引用扫描至少覆盖：

```python
REFERENCE_MAP = {
    "expense_type": ["expenses_non_contract.expense_type"],
    "payment_category": [...],
    "contract_category": [...],
    "project_category": [...],
}
```

删除逻辑目标：

```text
- 若字典值已被历史记录引用：禁止硬删除
- 提供“停用”而非“删除”
- 若必须替换，要求显式提供 replacement_value，并先校验 replacement_value 已存在
```

- [ ] **Step 5: 专门处理“费用类别”安全性**

必须区分并核实两个概念：

```text
1. expenses_non_contract.category
2. expenses_non_contract.expense_type
3. sys_dictionaries 中现有分类代码 expense_type
4. 文档中历史出现的 expense_category 命名
```

处理策略：

```text
- 不对已存储字段做重命名覆盖式迁移
- 先建立命名映射和兼容层
- 如果要新增“费用类别”字典分类，必须先导出现有 sys_dictionaries 与 expenses_non_contract 中实际值
- 任何新分类上线前，先验证历史记录中的 value 是否全部可回显
```

- [ ] **Step 6: 写字典安全测试**

```python
async def test_cannot_delete_expense_type_dictionary_value_when_referenced(...):
    ...

async def test_can_disable_dictionary_value_without_breaking_existing_expense_reads(...):
    ...

async def test_existing_expense_records_render_when_dictionary_label_changes(...):
    ...
```

- [ ] **Step 7: 运行兼容性测试并提交**

Run:

```bash
PYTHONPATH=backend pytest backend/tests/test_dictionary_safety.py backend/tests/test_file_compatibility.py -v
```

Expected:

```text
PASS
```

Commit:

```bash
git add backend/app/routers/common.py frontend/src/utils/common.js frontend/src/api/auth.js frontend/src/stores/user.js backend/app/routers/system.py backend/app/models/system.py backend/app/models/expense.py backend/app/services/dictionary_usage_service.py backend/tests/test_dictionary_safety.py backend/tests/test_file_compatibility.py
git commit -m "fix: preserve file and dictionary compatibility during upgrade"
```

---

### Task 4: 前端稳定性、可访问性和移动端整改

**Files:**
- Modify: `frontend/src/views/Layout.vue`
- Modify: `frontend/src/views/Login.vue`
- Modify: `frontend/src/views/reports/ReportDashboard.vue`
- Modify: `frontend/src/views/mobile/MobileLayout.vue`
- Modify: `frontend/src/views/mobile/ContractListMobile.vue`
- Modify: `frontend/src/components/ContractQueryBot.vue`
- Modify: `frontend/src/styles/index.scss`
- Modify: `frontend/src/assets/main.scss`
- Create: `frontend/src/styles/tokens.scss`

- [ ] **Step 1: 先做不影响数据与接口契约的前端壳层整改**

范围限制：

```text
- 只改模板语义、按钮、样式 token、响应式布局
- 不改业务接口字段名
- 不改表单提交 payload
- 不改数据展示逻辑含义
```

- [ ] **Step 2: 优先修正可访问性高风险点**

目标：

```text
- clickable div 改为 button / 可聚焦控件
- 关键表单加明确 label
- 状态展示不只依赖颜色
- 次要文字对比度提升
```

- [ ] **Step 3: 统一颜色与间距 token**

目标：

```text
- 建立单一 tokens.scss
- Layout / Login / ReportDashboard / ContractQueryBot 优先切换到 token
- 禁止继续新增硬编码颜色
```

- [ ] **Step 4: 修正移动端复用桌面页的高风险页面**

优先级：

```text
1. reports
2. expenses
3. system management
```

策略：

```text
- 能独立做 mobile 视图的做独立视图
- 暂时不能拆的，至少保证无横向滚动、按钮可点、筛选区可换行
```

- [ ] **Step 5: 降低“现代但花哨”的视觉噪声**

约束：

```text
- 移除大面积渐变背景作为默认工作区底色
- 收敛玻璃态和高饱和辅助色
- 保持企业后台的稳定感
```

- [ ] **Step 6: 运行前端检查并提交**

Run:

```bash
npm --prefix frontend install
npm --prefix frontend run build
```

Expected:

```text
build success
```

Commit:

```bash
git add frontend/src/views/Layout.vue frontend/src/views/Login.vue frontend/src/views/reports/ReportDashboard.vue frontend/src/views/mobile/MobileLayout.vue frontend/src/views/mobile/ContractListMobile.vue frontend/src/components/ContractQueryBot.vue frontend/src/styles/index.scss frontend/src/assets/main.scss frontend/src/styles/tokens.scss
git commit -m "feat: improve frontend accessibility and responsive stability"
```

---

### Task 5: 发布、灰度、回滚与验收

**Files:**
- Create: `docs/release/deployment-checklist-hardening.md`
- Modify: `DEPLOYMENT_CHECKLIST.md`
- Modify: `scripts/monitor.sh`

- [ ] **Step 1: 制定发布顺序**

推荐顺序：

```text
1. 备份
2. 部署后端兼容改动
3. 运行数据库只增量迁移
4. 执行升级验证脚本
5. 部署前端
6. 验证登录 / 文件访问 / 字典管理 / 历史费用记录
```

- [ ] **Step 2: 上线后立即执行冒烟验证**

必须验证：

```text
- 老用户可登录
- 历史上游/下游/管理合同可打开
- 历史无合同费用记录列表与详情可打开
- 历史上传附件可下载/预览
- 现有数据字典项可正常显示
- 新增的费用类别不会覆盖旧值
```

- [ ] **Step 3: 定义回滚门槛**

任一项成立立即回滚：

```text
- 登录失败率显著上升
- 文件访问 404/401 大量增加
- 历史费用记录出现空白类别或详情异常
- 字典接口返回异常，导致录入页不可用
- 数据库迁移耗时异常或阻塞写入
```

- [ ] **Step 4: 明确回滚方式**

```text
- 回滚应用镜像到前一版本
- 保留已执行的兼容性迁移，不做反向删列
- 如需数据恢复，仅从升级前备份中恢复，不直接覆盖线上库
- 对对象存储和 uploads 只做只读校验，不做覆盖式回滚
```

- [ ] **Step 5: 发布文档与最终提交**

```bash
git add docs/release/deployment-checklist-hardening.md DEPLOYMENT_CHECKLIST.md scripts/monitor.sh
git commit -m "docs: add hardening deployment and rollback checklist"
```

---

## Self-Review

### Spec coverage

- 覆盖了代码审查中的后端安全问题：公开注册提权、默认管理员、logout/refresh 契约、异常泄漏。
- 覆盖了审计中的前端问题：可访问性、响应式、主题分裂、过度装饰。
- 覆盖了用户提出的升级约束：历史文件不丢、历史记录不丢、升级后可用、不会导致崩溃。
- 专门覆盖了“费用类别/数据字典”安全性：禁止硬删除、先引用扫描、建立兼容层、不做覆盖式命名迁移。

### Placeholder scan

- 没有使用 TBD/TODO/后续补充之类占位符。
- 所有阶段都包含明确文件、验证目标和提交点。

### Type consistency

- 计划统一使用现有 `sys_dictionaries`、`expenses_non_contract.category`、`expenses_non_contract.expense_type` 命名。
- 明确要求先核实 `expense_type` 与历史文档 `expense_category` 的映射，不直接重命名生产字段。

---

## Execution Notes

- 本计划是“程序级修订计划”，适合先拆成 3 个执行分支：
  1. `auth-hardening`
  2. `file-dictionary-compat`
  3. `frontend-accessibility-responsive`
- 实施时先完成 Task 1，再并行推进 Task 2/3；Task 4 必须建立在 2/3 已稳定的前提上。
- 任何对字典值的修改都必须先导出 `sys_dictionaries` 快照，并对 `expenses_non_contract` 做引用统计。
