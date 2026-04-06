# Full Dashboard-01 App Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign all desktop pages, mobile pages, and the login page into one coherent `dashboard-01` inspired product while preserving current routes and business behavior.

**Architecture:** Extend the existing upstream workspace redesign into reusable page-level primitives, then migrate page families in batches: shared headers and shells first, list pages second, detail pages third, utility pages fourth, mobile pages fifth, and auth last. Keep business logic intact and use targeted structural tests plus focused frontend verification after each batch.

**Tech Stack:** Vue 3, Vite, Element Plus, Vant, SCSS, Vitest

---

### File Map

**Shared shell and primitives**

- Modify: `frontend/src/views/Layout.vue`
- Modify: `frontend/src/styles/tokens.scss`
- Modify: `frontend/src/components/ui/AppSectionCard.vue`
- Modify: `frontend/src/components/ui/AppFilterBar.vue`
- Modify: `frontend/src/components/ui/AppDataTable.vue`
- Modify: `frontend/src/components/ui/AppRangeField.vue`
- Create: `frontend/src/components/ui/AppPageHeader.vue`
- Create: `frontend/src/components/ui/AppWorkspacePanel.vue`
- Test: `frontend/src/components/ui/__tests__/AppFilterBar.spec.js`
- Test: `frontend/src/components/ui/__tests__/AppPageHeader.spec.js`

**Desktop list pages**

- Modify: `frontend/src/views/contracts/UpstreamList.vue`
- Modify: `frontend/src/views/contracts/ManagementList.vue`
- Modify: `frontend/src/views/contracts/DownstreamList.vue`
- Modify: `frontend/src/views/expenses/ExpenseList.vue`
- Modify: `frontend/src/views/expenses/OrdinaryExpenseList.vue`
- Modify: `frontend/src/views/expenses/ZeroHourLaborList.vue`
- Test: `frontend/src/views/contracts/__tests__/UpstreamList.spec.js`
- Test: `frontend/src/views/contracts/__tests__/ManagementList.spec.js`
- Test: `frontend/src/views/expenses/__tests__/OrdinaryExpenseList.spec.js`

**Desktop detail pages**

- Modify: `frontend/src/views/contracts/UpstreamDetail.vue`
- Modify: `frontend/src/views/contracts/ManagementDetail.vue`
- Modify: `frontend/src/views/contracts/DownstreamDetail.vue`
- Create: `frontend/src/views/contracts/__tests__/ContractDetailWorkspace.spec.js`

**Utility pages**

- Modify: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/views/home/Overview.vue`
- Modify: `frontend/src/views/home/Business.vue`
- Modify: `frontend/src/views/reports/ReportDashboard.vue`
- Modify: `frontend/src/views/notifications/NotificationCenter.vue`
- Modify: `frontend/src/views/system/SystemManagement.vue`
- Modify: `frontend/src/views/audit/AuditLog.vue`
- Create: `frontend/src/views/__tests__/DashboardWorkspace.spec.js`
- Create: `frontend/src/views/reports/__tests__/ReportDashboardWorkspace.spec.js`

**Mobile pages**

- Modify: `frontend/src/views/mobile/MobileLayout.vue`
- Modify: `frontend/src/views/mobile/ContractListMobile.vue`
- Modify: `frontend/src/views/mobile/ExpenseListMobile.vue`
- Create: `frontend/src/views/mobile/__tests__/MobileWorkspace.spec.js`

**Auth**

- Modify: `frontend/src/views/Login.vue`
- Create: `frontend/src/views/__tests__/LoginWorkspace.spec.js`

### Task 1: Freeze new shared workspace structure with failing tests

**Files:**
- Create: `frontend/src/components/ui/__tests__/AppPageHeader.spec.js`
- Modify: `frontend/src/views/contracts/__tests__/UpstreamList.spec.js`
- Create: `frontend/src/views/contracts/__tests__/ContractDetailWorkspace.spec.js`
- Create: `frontend/src/views/__tests__/DashboardWorkspace.spec.js`
- Create: `frontend/src/views/mobile/__tests__/MobileWorkspace.spec.js`
- Create: `frontend/src/views/__tests__/LoginWorkspace.spec.js`

- [ ] **Step 1: Write the failing page-header test**

```js
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'

