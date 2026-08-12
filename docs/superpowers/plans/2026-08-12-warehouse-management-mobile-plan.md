# 多库房及手机库管模块实施计划

> 本文件定义 `LH_Contract_Docker` 库房管理模块的业务边界、数据模型、权限、接口、手机端交互、迁移步骤和验收标准。本阶段只落盘计划，不修改业务代码。

## 1. 目标

在现有 FastAPI + PostgreSQL + Vue 3 系统内新增“库房管理”模块，替代多人在线 Excel 作为正式库存数据源，使库管可以通过手机完成入库、出库、项目/库房调拨和盘点，公司管理人员可以实时查看多库房、多项目库存与流水。

首期采用响应式 Web 移动端，不单独开发 Android/iOS 原生应用；复用现有登录、JWT、RBAC、审计、Docker、PostgreSQL、Redis、MinIO 和 Vue/Vant 移动端基础。

## 2. 已确认业务规则

### 2.1 角色

新增两个系统角色：

- `WAREHOUSE_ADMIN`：库房管理员。
- `COMPANY_STOREKEEPER`：公司库管。

权限边界：

| 能力 | 库房管理员 | 公司库管 |
| --- | --- | --- |
| 查看库存和流水 | 全部库房 | 仅获授权库房 |
| 入库、出库 | 全部库房 | 仅获授权库房 |
| 调拨 | 全部库房 | 调出库房必须在授权范围内 |
| 盘点录入 | 全部库房 | 仅获授权库房 |
| 盘点确认/差异过账 | 允许 | 不允许 |
| 物资档案维护 | 允许 | 只读 |
| 项目、库房、货位维护 | 允许 | 只读 |
| 价格、合同、验收补录 | 允许 | 不允许 |
| Excel 导入 | 允许 | 不允许 |
| Excel 导出 | 允许 | 允许导出授权范围 |
| 冲销已过账单据 | 允许并必须填写原因 | 不允许 |

补充规则：

- 系统 `ADMIN`/超级管理员继承全部库房权限。
- 为满足“管理人员实时可见”，`COMPANY_LEADER` 首期获得全部库房库存与报表只读权限，不获得任何过账权限。
- 其他现有角色默认无库房模块权限，避免因既有角色扩权造成数据泄露。
- 公司库管与库房使用关联表授权，并可设置一个默认库房；后端必须执行数据范围校验，不能只依赖前端隐藏菜单。

### 2.2 多库房、项目与货位

- 系统支持多个库房，每个库房有独立编码、名称、地址、负责人和启停状态。
- 每个库房包含多个货位；启用库房时至少建立一个“暂存区”货位。
- 项目不是物资编码的一部分。同规格、同厂家、同成色、同供应方式的物资在不同项目使用同一物资编码。
- 库存最小核算维度为：

```text
库房 + 货位 + 所属项目 + 物资
```

- 项目主数据由库房模块统一维护，可选关联一份上游合同，但不直接使用合同的自由文本 `project_name` 作为库存外键。
- 同一物资可以同时存在于多个项目、多个库房和多个货位，库存互不混用。

### 2.3 物资编码

物资编码由服务端自动生成，格式固定为：

```text
类别-供应/成色-流水号
```

示例：

| 编码 | 含义 |
| --- | --- |
| `ZC-J-001` | 主材、甲供、新料 |
| `ZC-Y-001` | 主材、乙供、新料 |
| `ZC-JF-001` | 主材、甲供、废旧回收 |
| `ZC-YF-001` | 主材、乙供、废旧回收 |
| `FC-J-001` | 辅材、甲供、新料 |
| `GJ-Y-001` | 工器具、乙供、新料 |

编码规则：

- 类别前缀首期为 `ZC`（主材）、`FC`（辅材）、`GJ`（工器具）、`LB`（劳保）。
- 中段为 `J`、`Y`、`JF`、`YF`。
- 流水号按“类别 + 中段”分别递增，至少三位；超过 999 后自然扩展为四位。
- 编码一经生成不可修改，也不可回收复用；停用物资使用归档状态。
- 编号必须在 PostgreSQL 事务中通过计数器行锁生成，防止两名管理员并发创建出重复编号。
- 业务唯一性继续采用“名称 + 品牌/厂家 + 规格 + 单位 + 成色 + 供应方式”的标准化组合，并在服务端做重复提示/约束。
- 从现有 Excel 迁移时保留 `legacy_code`，例如把 `ZC-001J` 映射到 `ZC-J-001`，以便历史追溯。

