# 月度与季度成本报表 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在“报表统计”页面新增“月度成本报表、季度成本报表”，并按公司合同分类输出上游、下游及管理、零星用工、无合同费用的金额统计。

**Architecture:** 后端新增一个聚合接口，按 `created_at`（月度新增口径）统计月度与季度两套数据；前端在报表页新增筛选和分组表格，展示两张报表与合计行。分类主维度使用 `project_category` 字典并补齐数据中出现但字典未配置的分类。

**Tech Stack:** FastAPI, SQLAlchemy Async, Vue3 + Element Plus

---

### Task 1: 报表接口测试（RED）

**Files:**
- Modify: `backend/tests/test_api_integration.py`

**Step 1: Write the failing test**
- 新增 `test_cost_monthly_quarterly_report`，构造一组上游/下游/管理/零星/无合同样本数据（不同 `created_at` 月份）。
- 断言接口 `/api/v1/reports/cost/monthly-quarterly` 返回：
  - 含 `monthly`、`quarterly`、`totals`。
  - 下游/管理与零星/无合同按其关联上游的 `company_category` 归类。
  - 季度统计包含同季度其它月份新增数据。

**Step 2: Run test to verify it fails**
- Run: `pytest backend/tests/test_api_integration.py::TestReportAPIEndpoints::test_cost_monthly_quarterly_report -v`
- Expected: FAIL（接口不存在或字段不匹配）

### Task 2: 后端实现（GREEN）

**Files:**
- Modify: `backend/app/routers/reports/summary.py`

**Step 1: 新增聚合辅助方法**
- 统一实现“按上游公司分类聚合金额”能力，支持：
  - 直接基于上游表聚合
  - 基于下游/管理及其子表，通过 `upstream_contract_id -> contracts_upstream.company_category` 聚合
  - 基于零星用工、无合同费用通过关联上游聚合

**Step 2: 新增接口 `/cost/monthly-quarterly`**
- 入参：`year`, `month`, `skip_cache`
- 输出：`monthly`, `quarterly`, `totals`, `period`
- 统计字段：
  - 上游：签约金额、应收款、挂账、收款、结算
  - 下游及管理：签约金额、应付款、挂账、付款、结算
  - 零星用工
  - 无合同费用
- 口径：全部按记录 `created_at` 的年月（季度为自然季度）

**Step 3: Run test to verify it passes**
- Run: `pytest backend/tests/test_api_integration.py::TestReportAPIEndpoints::test_cost_monthly_quarterly_report -v`
- Expected: PASS

### Task 3: 前端 API + 页面展示

**Files:**
- Modify: `frontend/src/api/reports.js`
- Modify: `frontend/src/views/reports/ReportDashboard.vue`

**Step 1: API 封装**
- 新增 `getCostMonthlyQuarterlyReport(year, month)`。

**Step 2: 页面新增成本报表区域**
- 在导出卡片前新增“月度/季度成本报表”模块：
  - 年/月选择 + 查询按钮
  - 月度表与季度表（可用 tabs）
  - 多级表头对齐截图字段
  - 合计行高亮显示

**Step 3: 交互与容错**
- 请求加载态、错误提示、金额格式化。

### Task 4: 验证与回归

**Files:**
- N/A

**Step 1: 后端测试**
- Run: `pytest backend/tests/test_api_integration.py::TestReportAPIEndpoints::test_cost_monthly_quarterly_report -v`
- Expected: PASS

**Step 2: 关键静态检查（若可执行）**
- Run: `npm run -C frontend lint`
- Expected: 无新引入错误