describe('AppPageHeader', () => {
  it('renders eyebrow, title, description, and actions in dashboard workspace order', () => {
    const wrapper = mount(AppPageHeader, {
      props: {
        eyebrow: 'Contracts',
        title: '上游合同',
        description: '浏览、筛选、导出和维护上游合同数据。'
      },
      slots: {
        actions: '<button>新建</button>'
      }
    })

    expect(wrapper.find('.app-page-header').exists()).toBe(true)
    expect(wrapper.find('.app-page-header__eyebrow').text()).toBe('Contracts')
    expect(wrapper.find('.app-page-header__title').text()).toBe('上游合同')
    expect(wrapper.find('.app-page-header__actions').text()).toContain('新建')
  })
})
```

- [ ] **Step 2: Write failing structure assertions for list, detail, utility, mobile, and login pages**

```js
expect(wrapper.find('.upstream-page-shell').exists()).toBe(true)
expect(wrapper.find('.detail-workspace').exists()).toBe(true)
expect(wrapper.find('.dashboard-shell').exists()).toBe(true)
expect(wrapper.find('.mobile-shell').exists()).toBe(true)
expect(wrapper.find('.login-shell').exists()).toBe(true)
```

- [ ] **Step 3: Run the new shared structure tests and verify they fail before implementation**

Run: `npm test -- src/components/ui/__tests__/AppPageHeader.spec.js src/views/contracts/__tests__/UpstreamList.spec.js src/views/contracts/__tests__/ContractDetailWorkspace.spec.js src/views/__tests__/DashboardWorkspace.spec.js src/views/mobile/__tests__/MobileWorkspace.spec.js src/views/__tests__/LoginWorkspace.spec.js`

Expected: FAIL with missing `AppPageHeader.vue`, missing `.detail-workspace`, missing `.login-shell`, or other absent wrapper classes

- [ ] **Step 4: Commit the test freeze for full-app workspace structure**

```bash
git add frontend/src/components/ui/__tests__/AppPageHeader.spec.js frontend/src/views/contracts/__tests__/UpstreamList.spec.js frontend/src/views/contracts/__tests__/ContractDetailWorkspace.spec.js frontend/src/views/__tests__/DashboardWorkspace.spec.js frontend/src/views/mobile/__tests__/MobileWorkspace.spec.js frontend/src/views/__tests__/LoginWorkspace.spec.js
git commit -m "test: freeze full app workspace redesign structure"
```

### Task 2: Add shared page-header and workspace primitives

**Files:**
- Create: `frontend/src/components/ui/AppPageHeader.vue`
- Create: `frontend/src/components/ui/AppWorkspacePanel.vue`
- Modify: `frontend/src/styles/tokens.scss`
- Modify: `frontend/src/components/ui/AppSectionCard.vue`
- Modify: `frontend/src/components/ui/AppFilterBar.vue`
- Modify: `frontend/src/components/ui/AppDataTable.vue`
- Modify: `frontend/src/components/ui/AppRangeField.vue`
- Test: `frontend/src/components/ui/__tests__/AppPageHeader.spec.js`
- Test: `frontend/src/components/ui/__tests__/AppFilterBar.spec.js`

- [ ] **Step 1: Implement the new shared page header**

```vue
<template>
  <header class="app-page-header">
    <div class="app-page-header__copy">
      <p v-if="eyebrow" class="app-page-header__eyebrow">{{ eyebrow }}</p>
      <h1 class="app-page-header__title">{{ title }}</h1>
      <p v-if="description" class="app-page-header__description">{{ description }}</p>
    </div>
    <div v-if="$slots.actions || meta" class="app-page-header__side">
      <div v-if="meta" class="app-page-header__meta">{{ meta }}</div>
      <div v-if="$slots.actions" class="app-page-header__actions"><slot name="actions" /></div>
    </div>
  </header>