### 2.4 入库、出库和库存

- 入库必须选择库房、货位、所属项目、物资、数量、日期和经办人。
- 出库必须选择调出库房、货位、所属项目、物资、数量、日期和经办人。
- 数量必须大于零；出库不得使对应库存维度出现负数。
- 入库业务类型首期包括：采购入库、领用退回、拆除回收、期初、盘盈。
- 出库业务类型首期包括：领用出库、退废旧、报废、盘亏。
- 甲供、乙供依靠物资编码中的供应属性区分，不允许在单据上临时改变物资供应方式。
- 已过账单据不可直接编辑或物理删除；错误记录必须创建反向冲销流水并保存原因。

### 2.5 调拨

调拨不设置审批流程，提交成功后立即过账。

一张调拨单必须包含：

- 物资及数量。
- 调出库房、调出货位、调出项目。
- 调入库房、调入货位、调入项目。
- 调拨日期、经办人、调拨依据和备注。

调拨支持三种场景：

1. 同库房不同项目调拨。
2. 同项目不同库房/货位调拨。
3. 库房和项目同时变化。

控制规则：

- 调出维度与调入维度不得完全相同。
- 调出库存不足时拒绝提交。
- 调拨在同一数据库事务内同时写入调出负流水和调入正流水，禁止只成功一侧。
- 不建立 `pending_approval`、`approved` 等审批状态；首期状态只保留 `DRAFT`、`POSTED`、`VOIDED`。
- 手机端默认直接提交并过账；网络重试必须使用幂等键，防止双击造成重复调拨。
- 甲供调拨暂不审批，但仍要求填写调拨依据并记录完整审计日志。

### 2.6 扫码

- 首期二维码代表物资，不代表库存数量或项目。
- 批量物资优先在货位卡、包装箱或整盘材料上贴码；贵重工器具后续可扩展为单件资产码。
- 二维码内容使用不可变标识或系统链接，例如：

```text
https://<domain>/m/warehouse/materials/<material-id>
```

- 扫码后显示物资名称、编码、规格、甲乙供属性，并要求用户选择/确认库房、货位、项目和业务类型。
- 可选增加货位二维码，先扫物资再扫货位，减少手工选择。
- 扫码依赖 HTTPS 和摄像头权限；使用浏览器 `BarcodeDetector`，不支持时回退到成熟扫码库。
- 首期不实现离线过账；断网时保留表单草稿提示，但不得假装提交成功。

## 3. 技术架构

### 3.1 实现方式

- 后端继续使用 FastAPI、SQLAlchemy 2.0 Async、PostgreSQL 和 Alembic。
- 前端继续使用 Vue 3；PC 管理端使用 Element Plus，手机操作端使用现有 Vant 移动路由。
- 使用现有 JWT 和刷新令牌；不新增独立登录系统。
- 使用现有审计服务记录建档、入库、出库、调拨、盘点、冲销、导入和导出。
- Docker Compose 中不新增独立微服务，库房模块随现有 backend/frontend 发布。
- Excel 只作为初始化导入和报表导出格式；系统上线后数据库是唯一正式库存源，不做 Excel 双向实时同步。

### 3.2 账务模型

采用“业务单据 + 不可变库存流水 + 当前余额”的三层模型：

```text
业务单据/明细
      ↓ 过账
不可变库存流水 ledger_entries
      ↓ 同事务更新
当前余额 stock_balances
```

- 业务单据用于表达入库、出库、调拨、盘点和冲销的业务含义。
- 库存流水是事实来源，每一行有正负数量和完整维度。
- 当前余额是性能表，可从流水重建，不能由前端直接修改。
- 报表优先查询余额表，审计和重建使用流水表。

### 3.3 并发与一致性

所有影响库存的过账服务必须：

1. 开启数据库事务。
2. 按稳定顺序锁定涉及的 `stock_balances` 行（`SELECT ... FOR UPDATE`）。
3. 重新读取实际库存并校验非负。
4. 写入单据、明细和库存流水。
5. 原子更新余额。
6. 写入审计日志。
7. 一次性提交；任一步失败则全部回滚。

移动端提交携带 `Idempotency-Key`。后端保存请求键和结果摘要；同一用户重复提交同一键时返回原结果，不重复过账。

## 4. 建议数据模型

### 4.1 主数据

#### `warehouse_warehouses`

