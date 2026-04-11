# 2026-04-11 安全审计报告

## 范围

- 后端：`backend/app`
- 前端：`frontend/src`、`frontend/public`
- 部署与代理：`docker-compose*.yml`、`nginx/*`
- 配套栈：`supabase/*`

本报告基于静态代码审计与配置检查形成，未完成动态渗透验证。

## 结论摘要

本项目当前存在多项高风险安全问题，集中在认证令牌边界、文件访问授权、Webhook 鉴权、批量导入权限控制以及生产部署暴露面。最高风险问题允许攻击者在获得 refresh token 或文件路径后，直接扩大访问范围并持续访问敏感业务数据。

## 发现列表

### P0: Refresh Token 可直接充当 Access Token 使用

- 风险等级：`P0`
- 位置：
  - `backend/app/services/auth.py:99`
  - `backend/app/services/auth.py:120`
  - `backend/app/services/auth.py:278`
  - `backend/app/services/auth.py:340`
- 问题描述：
  - 系统在签发 JWT 时区分了 `type=access` 和 `type=refresh`。
  - 但 `get_current_user()` 与 `get_user_from_token()` 解码后未校验 `payload["type"] == "access"`。
  - 结果是 refresh token 可直接访问受保护接口。
- 影响：
  - refresh token 本应仅用于换发 access token，当前却可直接调用 API。
  - 攻击者一旦拿到 refresh token，可绕过 access token 的短时效限制，直接获得最长 7 天的 API 使用能力。
- 修复建议：
  - 在所有访问鉴权入口强制校验 `type == "access"`。
  - 对不符合类型的 token 返回 401。
  - 补充回归测试，覆盖 refresh token 访问业务接口应失败的场景。

### P0: 文件下载接口只校验登录，不校验对象级授权

- 风险等级：`P0`
- 位置：
  - `backend/app/routers/common.py:181`
  - `backend/app/routers/common.py:223`
- 问题描述：
  - `/api/v1/common/files/{path}` 在取文件前只验证请求者是已登录用户。
  - 代码没有检查文件是否归属于当前用户、当前合同，或当前用户是否具有对应业务对象的访问权限。
  - 只要知道或猜到存储路径，任意登录用户即可请求他人的合同、结算、回单、附件。
- 影响：
  - 构成典型 IDOR/BOLA。
  - 敏感合同附件、银行回单、审批文件、结算资料可能被横向读取。
- 修复建议：
  - 文件访问必须绑定业务对象授权。
  - 通过数据库记录反查文件所属资源，再按资源权限校验。
  - 不允许“只凭路径”直接读对象存储或本地文件。

### P0: 生产 Nginx 直接公开上传目录

- 风险等级：`P0`
- 位置：
  - `nginx/nginx.conf:148`
  - `docker-compose.production.yml:118`
- 问题描述：
  - 生产前端容器把 `uploads_data` 挂载到 `/usr/share/nginx/html/uploads`。
  - Nginx 对 `/uploads/` 使用 `alias` 直接公开访问。
  - 该路径完全绕过后端鉴权与对象级授权逻辑。
- 影响：
  - 任意外部访问者都可能直接读取上传文件。
  - 文件名或路径一旦泄露，后端任何权限控制都会失效。
- 修复建议：
  - 生产环境移除静态公开挂载。
  - 统一通过后端受控下载接口访问文件。
  - 若必须直链，需改为短时签名 URL，且由后端按授权签发。

### P1: 飞书 Webhook 事件回调缺少有效鉴权

- 风险等级：`P1`
- 位置：
  - `backend/app/routers/feishu.py:90`
- 问题描述：
  - Webhook 仅在 `url_verification` 分支检查 `token`。
  - 真正的事件回调处理分支未校验签名、令牌或来源。
  - 外部可伪造 `approval.instance.status_changed` 事件。
- 影响：
  - 可伪造审批通过事件，触发审批状态更新和后台任务。
  - 审批流程完整性被破坏。
- 修复建议：
  - 对所有事件回调执行平台要求的签名校验。
  - 未通过校验的请求直接拒绝。
  - 审批状态变更前应复查实例真实性。

### P1: 上游合同 Excel 导入接口权限失控

- 风险等级：`P1`
- 位置：
  - `backend/app/routers/contracts_upstream.py:712`
  - 对比正常创建：`backend/app/routers/contracts_upstream.py:186`
- 问题描述：
  - 批量导入接口只要求 `get_current_active_user`。
  - 正常新建合同接口要求 `CREATE_UPSTREAM_CONTRACTS`。
  - 这意味着任何已登录用户都可能通过导入批量创建合同。
- 影响：
  - 低权限账号可越权写入核心业务数据。
  - 容易造成数据污染和审计困难。
- 修复建议：
  - 将导入接口权限提升为 `CREATE_UPSTREAM_CONTRACTS`。
  - 补充导入权限测试。

### P1: 改密后未撤销既有 Refresh Token

- 风险等级：`P1`
- 位置：
  - `backend/app/routers/auth.py:173`
  - 可用撤销方法：`backend/app/services/auth.py:240`
