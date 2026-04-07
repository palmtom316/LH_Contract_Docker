# 2026-04-07 项目代码审查报告

## 审查范围

- 后端：`backend/app`、`backend/tests`
- 前端：`frontend/src`、`frontend/package.json`
- 工程与交付：`README.md`、`.gitignore`、仓库中已跟踪的运行产物

本次审查目标：

- 找出明确缺陷、行为回归、安全边界问题
- 识别测试体系、仓库卫生、维护成本方面的风险
- 形成后续整改与优化输入

## 审查方法

- 静态审查关键模块：认证、合同、文件、通知、布局与共享组件
- 抽查测试与运行入口：`pytest`、`vitest`
- 校验工程状态：文档版本、运行产物、死代码与调试遗留

## 执行证据

### 前端测试

执行：

```bash
npm test --prefix frontend
```

结果：

- 28 个测试文件中 2 个失败
- 失败点集中在共享 UI 组件断言与源码不一致
- 失败测试：
  - `frontend/src/components/ui/__tests__/AppFilterBar.spec.js`
  - `frontend/src/components/ui/__tests__/AppPageHeader.spec.js`

### 后端测试

执行：

```bash
./.venv39/bin/pytest backend/tests -q
```

结果：

- 3 个失败
- 54 个错误
- 其中大量错误来自测试夹具强依赖本地 PostgreSQL：`127.0.0.1:5432`
- 同时存在真实断言失配：`backend/tests/test_errors.py`

## 主要发现

### P1

#### 1. `AppPageHeader` 在没有 `actions` 插槽时直接不渲染，导致多个页面标题消失

证据：

- `frontend/src/components/ui/AppPageHeader.vue:2`
- `frontend/src/components/ui/AppPageHeader.vue:38`
- 受影响页面示例：
  - `frontend/src/views/Dashboard.vue:3`
  - `frontend/src/views/reports/ReportDashboard.vue:3`
  - `frontend/src/views/system/SystemManagement.vue:3`
  - `frontend/src/views/expenses/ExpenseList.vue:3`
  - `frontend/src/views/system/SystemSettings.vue:4`

问题说明：

- `AppPageHeader` 整体被 `v-if="showHeader"` 包裹
- `showHeader` 仅依赖 `Boolean(slots.actions)`
- 没有 `actions` 插槽的页面即使传了 `title` 也不会显示页头

影响：

- 共享工作台多个页面发生可见回归
- 页面信息层级削弱，导航与定位成本上升
- 现有测试没有拦住该回归

建议结论：

- 这是本次审查中最明确、影响面最广的前端回归

### P2

#### 2. 通知持久化未按用户隔离，账号切换后会串读已读/删除状态与本地通知

证据：

- `frontend/src/stores/system.js:7-9`
- `frontend/src/stores/system.js:46-48`
- `frontend/src/stores/system.js:70-74`
- `frontend/src/stores/user.js:164-176`

问题说明：

- 通知相关状态使用固定 `localStorage` key：
  - `lh_notifications_read`
  - `lh_notifications_deleted`
  - `lh_notifications_local`
- 退出登录只清除会话与用户信息，不清除上述通知 key

影响：

- 同一浏览器切换账号后，后登录用户会继承前一个用户的通知已读/删除状态
- 本地产生的“删除受阻”等业务通知可能跨用户可见
- 属于数据隔离与 UX 一致性问题

#### 3. 审计日志 IP 提取逻辑无条件信任 `X-Forwarded-For`/`X-Real-IP`，与限流逻辑不一致

证据：

- 审计逻辑：`backend/app/services/audit_service.py:154-170`
- 可信代理配置：`backend/app/config.py:87-93`
- 限流逻辑的安全实现：`backend/app/core/rate_limit.py:29-47`

问题说明：

- 审计使用的 `get_client_ip()` 无条件读取转发头
- 项目其实已经有 `TRUSTED_PROXIES` 配置和更安全的限流版 `get_client_ip()`
- 当前实现造成两套 IP 解析标准并存

影响：

- 审计日志中的来源 IP 可被伪造
- 登录、登出、改密等安全事件的审计可信度下降
- 事后追踪和安全排查会受到干扰

建议结论：

- 应统一到可信代理感知的 IP 解析实现

#### 4. 后端测试体系与本地 PostgreSQL 强耦合，导致大量测试在非特定环境下不可运行