- `id`, `code`, `name`, `address`, `manager_name`
- `is_active`, `created_by`, `created_at`, `updated_at`
- `code` 和 `name` 分别唯一。

#### `warehouse_locations`

- `id`, `warehouse_id`, `code`, `name`, `description`
- `is_default`, `is_active`, 时间和创建人字段。
- 唯一约束：`warehouse_id + code`。

#### `warehouse_projects`

- `id`, `code`, `name`, `upstream_contract_id`
- `is_active`, `created_by`, `created_at`, `updated_at`
- `upstream_contract_id` 可空；项目独立存在，不依赖合同生命周期。

#### `warehouse_materials`

- `id`, `code`, `legacy_code`
- `category`, `supply_type`, `condition`
- `name`, `brand`, `specification`, `unit`
- `minimum_stock`, `description`, `is_active`
- 时间、创建人和更新人字段。
- `code` 唯一且不可修改。

#### `warehouse_code_counters`

- `category`, `supply_condition`, `next_number`
- 联合主键：`category + supply_condition`。
- 只允许编码生成服务在事务和行锁内更新。

#### `warehouse_user_scopes`

- `user_id`, `warehouse_id`, `is_default`
- 联合唯一约束：`user_id + warehouse_id`。
- 用户停用或库房停用时接口不得继续过账。

### 4.2 库存与单据

#### `warehouse_documents`

- `id`, `document_no`, `document_type`, `status`
- `occurred_on`, `business_type`, `reference_no`, `description`
- `idempotency_key`, `created_by`, `posted_by`, `voided_by`
- `created_at`, `posted_at`, `voided_at`, `void_reason`
- `document_no` 唯一；`created_by + idempotency_key` 唯一。

`document_type`：`INBOUND`、`OUTBOUND`、`TRANSFER`、`COUNT_ADJUSTMENT`、`REVERSAL`。

#### `warehouse_document_lines`

- `id`, `document_id`, `line_no`, `material_id`, `quantity`
- `source_warehouse_id`, `source_location_id`, `source_project_id`
- `target_warehouse_id`, `target_location_id`, `target_project_id`
- `original_document_line_id`, `description`
- 入库只填目标维度，出库只填源维度，调拨同时填两侧维度。

#### `warehouse_ledger_entries`

- `id`, `document_id`, `document_line_id`
- `warehouse_id`, `location_id`, `project_id`, `material_id`
- `quantity_delta`, `occurred_on`, `created_at`
- 调拨一条明细生成两条流水，数量一负一正。
- 唯一约束阻止同一明细同一方向重复入账。

#### `warehouse_stock_balances`

- `warehouse_id`, `location_id`, `project_id`, `material_id`
- `quantity`, `version`, `updated_at`
- 联合唯一约束覆盖四个库存维度。
- `quantity >= 0` 数据库检查约束作为最后一道保护。

#### `warehouse_counts` / `warehouse_count_lines`

- 盘点范围、盘点日期、状态、盘点人和确认人。
- 明细保存账面快照、实盘数量、差异和调整单据 ID。
- 公司库管录入实盘，库房管理员确认后生成盘盈/盘亏流水。

#### `warehouse_business_supplements`

- 关联入库/出库明细。
- 保存送货单、验收、合同、厂家、价格类型、单价、金额、过磅、残值和管理备注。
- 数量账与价格补录分离，修改补录不得改变库存。

## 5. 权限改造

### 5.1 用户角色

在 `backend/app/models/user.py` 的 `UserRole` 增加：

- `WAREHOUSE_ADMIN = "WAREHOUSE_ADMIN"`
- `COMPANY_STOREKEEPER = "COMPANY_STOREKEEPER"`

同步更新：

- 角色显示名称。
- 用户 Schema/OpenAPI 枚举。
- 初始化和用户管理下拉。
- 前端角色文案和菜单控制。
- 角色迁移及回滚测试。

### 5.2 新增权限

在 `backend/app/core/permissions.py` 增加至少以下权限：

- `VIEW_WAREHOUSE_INVENTORY`
- `VIEW_ALL_WAREHOUSES`
- `MANAGE_WAREHOUSE_MASTER`
- `MANAGE_WAREHOUSE_MATERIALS`
- `POST_WAREHOUSE_INBOUND`
- `POST_WAREHOUSE_OUTBOUND`
- `POST_WAREHOUSE_TRANSFER`
- `ENTER_WAREHOUSE_COUNT`
- `CONFIRM_WAREHOUSE_COUNT`
- `VOID_WAREHOUSE_DOCUMENT`
- `MANAGE_WAREHOUSE_SUPPLEMENTS`
- `IMPORT_WAREHOUSE_DATA`
- `EXPORT_WAREHOUSE_DATA`
- `VIEW_WAREHOUSE_REPORTS`

