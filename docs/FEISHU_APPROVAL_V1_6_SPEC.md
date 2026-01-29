# 飞书审批（V1.6）对接规格 & 无损升级实施方案（基于现网 V1.5.5）

> 目标：新增 **合同审批 / 付款审批 / 无合同费用审批 / 零星用工审批 / 采购审批**，并严格保证现网 V1.5.5 **历史数据与 MinIO 文件无损**。

---

## 0. 总体约束（CRITICAL）

1. **PostgreSQL 是唯一真理来源**：飞书表单数据与附件必须回传并落库（附件存 MinIO，DB 存引用）。
2. **无损升级**：
   - 只允许新增表/新增列；新增列必须 `NULLABLE`，严禁新增 `NOT NULL` 约束。
   - Pydantic 新字段必须 `Optional[...]`。
   - Vue 前端对新字段必须判空渲染，避免 `null` 报错。
3. **审批发起**：员工在飞书 App 填单（不直接访问内网）。
4. **数据同步**：采用 worker 模式将合同数据周期性同步到飞书 Base（多表分类型），用于查询/辅助填报。
5. **审批回调**：审批通过后飞书 Webhook 通知本地；本地异步 **生成** 审批流程 PDF 并归档到 MinIO（不依赖飞书直接导出 PDF）。
6. **部署**：Docker Compose，`backend`（Web）+ `sync-worker`（后台任务）两个独立容器。

---

## 1. 审批模板标识（approval_code）

建议统一命名并在飞书审批模板中配置：

- 合同审批：`LH_CONTRACT_APPROVAL_V1`
- 付款申请：`LH_PAYMENT_APPLICATION_V1`
- 无合同费用：`LH_NON_CONTRACT_EXPENSE_V1`
- 零星用工：`LH_ZERO_HOUR_LABOR_V1`
- 采购计划：`LH_PROCUREMENT_PLAN_V1`

> 说明：系统侧也做成可配置项（便于后续飞书侧变更不发版）。

---

## 2. “稳定字段标识”策略（field_code）

飞书审批实例详情中，字段解析应以 **field_code（飞书生成的字段编码）** 为准，而不是中文字段名。

落地方案：
1. 我方先定义“逻辑字段名（logical_key）+ 中文名 + 控件类型”的模板规范（见第 3 节）。
2. 飞书侧按规范创建模板后：
   - 我方提供一个“同步/登记”入口（管理端 API 或脚本），将：
     - `approval_code`
     - 每个字段的 `logical_key -> field_code`
     写入 Postgres（例如 `sys_config` 或专用映射表）。
3. Webhook 收到 `instance_code` 后，拉取实例详情，按已登记的 `field_code` 解析并落库。

---

## 3. 五类模板字段规范（飞书侧按此建模）

### 3.1 合同审批（飞书内完成；系统仅手工上传“合并件”）
必填：
- `contract_type`：单选（上游合同/下游合同/管理合同）
- `contract_name`：文本
- `party_a_name`：文本
- `party_b_name`：文本
- `contract_amount`：金额
- `draft_contract_pdfs`：附件（可 1 个或多个，PDF，≤30MB/个）

产物：
- 飞书内导出：审批流程 PDF + 合同初稿 PDF
- 人工合并后，在系统录入/编辑合同时上传到“合同审批合并件”字段（见第 4.3 节）

### 3.2 付款申请（新增“付款申请单”表；审批通过自动归档 PDF）
发起人必填：
- `contract_type`：单选（下游合同/管理合同）
- `contract_serial_number`：数字（合同序号）
- `payment_category`：单选（预付款/进度款/完工款/结算款/质保金）
- `planned_amount`：金额
- `planned_pay_date`：日期（date）

流程回填（只读展示；由飞书 HTTP 节点调用本地查询接口）：
- `upstream_contract_name`
- `upstream_received_total`
- `contract_amount`
- `contract_payable_total`
- `contract_invoiced_total`
- `contract_paid_total`

审批通过后：
- 本地生成审批流程 PDF -> 归档至 MinIO -> 写回 `payment_applications.approval_pdf_*`

