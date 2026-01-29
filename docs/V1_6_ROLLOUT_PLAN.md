# V1.6（审批增强）上线执行计划（飞书 + Cloudflare + 系统代码）

> 适用：现网已部署运行 V1.5.5（数据与 MinIO 文件不可丢失）

---

## 0. 上线前统一准备（建议先做）

1) **备份**
- PostgreSQL：做一次全库备份（或快照）
- MinIO：至少做桶级快照/备份（或导出对象清单 + 增量备份策略）

2) **确认域名与 Tunnel**
- 现网外网域名：`cm.lhdl.cc`
- Cloudflare Tunnel：已运行在 Docker Host 本机（作为入口）

3) **确认限制**
- 飞书附件：仅 PDF，单文件 ≤30MB
- 付款申请：`planned_pay_date` 使用 `date`
- 采购计划：`plan_date` 前端必填、DB 可空（nullable）

---

## 1. 飞书（先完成 Base + 审批流程）

### 1.1 飞书 Base（多表分类型）
目标：3 张表分别同步上游/下游/管理合同，用于飞书端检索/辅助填报。

操作：
1) 在飞书创建一个 Base（多维表格）
2) 在同一 Base 下创建 3 张表（建议命名）：
   - `UpstreamContracts`
   - `DownstreamContracts`
   - `ManagementContracts`
3) 每张表至少包含字段（可按你们习惯扩展）：
   - `serial_number`（合同序号）
   - `contract_code`（合同编号）
   - `contract_name`（合同名称）
   - `contract_amount`（签约金额）
   - `status`（状态）
   - 下游/管理建议加：`upstream_serial_number`（关联上游序号）与 `upstream_contract_name`（名称快照）

交付物（后续代码需要）：
- `FEISHU_BASE_APP_TOKEN`
- 3 个表的 `table_id`

### 1.2 五个审批模板（先建模板，再由系统登记 field_code）

系统内部流程类型（建议 approval_code/别名）：
- 合同审批：`LH_CONTRACT_APPROVAL_V1`
- 付款申请：`LH_PAYMENT_APPLICATION_V1`
- 无合同费用：`LH_NON_CONTRACT_EXPENSE_V1`
- 零星用工：`LH_ZERO_HOUR_LABOR_V1`
- 采购计划：`LH_PROCUREMENT_PLAN_V1`

> 注：若飞书不支持“自定义 approval_code”，则以飞书实际生成的 `approval_code` 为准；系统侧会建立映射（流程类型 -> 飞书 approval_code + field_code）。

#### A) 付款申请（发起必填 + HTTP 回填展示）
发起必填：
- 合同类型（下游/管理）
- 合同序号（数字）
- 付款类别（预付款/进度款/完工款/结算款/质保金）
- 计划支付金额
- 计划支付时间（date）

回填展示（只读；通过“HTTP 节点”调用系统接口后写入）：
- 上游合同名称
- 上游合同回款金额
- 本合同签订金额
- 本合同应付款金额
- 挂账金额
- 已付款金额

#### B) 无合同费用（必填 + 两类多附件）
必填：
- 上游合同序号、上游合同名称
- 费用归属（公司费用/项目费用）
- 费用分类
- 金额
- 日期
选填：
- 说明
附件（多文件）：
- 发票（多个，PDF ≤30MB/个）
- 报销凭证（多个，PDF ≤30MB/个）

#### C) 零星用工（只生成 PDF；系统手工建单+上传审批 PDF）
必填：
- 上游合同序号、名称
- 用工地点、计划用工时间（date）、用工单位/派工单位
- 工种/数量、材料名称、数量信息（建议用明细表/重复组）
回填展示（只读；HTTP 节点调用）：
- 已发送零星用工总价金额（按上游合同全历史汇总）

#### D) 采购计划（飞书生成采购计划单 PDF；系统手工上传；多份历史）
必填：
- 合同类型（下游/管理）
- 合同序号
建议：
- 计划日期（plan_date）
- 备注（remark，可选）
明细表：
- 材料名称、品牌、规格型号、数量

#### E) 合同审批（飞书内完成；系统手工合并上传）
- 模板内产生：审批流程 PDF + 合同初稿 PDF（飞书侧可下载）
- 人工合并后，系统合同录入/编辑时上传“合并件 PDF”

### 1.3 飞书事件订阅（Webhook）
1) 在飞书开放平台配置事件订阅：
- 订阅事件：审批实例状态变更（例如 status_changed）
- 回调地址：`https://cm.lhdl.cc/api/feishu/webhook`
- Verification Token：生成并保存（将写入系统 `.env`）
- Encrypt Key：不启用（按当前约定）

验收：
- 飞书“URL 验证”通过

---

## 2. Cloudflare（在写代码前先打通链路）

目标：飞书能稳定访问 `cm.lhdl.cc` 的 webhook 与回填接口，不被缓存/WAF/挑战拦截。

### 2.1 Tunnel 入口确认
在 Cloudflare Zero Trust 控制台：
- Tunnels -> 选当前 tunnel -> Public Hostnames
  - 确保 `cm.lhdl.cc` 指向本机 Nginx：`http://127.0.0.1:80`（或实际监听地址）

### 2.2 安全/缓存绕过规则（建议）
在 Cloudflare Dashboard（站点级规则）：
- 对路径前缀 `/api/feishu/*`：
  - Cache：Bypass
  - WAF/Managed Challenge：Skip（避免飞书请求被挑战）
  - Rate limiting：如开启过，需对该路径放行或提高阈值

### 2.3 验收（不依赖系统新代码也可先测）
- `https://cm.lhdl.cc/health` 可访问
- `https://cm.lhdl.cc/api/feishu/webhook`（POST）应能到达后端（后续代码会处理 challenge）

---

## 3. 系统代码编写（最后进行；严格无损升级）

后端：
- 新增表：付款申请单、无合同费用附件、采购计划历史
- 旧表新增可空列：合同审批合并件字段；零星用工审批文件字段（手工上传）
- 新增飞书回填查询接口（Token 鉴权）
- webhook 幂等落库 + reportlab 生成审批流 PDF -> MinIO 归档
- worker：扩展为同步三类合同到 Base 三表

前端：
- 合同：新增“合同审批合并件 PDF”上传
- 下游/管理：新增“采购计划历史”列表（多份上传，plan_date 必填）
- 零星用工：新增“审批 PDF”手工上传
- 无合同费用：展示两类多附件 + 审批 PDF

---

## 4. 你需要提供给开发的最终参数清单（飞书完成后）

- `FEISHU_APP_ID` / `FEISHU_APP_SECRET`
- `FEISHU_BASE_APP_TOKEN`
- `FEISHU_BASE_UPSTREAM_TABLE_ID` / `FEISHU_BASE_DOWNSTREAM_TABLE_ID` / `FEISHU_BASE_MANAGEMENT_TABLE_ID`
- 飞书 5 个流程的实际 `approval_code`（如果飞书允许自定义则与本计划一致；否则把飞书生成的 code 发我）
- `FEISHU_WEBHOOK_VERIFICATION_TOKEN`
- 计划设置的 `FEISHU_HTTP_API_TOKEN`（我可生成并给你放进 `.env`）