除权限枚举外，Service 查询必须注入“授权库房集合”条件；对单条资源操作时重新检查资源所属库房。

## 6. 后端接口

统一前缀：`/api/v1/warehouse`。

### 6.1 主数据

- `GET/POST /warehouses`
- `GET/PUT /warehouses/{id}`
- `GET/POST /warehouses/{id}/locations`
- `GET/POST /projects`
- `GET/PUT /projects/{id}`
- `GET/POST /materials`
- `GET/PUT /materials/{id}`
- `GET /materials/search?q=`
- `GET/PUT /users/{user_id}/warehouse-scopes`

### 6.2 库存和流水

- `GET /stock-balances`
- `GET /stock-balances/materials/{material_id}`
- `GET /ledger`
- `GET /documents`
- `GET /documents/{id}`
- `POST /documents/{id}/void`

查询支持库房、货位、项目、物资、甲乙供、成色、日期和状态过滤。

### 6.3 业务过账

- `POST /inbounds`
- `POST /outbounds`
- `POST /transfers`
- `POST /counts`
- `PUT /counts/{id}/lines`
- `POST /counts/{id}/confirm`
- `GET/PUT /documents/{id}/supplement`

所有写接口使用 Pydantic 严格校验、权限检查、库房范围检查、幂等键和库存事务服务。

### 6.4 导入导出与标签

- `POST /imports/excel/validate`：只校验并返回问题，不写数据库。
- `POST /imports/excel/commit`：以校验批次提交导入。
- `GET /exports/materials.xlsx`
- `GET /exports/stock.xlsx`
- `GET /exports/ledger.xlsx`
- `GET /materials/{id}/qr`：生成物资二维码图片或打印页。
- `GET /locations/{id}/qr`：生成货位二维码。

## 7. 前端与手机端

### 7.1 PC 管理端

新增一级菜单“库房管理”，包含：

- 库存总览。
- 物资档案。
- 库房与货位。
- 项目档案。
- 入库单、出库单、调拨单。
- 盘点。
- 业务补录。
- 流水与报表。
- Excel 导入导出。

建议路由：

```text
/warehouse/overview
/warehouse/materials
/warehouse/warehouses
/warehouse/projects
/warehouse/inventory
/warehouse/inbounds
/warehouse/outbounds
/warehouse/transfers
/warehouse/counts
/warehouse/ledger
/warehouse/reports
```

### 7.2 手机端

建议路由：

```text
/m/warehouse
/m/warehouse/scan
/m/warehouse/inbound
/m/warehouse/outbound
/m/warehouse/transfer
/m/warehouse/count
/m/warehouse/inventory
/m/warehouse/history
```

公司库管的移动首页以操作为中心：

- 扫码。
- 入库。
- 出库。
- 调拨。
- 盘点。
- 查库存。
- 最近流水。

交互要求：

- 使用 Vant 表单、选择器、数字键盘和底部固定提交区。
- 点击目标不小于 44px；主流程避免横向表格。
- 默认带入用户默认库房和最近使用项目/货位，但提交前清晰展示。
- 选物资后实时查询当前维度可用库存。
- 提交按钮防重复点击；等待期间展示明确状态。
- 后端库存冲突返回当前最新库存，前端提示用户刷新而不是覆盖。
- 手机端菜单按权限动态展示；公司库管登录后优先进入 `/m/warehouse`。

首期保持在线使用；可增加 Web App Manifest 以便添加到手机桌面，但 Service Worker 不缓存待提交库存业务，避免离线重复过账。

## 8. Excel 数据迁移

现有 `库房管理表.xlsx` 用于一次性迁移，不作为上线后的并行数据源。

迁移步骤：

1. 确定切换时间，冻结 Excel 写入并保存原文件及 SHA-256。
2. 先创建库房和货位；旧表无库房信息时由管理员为批次指定默认库房/暂存区。
3. 导入基础设置中的项目、货位和人员字典。
4. 导入物资档案，按新规则生成 `ZC-J-001` 等编码，并保存旧编码映射。
5. 导入入库、出库和项目调拨历史，保留原编号、日期、经办人及备注。
6. 导入管理补录数据，并关联到对应业务明细。
7. 按“库房 + 货位 + 项目 + 物资”重算余额。
8. 将系统余额与 Excel 余额逐项对账，生成差异报告；存在差异时不得切换生产。
9. 完成管理人员签字确认后，将 Excel 设为只读历史档案。