- 问题描述：
  - `change_password()` 修改密码后直接提交。
  - 已实现的 `revoke_all_user_tokens()` 未被调用。
- 影响：
  - 已泄露 refresh token 在用户改密后仍然有效。
  - 与 refresh token 可直接访问 API 的问题叠加后，风险显著扩大。
- 修复建议：
  - 改密成功后立即撤销该用户全部 refresh token。
  - 重新登录后再发放新令牌。

### P2: 仪表盘趋势接口绕过 `VIEW_DASHBOARD` 权限

- 风险等级：`P2`
- 位置：
  - `backend/app/routers/dashboard.py:340`
- 问题描述：
  - `/api/v1/dashboard/stats/trend/period` 只要求登录。
  - 同模块其他看板接口要求 `VIEW_DASHBOARD`。
- 影响：
  - 无首页/经营看板权限的用户仍可读取收入、支出趋势数据。
- 修复建议：
  - 与同类接口对齐，要求 `VIEW_DASHBOARD`。

### P2: 前端将 Access Token 与 Refresh Token 存入 localStorage

- 风险等级：`P2`
- 位置：
  - `frontend/src/utils/authSession.js:5`
  - `frontend/public/diagnose.html:31`
- 问题描述：
  - 前端会把 `token`、`refresh_token`、用户信息与权限全部放入 `localStorage`。
  - 仓库内还保留了公开诊断页，会主动读取这些值并输出到页面。
- 影响：
  - 任意 XSS 都可直接窃取长期有效会话材料。
  - 攻击者可离线复用 refresh token。
- 修复建议：
  - 优先改为 `HttpOnly`、`Secure` Cookie 存储 refresh token。
  - access token 至少改为内存态短存活。
  - 生产禁用或删除诊断页。

### P2: 默认弱凭据和开发回退值仍广泛存在

- 风险等级：`P2`
- 位置：
  - `backend/app/config.py:27`
  - `backend/app/config.py:90`
  - `docker-compose.yml:10`
  - `docker-compose.yml:45`
  - `docker-compose.supabase.yml:18`
  - `supabase/roles.sql:11`
- 问题描述：
  - 数据库、MinIO、Supabase 相关配置仍保留默认弱口令和回退值。
  - `supabase/roles.sql` 甚至为多个高权限角色硬编码 `dev_password_change_me`。
  - 开发 compose 还直接暴露数据库、Redis、MinIO 端口。
- 影响：
  - 容易因误部署、脚本继承、示例配置复制导致真实环境弱口令运行。
  - 一旦服务暴露到不可信网络，极易被直接接管。
- 修复建议：
  - 禁止在代码中保留真实可用默认口令。
  - 生产启动时对弱值显式失败退出。
  - 对 Supabase 初始化 SQL 改为模板注入或部署期生成。

### P2: 零星用工可能绕过“仅本人数据”限制

- 风险等级：`P2`
- 位置：
  - `backend/app/core/permissions.py:165`
  - `backend/app/services/expense_service.py:20`
  - `backend/app/services/zero_hour_labor_service.py:25`
  - `backend/app/routers/zero_hour_labor.py:109`
- 问题描述：
  - 权限定义说明部分角色的费用类数据应仅查看本人数据。
  - `ExpenseService` 实现了 owner 过滤。
  - `ZeroHourLaborService` 未实现对应数据隔离，但接口复用了 `VIEW_EXPENSES`。
- 影响：
  - 若零星用工属于费用数据范畴，则审计部、投标部等可能看到他人数据。
- 修复建议：
  - 明确零星用工是否适用“仅本人数据”规则。
  - 若适用，补充与 `ExpenseService` 一致的 owner filter 与测试。

### P3: 生产对外公开 API 文档

- 风险等级：`P3`
- 位置：
  - `backend/app/main.py:68`
  - `nginx/nginx.conf:170`
- 问题描述：
  - 后端固定启用 `/docs` 和 `/openapi.json`。
  - Nginx 也直接代理 `/docs` 与 `/redoc`。
- 影响：
  - 攻击者可直接获知全部 API 面、参数结构和认证方式。
- 修复建议：
  - 生产环境默认关闭文档。
  - 或仅内网/IP 白名单开放。

## 建议修复优先级

### 第一优先级

1. 修复 refresh token 被当 access token 使用的问题。
2. 关闭所有上传目录直出，补齐文件对象级授权。
3. 给飞书 webhook 增加严格鉴权。
4. 修复导入接口权限绕过。
5. 改密后撤销全部 refresh token。

### 第二优先级

1. 收紧 dashboard 趋势接口权限。
2. 调整前端会话存储策略，移除诊断页。
3. 清理默认弱凭据与开发回退值。
4. 确认并修复零星用工的数据隔离边界。

## 验证说明

本次未完成后端自动化测试验证，原因如下：

- 当前环境不存在仓库建议使用的 `./.venv39/bin/pytest`
- 系统 `pytest` 可执行，但运行时在 `backend/tests/conftest.py` 导入阶段缺少 `asyncpg`

因此，本报告结论基于静态代码审计和配置检查，不代表已完成动态利用验证。