</template>
```

- [ ] **Step 2: Implement the shared workspace panel wrapper**

```vue
<template>
  <section class="app-workspace-panel" :class="panelClass">
    <slot />
  </section>
</template>

<script setup>
defineProps({
  panelClass: {
    type: [String, Array, Object],
    default: ''
  }
})
</script>
```

- [ ] **Step 3: Extend shared tokens and wrappers for the full-app workspace language**

```scss
:root,
:root[data-theme='light'] {
  --workspace-max-width: 1400px;
  --workspace-copy-width: 720px;
  --control-height-md: 40px;
  --panel-padding: 20px;
}

.app-workspace-panel {
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
  padding: var(--panel-padding);
}
```

- [ ] **Step 4: Run component tests and verify the new primitives pass**

Run: `npm test -- src/components/ui/__tests__/AppPageHeader.spec.js src/components/ui/__tests__/AppFilterBar.spec.js`

Expected: PASS

- [ ] **Step 5: Commit the shared primitive layer**

```bash
git add frontend/src/components/ui/AppPageHeader.vue frontend/src/components/ui/AppWorkspacePanel.vue frontend/src/styles/tokens.scss frontend/src/components/ui/AppSectionCard.vue frontend/src/components/ui/AppFilterBar.vue frontend/src/components/ui/AppDataTable.vue frontend/src/components/ui/AppRangeField.vue frontend/src/components/ui/__tests__/AppPageHeader.spec.js frontend/src/components/ui/__tests__/AppFilterBar.spec.js
git commit -m "feat: add shared dashboard workspace primitives"
```

### Task 3: Convert all desktop list pages to the workspace template

**Files:**
- Modify: `frontend/src/views/contracts/UpstreamList.vue`
- Modify: `frontend/src/views/contracts/ManagementList.vue`
- Modify: `frontend/src/views/contracts/DownstreamList.vue`
- Modify: `frontend/src/views/expenses/ExpenseList.vue`
- Modify: `frontend/src/views/expenses/OrdinaryExpenseList.vue`
- Modify: `frontend/src/views/expenses/ZeroHourLaborList.vue`
- Modify: `frontend/src/views/contracts/__tests__/ManagementList.spec.js`
- Modify: `frontend/src/views/contracts/__tests__/UpstreamList.spec.js`
- Modify: `frontend/src/views/expenses/__tests__/OrdinaryExpenseList.spec.js`

- [ ] **Step 1: Add failing structure assertions for management, downstream, and expense workspaces**

```js
expect(wrapper.find('.management-page-shell').exists()).toBe(true)
expect(wrapper.find('.downstream-page-shell').exists()).toBe(true)
expect(wrapper.find('.expense-page-shell').exists()).toBe(true)
```

- [ ] **Step 2: Run focused list-page tests and verify the new wrappers fail before implementation**

Run: `npm test -- src/views/contracts/__tests__/ManagementList.spec.js src/views/contracts/__tests__/UpstreamList.spec.js src/views/expenses/__tests__/OrdinaryExpenseList.spec.js`

Expected: FAIL with missing list-page shell classes

- [ ] **Step 3: Recompose each list page around the shared page header and panel structure**

```vue
<div class="management-page-shell">
  <AppPageHeader eyebrow="Contracts" title="管理合同" description="筛选、导出和维护管理合同数据。" />
  <section class="management-page-sections">
    <AppSectionCard class="management-filter-section">...</AppSectionCard>
    <AppSectionCard class="management-table-section">...</AppSectionCard>
  </section>
</div>
```

```vue
<div class="expense-page-shell">
  <AppPageHeader eyebrow="Expenses" title="无合同费用" description="在同一工作台中查看普通费用报销与零星用工。" />
  <section class="expense-page-tabs">
    <AppSectionCard>...</AppSectionCard>
  </section>