导入必须有预检页，至少报告：

- 无法识别或重复的物资。
- 缺失项目、库房、货位。
- 数量、日期和业务类型错误。
- 出库超过累计可用库存。
- 旧编码到新编码的映射表。
- 导入后余额差异。

## 9. 实施任务

### 任务 1：冻结业务规格和原型

- 确认两个角色权限矩阵、库房授权方式和管理人员只读范围。
- 确认物资类别、单位、成色、业务类型字典。
- 确认调拨立即过账、冲销规则和单号格式。
- 输出手机端入库、出库、调拨、盘点线框和字段清单。

验收：规格中的所有必填字段、状态和权限无歧义。

### 任务 2：角色、权限和库房范围

- 新增两个 `UserRole` 及显示名称。
- 新增库房权限枚举和角色映射。
- 建立用户-库房授权模型、迁移和管理接口。
- 改造前后端菜单，使权限与数据范围同时生效。

验收：公司库管不能通过直接调用 API 查看或操作未授权调出库房。

### 任务 3：主数据与编码服务

- 建立库房、货位、项目、物资和编码计数器模型。
- 实现 `ZC-J-001` 编码生成、不可变控制和重复物资校验。
- 实现 PC 管理页面和手机物资搜索。

验收：并发创建 20 个同类别物资不重号、不跳回、不复用已归档编码。

### 任务 4：库存引擎

- 建立单据、明细、流水和余额模型。
- 实现统一过账服务、行锁、非负校验、幂等和冲销。
- 增加余额重建/核对管理命令。

验收：任意单据失败不产生部分流水；余额可由流水完全重建且结果一致。

### 任务 5：入库和出库

- 实现入库、出库 API、PC 列表和手机表单。
- 实现项目、库房、货位、物资联动和可用库存提示。
- 实现最近流水和单据详情。

验收：两名用户并发出库时最多一笔可消耗最后库存，余额不为负。

### 任务 6：无审批调拨

- 实现单行/多行调拨单和立即过账事务。
- 支持同库房跨项目、同项目跨库房以及同时跨库房跨项目。
- 公司库管调出库房必须在授权范围；库房管理员不受此限制。
- 实现调拨冲销，禁止直接编辑已过账调拨。

验收：调拨前后公司总量守恒，任何异常都不允许只写入一侧。

### 任务 7：盘点和管理补录

- 实现按库房/货位/项目创建盘点范围和账面快照。
- 公司库管录入实盘；库房管理员确认差异并生成调整流水。
- 实现合同、验收、价格、过磅和残值补录。

验收：补录价格不改变库存；盘点确认只生成一次调整流水。

### 任务 8：手机扫码和标签

- 增加摄像头扫码、物资/货位二维码识别和权限错误状态。
- 实现二维码打印页及批量导出。
- 在 HTTPS 真机环境验证主流 Android/iOS 浏览器。

验收：扫码后正确定位物资，二维码不包含库存、价格等动态或敏感信息。

### 任务 9：报表和 Excel 导入导出

- 实现多库房库存、项目库存、甲乙供、低库存和流水报表。
- 实现现有 Excel 的预检、映射、导入和对账。
- 输出新格式 Excel 报表，但不允许反向覆盖数据库。

验收：迁移后每个库存维度与确认口径一致，差异为零或有经确认的调整单。

### 任务 10：测试、部署和文档

- 完成 Alembic 升级/降级测试、Docker 构建、备份恢复和生产升级演练。
- 更新 OpenAPI、用户手册、运维手册、权限说明和数据迁移说明。
- 先在一个库房试运行，再切换全部库房。

验收：后端、前端、迁移、权限、安全及移动真机测试全部通过，并有可恢复的上线前备份。

## 10. 测试范围

### 10.1 后端

- 角色权限和库房范围隔离。
- 物资编码格式、并发生成、归档及旧编码映射。
- 入库、出库、调拨、盘点、冲销和余额重建。
- 同库房跨项目、跨库房同项目、库房项目同时变化。
- 库存不足、重复请求、双击提交和并发竞争。
- 已过账单据禁止修改/删除。
- 调拨不产生审批状态，提交后即时反映余额。
- 审计日志包含用户、IP、设备、前后值和业务单号。
- Excel 预检、部分失败回滚和余额对账。