证据：

- `backend/tests/conftest.py:24-28`
- `backend/tests/conftest.py:67-88`
- `backend/tests/conftest.py:99-113`

问题说明：

- 测试默认连接 `postgresql+asyncpg://...@127.0.0.1:5432/lh_contract_test_db`
- 每个函数级测试都会尝试建库、删表、重建
- 缺少轻量替代方案或环境探测降级策略

影响：

- CI/本地环境一致性差
- 单元测试与集成测试边界混乱
- 测试失败时难以区分“代码坏了”还是“环境没配好”

补充：

- 本次执行中大量 `PermissionError` 来自沙箱无法连本地 5432，但这也暴露了测试架构对外部数据库的硬依赖

#### 5. 后端错误模型和测试断言已经脱节，说明错误契约缺少统一维护

证据：

- 当前实现：`backend/app/core/errors.py`
- 失败测试：`backend/tests/test_errors.py:81-137`

问题说明：

- `AppException.detail` 现在承载完整响应体字典
- 但测试仍按旧语义把 `detail` 当作纯字符串断言

影响：

- 错误处理的契约无人守护
- 测试红灯但没有及时修复，降低测试可信度

### P3

#### 6. 前端测试套件当前不是绿的，且失败反映出共享组件与测试规范已经分叉

证据：

- 失败测试：
  - `frontend/src/components/ui/__tests__/AppFilterBar.spec.js`
  - `frontend/src/components/ui/__tests__/AppPageHeader.spec.js`
- 相关源码：
  - `frontend/src/components/ui/AppFilterBar.vue`
  - `frontend/src/components/ui/AppWorkspacePanel.vue`
  - `frontend/src/components/ui/AppPageHeader.vue`

问题说明：

- 一部分断言还停留在旧视觉/旧结构预期
- 另一部分问题则是真实源码回归
- 测试无法稳定承担“共享组件守门人”角色

影响：

- UI 改动的回归和设计漂移都更难被区分
- 团队很容易对测试告警失去信任

#### 7. 文档版本明显滞后，项目对外认知与实际代码版本不一致

证据：

- `README.md:1-3` 仍写 `V1.1`
- `frontend/package.json:3` 已是 `1.6`
- `backend/app/config.py:18-19` 也标注 `1.6`

影响：

- 新成员和部署人员会被误导
- 发布、排障、升级说明容易引用错误版本

#### 8. 仓库已跟踪运行产物，不利于版本管理与审查

已跟踪文件：

- `backend/logs/app.log`
- `backend/logs/error.log`
- `backend/uploads/system/site_logo.jpg`
- `backend/uploads/upstream_contracts_import_template.xlsx`

问题说明：

- 根 `.gitignore` 已忽略日志和上传目录，但已跟踪文件不会自动移出版本控制

影响：

- 审查噪音增大
- 易引入无意义冲突
- 运行环境数据与源码边界不清晰

#### 9. 仓库中存在死代码、重复组件与参考备份文件

证据：

- 未发现引用的重复页头组件：`frontend/src/components/layout/AppPageHeader.vue`
- 参考备份文件：`frontend/src/views/home/Overview.vue_backup_for_ref`
- 兼容/历史路径较多，缺少集中清理策略

影响：

- 增加认知负担
- 容易让维护者误改错误文件

#### 10. 前端源码仍保留多处调试日志

证据：

- `frontend/src/utils/request.js:34`
- `frontend/src/utils/download.js:14-15`
- `frontend/src/utils/download.js:24`
- `frontend/src/utils/download.js:36`
- `frontend/src/utils/download.js:49`
- `frontend/src/components/PdfUpload.vue:169`

影响：

- 生产控制台噪音增加
- 下载、上传等高频路径暴露调试细节

## 结论

本项目当前的主要问题不在“完全不可用”，而在以下三类：

1. 共享前端组件回归已经进入主流程页面。
2. 测试与错误契约、视觉契约、运行环境之间出现了明显漂移。
3. 工程治理层面存在文档滞后、已跟踪运行产物、死代码与调试残留。

整体判断：

- 业务主干仍可读、结构大体可维护
- 但当前分支不适合在不做整理的情况下继续堆叠 UI 改造或大规模重构
- 建议先做一轮“稳定性与工程卫生修复”，再继续功能演进