### 3.3 无合同费用（飞书填报；必须落库 Postgres；附件多文件）
必填：
- `upstream_contract_serial_number`：数字（上游合同序号）
- `upstream_contract_name`：文本（上游合同名称）
- `expense_category`：单选（公司费用/项目费用）
- `expense_type`：单选（费用分类）
- `amount`：金额
- `expense_date`：日期（date）
选填：
- `description`：多行文本
附件（多文件，PDF，≤30MB/个）：
- `invoice_attachments`：发票附件（多个）
- `reimburse_attachments`：报销凭证（多个）

说明：
- 落库必须同时保存“上游合同序号+名称”快照字段（避免仅依赖外键导致信息丢失）。
- 审批通过后：本地生成审批流程 PDF 并归档到 MinIO，写回 `expenses_non_contract.approval_pdf_*`。

### 3.4 零星用工（飞书只生成 PDF；系统手工建单并上传审批 PDF）
必填（示例）：
- `upstream_contract_serial_number`：数字（上游合同序号）
- `upstream_contract_name`：文本（上游合同名称）
- `work_location`：文本（用工地点）
- `planned_work_date`：日期（计划用工时间）
- `dispatch_unit`：文本（用工单位/派工单位）
- 明细（子表/重复组）：`job_type`、`quantity`、`material_name`、`material_quantity_note`

流程回填（只读展示；HTTP 节点调用本地查询接口）：
- `sent_zero_hour_total_amount`（按上游合同全历史汇总）

审批完成后：
- 飞书提供审批流程 PDF 下载（人工下载）
- 系统侧在零星用工单增加“零星用工审批文件”字段：人工上传（不自动）

### 3.5 采购计划（飞书生成采购计划单 PDF；系统手工上传；多份历史）
必填：
- `contract_type`：单选（下游合同/管理合同）
- `contract_serial_number`：数字
建议（前端必填，DB 可空）：
- `plan_date`：日期（计划日期）
选填：
- `remark`：多行文本（备注）
明细（子表/重复组）：
- `material_name`、`brand`、`spec_model`、`quantity`

审批完成后：
- 飞书生成“采购计划单 PDF”（可下载）
- 系统侧“采购计划历史”支持多份上传（不自动）

---

## 4. 后端数据库/模型改造（只增不改）

### 4.1 新表：付款申请单 `payment_applications`
核心字段（全部可空或有默认，避免破坏升级）：
- `contract_type`（downstream/management）
- `contract_serial_number`（int）
- `payment_category`（string）
- `planned_amount`（numeric）
- `planned_pay_date`（date）
- `feishu_instance_code`（unique，可空）
- `approval_status`（DRAFT/PENDING/APPROVED/REJECTED）
- `approval_pdf_path/key/storage`
- 可选：回填的 6 项金额快照（用于审计留痕）

### 4.2 新表：无合同费用附件 `expense_attachments`
- `expense_id`（FK）
- `attachment_type`（INVOICE/REIMBURSE）
- `file_path/file_key/storage_provider`
- `original_filename`

> 兼容策略：保留 `expenses_non_contract.file_*` 作为“旧单附件（单文件）”；新飞书单据使用附件子表（多文件）。

### 4.3 合同表新增字段：合同审批合并件（三表）
在 `contracts_upstream` / `contracts_downstream` / `contracts_management` 新增：
- `contract_approval_file_path`
- `contract_approval_file_key`
- `contract_approval_file_storage`

### 4.4 新表：采购计划历史 `procurement_plans`
- 关联对象：下游合同/管理合同
- 字段：
  - `contract_type`（downstream/management）
  - `contract_id`（FK，优先）
  - `plan_date`（date，DB 可空）
  - `remark`（text，可空）
  - `file_path/file_key/storage_provider`

### 4.5 零星用工：手工上传审批文件
复用现有 `zero_hour_labor.approval_pdf_*`，补齐 Update Schema/接口允许写入。

### 4.6 启动自愈（必做）
将所有新增列加入 `backend/app/core/db_check.py` 的 required columns，以确保生产库缺列时自动补齐（仅添加列，不做 destructive 变更）。