### 10.2 前端

- 两个新角色登录后的菜单和首页正确。
- 未授权库房不出现在选择器中。
- 手机端入库、出库、调拨、盘点主流程。
- 数量键盘、库存提示、错误提示和重复提交保护。
- 扫码成功、拒绝摄像头权限、不支持扫码和手工搜索回退。
- PC 管理端主数据、库存筛选、流水详情和冲销确认。

### 10.3 端到端验收样例

1. A 项目在一号库入库 `ZC-J-001` 20 圈。
2. A 项目从一号库领用 4 圈，余额 16。
3. 从一号库 A 项目调拨 6 圈到二号库 B 项目。
4. 一号库 A 项目余额 10，二号库 B 项目余额 6，公司总库存仍为 16。
5. 两名库管并发尝试从余额 6 的维度各出库 4，仅一笔成功。
6. 冲销调拨后，原调出/调入余额恢复，原单据和冲销单均可追溯。

## 11. 明确不在首期范围

- 原生 Android/iOS 应用。
- 离线库存过账和断网自动同步。
- 调拨审批工作流和多级审批。
- 单件序列号、设备生命周期和借用归还管理。
- 电缆盘号、批次、保质期和先进先出成本核算。
- 蓝牙标签打印机的厂商专用 SDK。
- Excel 与数据库双向实时同步。

这些能力应在核心库存账稳定运行后单独立项。

## 12. 风险与控制

| 风险 | 控制措施 |
| --- | --- |
| 多人同时出库造成负库存 | 数据库事务、余额行锁、数据库非负约束 |
| 手机网络重试造成重复单据 | `Idempotency-Key` 和提交按钮锁定 |
| 公司库管越权操作其他库房 | 后端仓库范围过滤和单资源二次校验 |
| 调拨无审批导致误操作 | 提交确认、立即审计、已过账不可编辑、管理员冲销 |
| 旧 Excel 项目/编码不规范 | 预检、编码映射、余额对账、差异不清零不切换 |
| 合同项目名称与库存项目重复 | 独立项目主数据，合同使用外键可选关联 |
| 二维码标签过期 | 二维码只保存不可变物资/货位标识 |
| 余额表与流水不一致 | 原子更新、定期核对任务、可重复余额重建 |

## 13. 计划工期

单名熟悉现有项目的全栈开发者参考量级：

| 阶段 | 内容 | 预计工作量 |
| --- | --- | --- |
| 第一阶段 | 规格、角色权限、主数据、编码、库存引擎 | 2–3 周 |
| 第二阶段 | 入库、出库、调拨、PC/手机主流程 | 2–3 周 |
| 第三阶段 | 盘点、补录、扫码、报表和 Excel 迁移 | 2–3 周 |
| 第四阶段 | 全量测试、试运行、修正和生产切换 | 1–2 周 |

完整首期约 7–11 周；若先交付不含扫码、管理补录和历史全量迁移的核心 MVP，约 4–6 周。

## 14. 完成标准

- 两个新增角色权限和库房数据范围符合矩阵。
- 支持多个库房、多个货位和多个项目库存分账。
- 物资编码由服务端按 `ZC-J-001` 规则并发安全生成。
- 入库、出库、无审批调拨、盘点和冲销形成完整不可变流水。
- 任何并发场景均不出现负库存、重复过账或调拨单边入账。
- 公司库管可以在手机上完成高频操作，库房管理员可以在 PC 端管理和追溯。
- 多库房、多项目实时库存和报表可查询、可导出。
- 当前 Excel 数据完成映射、迁移和余额对账，生产切换后 Excel 只读归档。
- Windows/Android/iOS 主流浏览器、Docker 构建、数据库迁移、备份恢复和自动化测试均通过。

## 15. 推荐实施顺序

1. 先冻结角色、主数据和库存维度，不先做页面。
2. 实现 Alembic 模型、权限和库房范围，再实现编码服务。
3. 完成库存事务引擎、幂等、冲销和并发测试。
4. 在同一库存引擎上实现入库、出库和无审批调拨 API。
5. 完成 PC 管理端和手机高频操作端。
6. 增加盘点、管理补录、扫码和报表。
7. 最后执行 Excel 迁移预演、单库试运行、全量切换和归档。