</div>
```

- [ ] **Step 4: Normalize list-page local styles to the new tabs, filter spacing, mobile cards, and pagination rhythm**

```scss
.management-page-shell,
.downstream-page-shell,
.expense-page-shell {
  display: grid;
  gap: 18px;
}

.management-page-sections,
.downstream-page-sections,
.expense-page-tabs {
  display: grid;
  gap: 16px;
}
```

- [ ] **Step 5: Re-run focused list tests**

Run: `npm test -- src/views/contracts/__tests__/ManagementList.spec.js src/views/contracts/__tests__/UpstreamList.spec.js src/views/expenses/__tests__/OrdinaryExpenseList.spec.js`

Expected: PASS

- [ ] **Step 6: Commit the desktop list-page migration**

```bash
git add frontend/src/views/contracts/UpstreamList.vue frontend/src/views/contracts/ManagementList.vue frontend/src/views/contracts/DownstreamList.vue frontend/src/views/expenses/ExpenseList.vue frontend/src/views/expenses/OrdinaryExpenseList.vue frontend/src/views/expenses/ZeroHourLaborList.vue frontend/src/views/contracts/__tests__/ManagementList.spec.js frontend/src/views/contracts/__tests__/UpstreamList.spec.js frontend/src/views/expenses/__tests__/OrdinaryExpenseList.spec.js
git commit -m "style: migrate desktop list pages to workspace layout"
```

### Task 4: Convert contract detail pages into a shared detail workspace

**Files:**
- Modify: `frontend/src/views/contracts/UpstreamDetail.vue`
- Modify: `frontend/src/views/contracts/ManagementDetail.vue`
- Modify: `frontend/src/views/contracts/DownstreamDetail.vue`
- Modify: `frontend/src/views/contracts/__tests__/ContractDetailWorkspace.spec.js`

- [ ] **Step 1: Add failing structure assertions for the detail workspace**

```js
expect(wrapper.find('.detail-workspace').exists()).toBe(true)
expect(wrapper.find('.detail-workspace__hero').exists()).toBe(true)
expect(wrapper.find('.detail-workspace__sections').exists()).toBe(true)
```

- [ ] **Step 2: Run the detail workspace tests and verify the wrappers fail first**

Run: `npm test -- src/views/contracts/__tests__/ContractDetailWorkspace.spec.js`

Expected: FAIL with missing detail workspace classes

- [ ] **Step 3: Wrap each contract detail page in the shared detail skeleton**

```vue
<div class="detail-workspace">
  <AppPageHeader eyebrow="Contracts" :title="pageTitle" :description="pageDescription">
    <template #actions>
      <el-button @click="router.back()">返回</el-button>
    </template>
  </AppPageHeader>

  <section class="detail-workspace__hero">...</section>
  <section class="detail-workspace__sections">...</section>