---

## 5. 后端 API 设计（飞书可直连；Token 鉴权）

### 5.1 飞书 Webhook（审批回调）
- `POST /api/feishu/webhook`
  - 校验：verification token（最少），并做幂等（按 `instance_code`）
  - 按 `approval_code` 路由：
    - 付款申请：创建/更新 `payment_applications`，审批通过生成并归档 PDF
    - 无合同费用：创建/更新 `expenses_non_contract` + `expense_attachments`，审批通过归档 PDF
    - 其他流程：仅更新状态/记录（按需求）

### 5.2 飞书 HTTP 回填查询（审批表单内 HTTP 节点调用）
统一鉴权：`Authorization: Bearer <FEISHU_HTTP_API_TOKEN>`

- 付款回填：`POST /api/feishu/query/payment-context`
  - 入参：`contract_type` + `contract_serial_number`
  - 出参：6 项金额 + 上游合同名称
- 零星用工回填：`POST /api/feishu/query/zero-hour-summary`
  - 入参：`upstream_contract_serial_number`
  - 出参：`sent_zero_hour_total_amount`

### 5.3 审批字段映射登记（管理端）
建议提供一个管理端接口（或 CLI 脚本）：
- `POST /api/v1/system/feishu/mappings/sync`
  - 从飞书拉取指定 `approval_code` 模板结构，写入 `logical_key -> field_code` 映射

---

## 6. PDF 归档策略（后端生成）

### 6.1 生成来源
- Webhook 收到 `instance_code` 后：
  1) 调用飞书 OpenAPI 拉取审批实例详情（审批人节点、意见、时间等）
  2) 使用 `reportlab` 渲染为审批流程 PDF
  3) 上传到 MinIO（建议 key 前缀：`feishu/approvals/{approval_code}/{instance_code}.pdf`）
  4) 写回业务表的 `approval_pdf_*`

### 6.2 字体
- 需要内置中文字体（TTF）进镜像或挂载（避免 reportlab 中文乱码）。

---

## 7. Worker 模式：合同数据同步到飞书 Base（多表分类型）

现状：代码里仅同步“上游合同”到单一 Base table。

V1.6 规划：
- 同步三类合同到 Base 的三个 table：
  - Upstream table：包含 `serial_number`、`contract_code`、`contract_name`、`party_a_name`、`party_b_name`、`contract_amount`、`status`、`sign_date`
  - Downstream table：至少包含 `serial_number`、`contract_name`、`party_b_name`、`contract_amount`、`upstream_serial_number`
  - Management table：同下游
- 环境变量拆分：
  - `FEISHU_BASE_UPSTREAM_TABLE_ID`
  - `FEISHU_BASE_DOWNSTREAM_TABLE_ID`
  - `FEISHU_BASE_MANAGEMENT_TABLE_ID`

---

## 8. Cloudflare 托管域名 + 本地服务器：最流畅接入方案

建议使用 **Cloudflare Tunnel（cloudflared）**，无需端口映射、无需固定公网 IP。

推荐域名划分：
- `app.xxx.com`：给人使用（前端+系统 API）
- `feishu.xxx.com`：仅给飞书使用（webhook + 回填查询）

Tunnel 入口建议指向本地 Nginx（80）：
- `feishu.xxx.com` -> `http://127.0.0.1:80`
- 飞书配置：
  - Webhook：`https://feishu.xxx.com/api/feishu/webhook`
  - 回填接口：`https://feishu.xxx.com/api/feishu/query/*`

Cloudflare 规则建议：
- 对 `feishu.xxx.com` 禁用缓存（Cache Bypass）
- 不启用需要交互登录的 Access（用 `FEISHU_HTTP_API_TOKEN` 鉴权更稳）

---

## 9. 需要业务方/管理员配合的输入清单

1) 5 个审批模板创建完成（使用本文件的 approval_code 与字段规范）
2) 开通飞书应用权限：审批实例读取、附件下载
3) 配置事件订阅：审批实例状态变更事件（指向 webhook URL）
4) 提供 Base 的 app_token 与三张表的 table_id