</div>
```

- [ ] **Step 4: Group detail forms and attachments into reusable visual regions**

```scss
.detail-workspace__hero {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.detail-workspace__sections {
  display: grid;
  gap: 16px;
}
```

- [ ] **Step 5: Re-run detail workspace tests**

Run: `npm test -- src/views/contracts/__tests__/ContractDetailWorkspace.spec.js`

Expected: PASS

- [ ] **Step 6: Commit the detail-page migration**

```bash
git add frontend/src/views/contracts/UpstreamDetail.vue frontend/src/views/contracts/ManagementDetail.vue frontend/src/views/contracts/DownstreamDetail.vue frontend/src/views/contracts/__tests__/ContractDetailWorkspace.spec.js
git commit -m "style: migrate contract detail pages to workspace layout"
```

### Task 5: Convert dashboard, reports, notifications, system, and audit into utility workspaces

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/views/home/Overview.vue`
- Modify: `frontend/src/views/home/Business.vue`
- Modify: `frontend/src/views/reports/ReportDashboard.vue`
- Modify: `frontend/src/views/notifications/NotificationCenter.vue`
- Modify: `frontend/src/views/system/SystemManagement.vue`
- Modify: `frontend/src/views/audit/AuditLog.vue`
- Modify: `frontend/src/views/__tests__/DashboardWorkspace.spec.js`
- Create: `frontend/src/views/reports/__tests__/ReportDashboardWorkspace.spec.js`

- [ ] **Step 1: Add failing dashboard and report workspace assertions**

```js
expect(wrapper.find('.dashboard-shell').exists()).toBe(true)
expect(wrapper.find('.dashboard-page-header').exists()).toBe(true)
expect(wrapper.find('.report-dashboard-shell').exists()).toBe(true)
```

- [ ] **Step 2: Run utility-page tests and verify the new expectations fail**

Run: `npm test -- src/views/__tests__/DashboardWorkspace.spec.js src/views/reports/__tests__/ReportDashboardWorkspace.spec.js`

Expected: FAIL with missing utility workspace wrappers

- [ ] **Step 3: Add shared utility headers and panels to dashboard and report pages**

```vue
<div class="dashboard-shell">
  <AppPageHeader class="dashboard-page-header" eyebrow="Workspace" title="首页概览" description="在统一工作台内查看概览和经营看板。" />
  <AppWorkspacePanel class="dashboard-tabs-panel">...</AppWorkspacePanel>
</div>
```

```vue
<div class="report-dashboard-shell">
  <AppPageHeader eyebrow="Reports" title="报表统计" description="查询月度成本报表与业务导出数据。" />
  <AppWorkspacePanel>...</AppWorkspacePanel>
</div>
```

- [ ] **Step 4: Refactor notifications, system, and audit into the same header-plus-panel rhythm**

```vue
<div class="system-management-shell">
  <AppPageHeader eyebrow="System" title="系统管理" description="管理用户、配置与运维操作。" />
  <AppWorkspacePanel>...</AppWorkspacePanel>
</div>
```

- [ ] **Step 5: Re-run utility-page tests**

Run: `npm test -- src/views/__tests__/DashboardWorkspace.spec.js src/views/reports/__tests__/ReportDashboardWorkspace.spec.js`

Expected: PASS

- [ ] **Step 6: Commit the utility-page migration**

```bash
git add frontend/src/views/Dashboard.vue frontend/src/views/home/Overview.vue frontend/src/views/home/Business.vue frontend/src/views/reports/ReportDashboard.vue frontend/src/views/notifications/NotificationCenter.vue frontend/src/views/system/SystemManagement.vue frontend/src/views/audit/AuditLog.vue frontend/src/views/__tests__/DashboardWorkspace.spec.js frontend/src/views/reports/__tests__/ReportDashboardWorkspace.spec.js
git commit -m "style: migrate utility pages to dashboard workspace"
```

### Task 6: Convert the mobile routes to a matching mobile workspace

**Files:**
- Modify: `frontend/src/views/mobile/MobileLayout.vue`
- Modify: `frontend/src/views/mobile/ContractListMobile.vue`
- Modify: `frontend/src/views/mobile/ExpenseListMobile.vue`
- Modify: `frontend/src/views/mobile/__tests__/MobileWorkspace.spec.js`

- [ ] **Step 1: Add failing mobile workspace assertions**

```js
expect(wrapper.find('.mobile-shell').exists()).toBe(true)
expect(wrapper.find('.mobile-shell__frame').exists()).toBe(true)
expect(wrapper.find('.mobile-contract-list__toolbar').exists()).toBe(true)
```

- [ ] **Step 2: Run the mobile workspace tests and verify they fail before implementation**

Run: `npm test -- src/views/mobile/__tests__/MobileWorkspace.spec.js`

Expected: FAIL with missing mobile workspace classes

- [ ] **Step 3: Rebuild the mobile shell around a framed header, inset content, and aligned tabbar**

```vue
<div class="mobile-shell">
  <div class="mobile-shell__frame">
    <header class="mobile-topbar">...</header>
    <main class="mobile-content"><router-view /></main>
  </div>
  <van-tabbar class="mobile-tabbar">...</van-tabbar>
</div>
```

- [ ] **Step 4: Rebuild mobile contract and expense pages into consistent card stacks and toolbars**

```vue
<div class="mobile-contract-list">
  <section class="mobile-contract-list__toolbar">...</section>
  <section class="mobile-contract-list__filters">...</section>
  <section class="mobile-contract-list__cards">...</section>
</div>
```

- [ ] **Step 5: Re-run the mobile tests**

Run: `npm test -- src/views/mobile/__tests__/MobileWorkspace.spec.js`

Expected: PASS

- [ ] **Step 6: Commit the mobile-page migration**

```bash
git add frontend/src/views/mobile/MobileLayout.vue frontend/src/views/mobile/ContractListMobile.vue frontend/src/views/mobile/ExpenseListMobile.vue frontend/src/views/mobile/__tests__/MobileWorkspace.spec.js
git commit -m "style: migrate mobile pages to workspace layout"
```

### Task 7: Convert the login page into the auth workspace

**Files:**
- Modify: `frontend/src/views/Login.vue`
- Modify: `frontend/src/views/__tests__/LoginWorkspace.spec.js`

- [ ] **Step 1: Add failing login-shell assertions**

```js
expect(wrapper.find('.login-shell').exists()).toBe(true)
expect(wrapper.find('.login-shell__panel').exists()).toBe(true)
expect(wrapper.find('.login-shell__brand').exists()).toBe(true)
```

- [ ] **Step 2: Run the login test and verify it fails first**

Run: `npm test -- src/views/__tests__/LoginWorkspace.spec.js`

Expected: FAIL with missing `.login-shell` wrappers

- [ ] **Step 3: Recompose the login page into the auth workspace**

```vue
<div class="login-shell">
  <div class="login-shell__panel">
    <section class="login-shell__brand">...</section>
    <section class="login-shell__form">...</section>
  </div>
</div>
```

- [ ] **Step 4: Align login inputs and buttons with the shared 40px control language**

```scss
.login-shell__panel {
  border: 1px solid var(--border-subtle);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.9);
}

.login-form :deep(.el-input__wrapper),
.login-form .login-button {
  min-height: 46px;
}
```

- [ ] **Step 5: Re-run the login test**

Run: `npm test -- src/views/__tests__/LoginWorkspace.spec.js`

Expected: PASS

- [ ] **Step 6: Commit the auth-page migration**

```bash
git add frontend/src/views/Login.vue frontend/src/views/__tests__/LoginWorkspace.spec.js
git commit -m "style: migrate login page to auth workspace"
```

### Task 8: Run final verification and integrate the redesign

**Files:**
- Modify: any files touched by fixes from verification

- [ ] **Step 1: Run focused frontend regression tests**

Run: `npm test -- src/components/ui/__tests__/AppFilterBar.spec.js src/components/ui/__tests__/AppPageHeader.spec.js src/views/contracts/__tests__/ManagementList.spec.js src/views/contracts/__tests__/UpstreamList.spec.js src/views/contracts/__tests__/ContractDetailWorkspace.spec.js src/views/expenses/__tests__/OrdinaryExpenseList.spec.js src/views/__tests__/DashboardWorkspace.spec.js src/views/reports/__tests__/ReportDashboardWorkspace.spec.js src/views/mobile/__tests__/MobileWorkspace.spec.js src/views/__tests__/LoginWorkspace.spec.js`

Expected: PASS

- [ ] **Step 2: Run the frontend production build**

Run: `npm run build`

Expected: PASS with a generated `dist/` bundle and exit code `0`

- [ ] **Step 3: Run contract-related backend verification**

Run: `./.venv39/bin/pytest backend/tests/test_contracts.py -q`

Expected: PASS

- [ ] **Step 4: Commit the verified full-app redesign state**

```bash
git add frontend/src/components/ui frontend/src/views frontend/src/styles/tokens.scss
git commit -m "test: verify full dashboard redesign rollout"
```
