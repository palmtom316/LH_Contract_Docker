# Frontend Visual Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the full frontend, including desktop, mobile, and chart rendering, into one shadcn/ui-inspired visual system with better readability, better chart typography, zero chart label collisions, and stronger light/dark consistency.

**Architecture:** The implementation follows a layered sequence. First normalize the token system and global Element Plus overrides, then migrate shared display primitives, then unify shell chrome, then rebuild the chart option contract, and finally migrate desktop and mobile business pages onto the new primitives. This keeps behavior stable while letting presentation converge across the whole app.

**Tech Stack:** Vue 3, Element Plus, Vant, Pinia, ECharts, SCSS tokens, Tailwind utility classes, Vitest

---

## Planned File Changes

- Modify: `frontend/src/styles/tokens.scss`
- Modify: `frontend/src/styles/index.scss`
- Modify: `frontend/src/components/ui/AppMetricCard.vue`
- Modify: `frontend/src/components/ui/AppSectionCard.vue`
- Modify: `frontend/src/components/ui/AppWorkspacePanel.vue`
- Modify: `frontend/src/components/ui/AppFilterBar.vue`
- Modify: `frontend/src/components/ui/AppDataTable.vue`
- Add: `frontend/src/components/ui/AppChartPanel.vue`
- Modify: `frontend/src/views/Layout.vue`
- Modify: `frontend/src/views/mobile/MobileLayout.vue`
- Modify: `frontend/src/utils/chartTheme.js`
- Modify: `frontend/src/utils/chartOptions.js`
- Modify: `frontend/src/utils/dashboardRanking.js`
- Modify: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/views/home/Overview.vue`
- Modify: `frontend/src/views/home/Business.vue`
- Modify: `frontend/src/views/reports/ReportDashboard.vue`
- Modify: `frontend/src/views/contracts/UpstreamList.vue`
- Modify: `frontend/src/views/contracts/DownstreamList.vue`
- Modify: `frontend/src/views/contracts/ManagementList.vue`
- Modify: `frontend/src/views/contracts/UpstreamDetail.vue`
- Modify: `frontend/src/views/contracts/DownstreamDetail.vue`
- Modify: `frontend/src/views/contracts/ManagementDetail.vue`
- Modify: `frontend/src/views/expenses/ExpenseList.vue`
- Modify: `frontend/src/views/expenses/OrdinaryExpenseList.vue`
- Modify: `frontend/src/views/expenses/ZeroHourLaborList.vue`
- Modify: `frontend/src/views/system/SystemManagement.vue`
- Modify: `frontend/src/views/system/SystemSettings.vue`
- Modify: `frontend/src/views/users/UserManagement.vue`
- Modify: `frontend/src/views/audit/AuditLog.vue`
- Modify: `frontend/src/views/notifications/NotificationCenter.vue`
- Modify: `frontend/src/views/Login.vue`
- Modify: `frontend/src/views/mobile/ContractListMobile.vue`
- Modify: `frontend/src/views/mobile/ExpenseListMobile.vue`
- Add: `frontend/src/components/ui/__tests__/AppMetricCard.spec.js`
- Add: `frontend/src/components/ui/__tests__/AppSectionCard.spec.js`
- Add: `frontend/src/components/ui/__tests__/AppChartPanel.spec.js`
- Modify: `frontend/src/utils/__tests__/chartOptions.spec.js`
- Modify: `frontend/src/utils/__tests__/dashboardRanking.spec.js`
- Add: `frontend/src/views/__tests__/LayoutWorkspaceVisual.spec.js`
- Add: `frontend/src/views/reports/__tests__/ReportDashboardVisual.spec.js`
- Add: `frontend/src/views/mobile/__tests__/MobileVisualShell.spec.js`

### Task 1: Normalize the Token System and Global Component Contract

**Files:**
- Modify: `frontend/src/styles/tokens.scss`
- Modify: `frontend/src/styles/index.scss`
- Test: `frontend/src/styles/__tests__/colorSystem.spec.js`

- [ ] **Step 1: Add a failing token regression test for the new radius and surface contract**

```js
import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const tokens = readFileSync(path.resolve(process.cwd(), 'src/styles/tokens.scss'), 'utf-8')
const globals = readFileSync(path.resolve(process.cwd(), 'src/styles/index.scss'), 'utf-8')

describe('visual token contract', () => {
  it('keeps one compact radius ladder and removes oversized hard-coded panel radii', () => {
    expect(tokens).toContain('--radius: 0.75rem;')
    expect(tokens).toContain('--radius-lg: 1rem;')
    expect(tokens).not.toContain('22px')
    expect(tokens).not.toContain('24px')
  })

  it('binds Element Plus controls to token-driven radius and surface values', () => {
    expect(globals).toContain('border-radius: var(--radius)')
    expect(globals).toContain('--el-box-shadow: var(--shadow-card)')
  })
})
```

- [ ] **Step 2: Run the style test to verify it fails against current tokens**

Run: `npm --prefix frontend test -- colorSystem`
Expected: FAIL because the current token file still contains gradient-heavy panel surfaces and multiple oversized radii.

- [ ] **Step 3: Simplify tokens and global Element Plus overrides**

```scss
:root,
:root[data-theme='light'] {
  --background: 210 20% 98%;
  --foreground: 222 47% 11%;
  --card: 0 0% 100%;
  --muted: 210 16% 95%;
  --muted-foreground: 215 16% 43%;
  --border: 214 20% 88%;
  --ring: 215 20% 65%;
  --radius: 0.75rem;
  --radius-sm: 0.5rem;
  --radius-md: 0.75rem;
  --radius-lg: 1rem;
  --surface-page: hsl(var(--background));
  --surface-page-gradient: linear-gradient(180deg, hsl(var(--background)), hsl(var(--background)));
  --surface-panel: hsl(var(--card));
  --surface-panel-elevated: hsl(var(--card));
  --surface-sidebar: hsl(var(--card));
  --shadow-card: 0 1px 2px hsl(222 47% 11% / 0.06);
  --shadow-soft: 0 1px 2px hsl(222 47% 11% / 0.04);
  --shadow-frame: 0 10px 24px hsl(222 47% 11% / 0.08);
}

:root {
  --el-box-shadow: var(--shadow-card);
  --el-box-shadow-light: var(--shadow-soft);
}

.el-button,
.el-input__wrapper,
.el-select__wrapper,
.el-textarea__inner,
.el-card {
  border-radius: var(--radius);
}
```

- [ ] **Step 4: Re-run the style contract test**

Run: `npm --prefix frontend test -- colorSystem`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/styles/tokens.scss frontend/src/styles/index.scss frontend/src/styles/__tests__/colorSystem.spec.js
git commit -m "refactor: normalize frontend token contract"
```

### Task 2: Refactor Shared Display Primitives Into One Visual Family

**Files:**
- Modify: `frontend/src/components/ui/AppMetricCard.vue`
- Modify: `frontend/src/components/ui/AppSectionCard.vue`
- Modify: `frontend/src/components/ui/AppWorkspacePanel.vue`
- Modify: `frontend/src/components/ui/AppFilterBar.vue`
- Modify: `frontend/src/components/ui/AppDataTable.vue`
- Add: `frontend/src/components/ui/AppChartPanel.vue`
- Add: `frontend/src/components/ui/__tests__/AppMetricCard.spec.js`
- Add: `frontend/src/components/ui/__tests__/AppSectionCard.spec.js`
- Add: `frontend/src/components/ui/__tests__/AppChartPanel.spec.js`

- [ ] **Step 1: Add failing primitive tests for card and chart panel structure**

```js
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AppMetricCard from '@/components/ui/AppMetricCard.vue'
import AppSectionCard from '@/components/ui/AppSectionCard.vue'

describe('shared surface primitives', () => {
  it('renders metric cards as quiet bordered surfaces without decorative highlight rails', () => {
    const wrapper = mount(AppMetricCard, {
      props: { eyebrow: '指标', title: '年度回款', value: '¥ 120 万' }
    })

    expect(wrapper.classes()).toContain('app-metric-card')
    expect(wrapper.find('.app-metric-card__rail').exists()).toBe(false)
    expect(wrapper.find('.app-metric-card__value').text()).toContain('120')
  })

  it('renders section cards with header/action slots inside one shared surface shell', () => {
    const wrapper = mount(AppSectionCard, {
      slots: {
        header: '<span>合同列表</span>',
        actions: '<button>导出</button>',
        default: '<div class="body">content</div>'
      }
    })

    expect(wrapper.find('.app-section-card').exists()).toBe(true)
    expect(wrapper.find('.app-section-card__header').exists()).toBe(true)
    expect(wrapper.find('.body').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: Run primitive tests to verify failure**

Run: `npm --prefix frontend test -- AppMetricCard AppSectionCard`
Expected: FAIL because the current components still rely on oversized radii, pseudo-element highlights, and inconsistent shell structure.

- [ ] **Step 3: Rewrite the shared primitive shells**

```vue
<template>
  <article class="app-metric-card rounded-xl border border-border bg-card shadow-sm">
    <div class="app-metric-card__head">
      <span class="app-metric-card__eyebrow">{{ eyebrow }}</span>
      <slot name="badge" />
    </div>
    <div class="app-metric-card__title">{{ title }}</div>
    <div class="app-metric-card__value">{{ value }}</div>
    <p v-if="description" class="app-metric-card__description">{{ description }}</p>
    <div v-if="$slots.footer" class="app-metric-card__footer"><slot name="footer" /></div>
  </article>
</template>

<style scoped lang="scss">
.app-metric-card {
  display: grid;
  gap: 0.75rem;
  min-width: 0;
  min-height: 100%;
  padding: 1rem;
  transition: border-color 160ms ease, box-shadow 160ms ease;
}
</style>
```

```vue
<template>
  <section class="app-chart-panel rounded-xl border border-border bg-card shadow-sm">
    <header v-if="$slots.header || $slots.actions" class="app-chart-panel__header">
      <div class="app-chart-panel__title"><slot name="header" /></div>
      <div v-if="$slots.actions" class="app-chart-panel__actions"><slot name="actions" /></div>
    </header>
    <div class="app-chart-panel__body"><slot /></div>
  </section>
</template>
```

- [ ] **Step 4: Re-run the primitive tests**

Run: `npm --prefix frontend test -- AppMetricCard AppSectionCard AppChartPanel`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/AppMetricCard.vue frontend/src/components/ui/AppSectionCard.vue frontend/src/components/ui/AppWorkspacePanel.vue frontend/src/components/ui/AppFilterBar.vue frontend/src/components/ui/AppDataTable.vue frontend/src/components/ui/AppChartPanel.vue frontend/src/components/ui/__tests__/AppMetricCard.spec.js frontend/src/components/ui/__tests__/AppSectionCard.spec.js frontend/src/components/ui/__tests__/AppChartPanel.spec.js
git commit -m "refactor: unify shared frontend surfaces"
```

### Task 3: Unify Desktop and Mobile Shell Chrome

**Files:**
- Modify: `frontend/src/views/Layout.vue`
- Modify: `frontend/src/views/mobile/MobileLayout.vue`
- Add: `frontend/src/views/__tests__/LayoutWorkspaceVisual.spec.js`
- Add: `frontend/src/views/mobile/__tests__/MobileVisualShell.spec.js`
- Existing Test: `frontend/src/views/mobile/__tests__/MobileWorkspace.spec.js`

- [ ] **Step 1: Add failing shell tests for simplified chrome**

```js
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const desktopShell = readFileSync(path.resolve(process.cwd(), 'src/views/Layout.vue'), 'utf-8')
const mobileShell = readFileSync(path.resolve(process.cwd(), 'src/views/mobile/MobileLayout.vue'), 'utf-8')

describe('workspace shell visual contract', () => {
  it('removes legacy glossy transform-based hover chrome from the desktop shell', () => {
    expect(desktopShell).not.toContain('translateX(-18%)')
    expect(desktopShell).not.toContain('radial-gradient')
  })

  it('aligns mobile shell radii to shared token values', () => {
    expect(mobileShell).not.toContain('border-radius: 24px')
    expect(mobileShell).toContain('var(--radius-lg)')
  })
})
```

- [ ] **Step 2: Run the shell tests and verify they fail**

Run: `npm --prefix frontend test -- LayoutWorkspaceVisual MobileVisualShell MobileWorkspace`
Expected: FAIL because current shell files still use heavier gradients, hard-coded mobile radii, and older chrome effects.

- [ ] **Step 3: Simplify shell styling in desktop and mobile layout**

```scss
.sidebar {
  background: hsl(var(--card));
  border-right: 1px solid hsl(var(--border));
}

.sidebar-nav-item {
  border-radius: var(--radius);
  background: transparent;
}

.sidebar-nav-item:hover {
  background: hsl(var(--muted));
}

.sidebar-nav-item.is-active {
  background: hsl(var(--accent));
  color: hsl(var(--foreground));
}
```

```scss
.mobile-shell__frame {
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  background: hsl(var(--card));
  box-shadow: var(--shadow-card);
}

.mobile-topbar {
  background: hsl(var(--card));
  border-bottom: 1px solid hsl(var(--border));
}
```

- [ ] **Step 4: Re-run the shell tests**

Run: `npm --prefix frontend test -- LayoutWorkspaceVisual MobileVisualShell MobileWorkspace`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/Layout.vue frontend/src/views/mobile/MobileLayout.vue frontend/src/views/__tests__/LayoutWorkspaceVisual.spec.js frontend/src/views/mobile/__tests__/MobileVisualShell.spec.js frontend/src/views/mobile/__tests__/MobileWorkspace.spec.js
git commit -m "refactor: align desktop and mobile workspace shells"
```

### Task 4: Rebuild the Chart Theme and Option Factories

**Files:**
- Modify: `frontend/src/utils/chartTheme.js`
- Modify: `frontend/src/utils/chartOptions.js`
- Modify: `frontend/src/utils/dashboardRanking.js`
- Modify: `frontend/src/utils/__tests__/chartOptions.spec.js`
- Modify: `frontend/src/utils/__tests__/dashboardRanking.spec.js`

- [ ] **Step 1: Add failing chart tests for no-overlap defaults**

```js
describe('createPieChartOption', () => {
  it('uses center emphasis and legend-led reading instead of risky outside labels', () => {
    const option = createPieChartOption({
      title: '费用结构',
      data: [
        { name: '管理费', value: 30 },
        { name: '人工费', value: 20 },
        { name: '材料费', value: 10 }
      ]
    })

    expect(option.series[0].label.show).toBe(false)
    expect(option.series[0].labelLine.show).toBe(false)
    expect(option.legend.type).toBe('scroll')
  })
})

describe('createHorizontalRankOption', () => {
  it('reserves wider label space for long Chinese category names', () => {
    const option = createHorizontalRankOption({
      items: [{ name: '市政道路综合整治专项工程', value: 100000 }]
    })

    expect(option.grid.left).toBe('24%')
    expect(option.yAxis.axisLabel.width).toBeGreaterThanOrEqual(112)
  })
})
```

- [ ] **Step 2: Run chart tests to verify they fail**

Run: `npm --prefix frontend test -- chartOptions dashboardRanking`
Expected: FAIL because current pie charts still render outside labels and current rank charts reserve too little space for longer labels.

- [ ] **Step 3: Replace chart defaults with a readability-first contract**

```js
export function createPieChartOption({ title = '', data = [] }) {
  const theme = readChartTheme()

  return {
    aria: { enabled: true },
    tooltip: {
      trigger: 'item',
      confine: true,
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: { color: theme.textStrong, fontSize: 12 }
    },
    legend: {
      bottom: 0,
      type: 'scroll',
      textStyle: { color: theme.text, fontSize: 12 }
    },
    series: [{
      type: 'pie',
      radius: ['56%', '74%'],
      center: ['50%', '42%'],
      avoidLabelOverlap: true,
      label: { show: false },
      labelLine: { show: false },
      emphasis: {
        scale: true,
        label: {
          show: true,
          position: 'center',
          formatter: '{b}\n{d}%',
          color: theme.textStrong,
          fontSize: 14,
          fontWeight: 600
        }
      },
      data
    }]
  }
}
```

```js
export function createHorizontalRankOption({ items, color = '#2563eb' }) {
  return {
    grid: { left: '24%', right: '4%', top: '8%', bottom: '12%', containLabel: true },
    yAxis: {
      type: 'category',
      axisLabel: {
        width: 120,
        overflow: 'truncate'
      }
    }
  }
}
```

- [ ] **Step 4: Re-run chart tests**

Run: `npm --prefix frontend test -- chartOptions dashboardRanking`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/chartTheme.js frontend/src/utils/chartOptions.js frontend/src/utils/dashboardRanking.js frontend/src/utils/__tests__/chartOptions.spec.js frontend/src/utils/__tests__/dashboardRanking.spec.js
git commit -m "refactor: unify chart readability defaults"
```

### Task 5: Migrate Dashboard and Report Surfaces to the New Display System

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/views/home/Overview.vue`
- Modify: `frontend/src/views/home/Business.vue`
- Modify: `frontend/src/views/reports/ReportDashboard.vue`
- Add: `frontend/src/views/reports/__tests__/ReportDashboardVisual.spec.js`
- Existing Test: `frontend/src/views/__tests__/DashboardWorkspace.spec.js`

- [ ] **Step 1: Add a failing page-level visual structure test**

```js
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const overview = readFileSync(path.resolve(process.cwd(), 'src/views/home/Overview.vue'), 'utf-8')
const business = readFileSync(path.resolve(process.cwd(), 'src/views/home/Business.vue'), 'utf-8')
const reports = readFileSync(path.resolve(process.cwd(), 'src/views/reports/ReportDashboard.vue'), 'utf-8')

describe('dashboard and reports visual contract', () => {
  it('uses shared chart panel wrappers instead of ad-hoc chart card shells', () => {
    expect(overview).toContain('AppChartPanel')
    expect(business).toContain('AppChartPanel')
    expect(reports).toContain('AppSectionCard')
  })

  it('removes hand-crafted inline chart option islands from business dashboard', () => {
    expect(business).not.toContain('resultChart.setOption({')
    expect(business).not.toContain('trendChart.setOption({')
  })
})
```

- [ ] **Step 2: Run dashboard and report tests to verify failure**

Run: `npm --prefix frontend test -- DashboardWorkspace ReportDashboardVisual`
Expected: FAIL because current dashboard files still contain page-local chart option composition and the report shell still uses mixed-generation surface composition.

- [ ] **Step 3: Refactor dashboard and report pages onto the shared visual layer**

```vue
<AppChartPanel class="result-panel">
  <template #header>
    <div class="section-heading">
      <div class="section-heading__title">经营结果</div>
      <div class="section-heading__meta">年度收入与支出结果拆解</div>
    </div>
  </template>
  <div ref="resultChartRef" class="chart-surface chart-surface--result" />
</AppChartPanel>
```

```js
resultChart.setOption(createStackedResultOption({
  income: annualReceiptsAmount.value,
  expenses: annualPaymentsAmount.value,
  theme: readChartTheme()
}))
```

- [ ] **Step 4: Re-run the dashboard/report tests**

Run: `npm --prefix frontend test -- DashboardWorkspace ReportDashboardVisual`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/Dashboard.vue frontend/src/views/home/Overview.vue frontend/src/views/home/Business.vue frontend/src/views/reports/ReportDashboard.vue frontend/src/views/reports/__tests__/ReportDashboardVisual.spec.js frontend/src/views/__tests__/DashboardWorkspace.spec.js
git commit -m "refactor: unify dashboard and report surfaces"
```

### Task 6: Migrate Contract, Expense, System, Audit, Notification, and Login Pages

**Files:**
- Modify: `frontend/src/views/contracts/UpstreamList.vue`
- Modify: `frontend/src/views/contracts/DownstreamList.vue`
- Modify: `frontend/src/views/contracts/ManagementList.vue`
- Modify: `frontend/src/views/contracts/UpstreamDetail.vue`
- Modify: `frontend/src/views/contracts/DownstreamDetail.vue`
- Modify: `frontend/src/views/contracts/ManagementDetail.vue`
- Modify: `frontend/src/views/expenses/ExpenseList.vue`
- Modify: `frontend/src/views/expenses/OrdinaryExpenseList.vue`
- Modify: `frontend/src/views/expenses/ZeroHourLaborList.vue`
- Modify: `frontend/src/views/system/SystemManagement.vue`
- Modify: `frontend/src/views/system/SystemSettings.vue`
- Modify: `frontend/src/views/users/UserManagement.vue`
- Modify: `frontend/src/views/audit/AuditLog.vue`
- Modify: `frontend/src/views/notifications/NotificationCenter.vue`
- Modify: `frontend/src/views/Login.vue`
- Existing Tests:
  - `frontend/src/views/contracts/__tests__/ContractListTableDensity.spec.js`
  - `frontend/src/views/contracts/__tests__/ContractDetailWorkspace.spec.js`
  - `frontend/src/views/expenses/__tests__/OrdinaryExpenseList.spec.js`
  - `frontend/src/views/system/__tests__/SystemSettingsWorkspace.spec.js`
  - `frontend/src/views/__tests__/LoginWorkspace.spec.js`

- [ ] **Step 1: Add a failing page-shell regression test for shared surfaces**

```js
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const upstream = readFileSync(path.resolve(process.cwd(), 'src/views/contracts/UpstreamList.vue'), 'utf-8')
const system = readFileSync(path.resolve(process.cwd(), 'src/views/system/SystemManagement.vue'), 'utf-8')
const login = readFileSync(path.resolve(process.cwd(), 'src/views/Login.vue'), 'utf-8')

describe('page shell visual migration', () => {
  it('keeps list pages on shared workspace and section surfaces', () => {
    expect(upstream).toContain('AppWorkspacePanel')
    expect(upstream).toContain('AppSectionCard')
    expect(upstream).not.toContain('shadow="hover"')
  })

  it('aligns system and login pages to the same quiet surface language', () => {
    expect(system).not.toContain('operation-panel--danger')
    expect(login).toContain('rounded-xl')
  })
})
```

- [ ] **Step 2: Run affected page tests to verify failure**

Run: `npm --prefix frontend test -- ContractListTableDensity ContractDetailWorkspace OrdinaryExpenseList SystemSettingsWorkspace LoginWorkspace`
Expected: FAIL or reveal mixed visual shells that still need to be normalized.

- [ ] **Step 3: Migrate all remaining desktop business pages**

```vue
<AppSectionCard class="upstream-table-section">
  <template #header>合同列表</template>
  <AppDataTable>
    <el-table class="contract-table--dense" ... />
  </AppDataTable>
</AppSectionCard>
```

```scss
.contract-card {
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  background: hsl(var(--card));
  box-shadow: var(--shadow-soft);
}
```

- [ ] **Step 4: Re-run desktop page tests**

Run: `npm --prefix frontend test -- ContractListTableDensity ContractDetailWorkspace OrdinaryExpenseList SystemSettingsWorkspace LoginWorkspace`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/contracts/UpstreamList.vue frontend/src/views/contracts/DownstreamList.vue frontend/src/views/contracts/ManagementList.vue frontend/src/views/contracts/UpstreamDetail.vue frontend/src/views/contracts/DownstreamDetail.vue frontend/src/views/contracts/ManagementDetail.vue frontend/src/views/expenses/ExpenseList.vue frontend/src/views/expenses/OrdinaryExpenseList.vue frontend/src/views/expenses/ZeroHourLaborList.vue frontend/src/views/system/SystemManagement.vue frontend/src/views/system/SystemSettings.vue frontend/src/views/users/UserManagement.vue frontend/src/views/audit/AuditLog.vue frontend/src/views/notifications/NotificationCenter.vue frontend/src/views/Login.vue frontend/src/views/contracts/__tests__/ContractListTableDensity.spec.js frontend/src/views/contracts/__tests__/ContractDetailWorkspace.spec.js frontend/src/views/expenses/__tests__/OrdinaryExpenseList.spec.js frontend/src/views/system/__tests__/SystemSettingsWorkspace.spec.js frontend/src/views/__tests__/LoginWorkspace.spec.js
git commit -m "refactor: unify desktop business page presentation"
```

### Task 7: Migrate Mobile Business Pages and Run Final Verification

**Files:**
- Modify: `frontend/src/views/mobile/ContractListMobile.vue`
- Modify: `frontend/src/views/mobile/ExpenseListMobile.vue`
- Modify: `frontend/src/views/mobile/MobileLayout.vue`
- Existing Tests:
  - `frontend/src/views/mobile/__tests__/MobileWorkspace.spec.js`
  - `frontend/src/views/mobile/__tests__/MobileAdaptation.spec.js`
- Final Verification:
  - `frontend/src/utils/__tests__/chartOptions.spec.js`
  - `frontend/src/utils/__tests__/dashboardRanking.spec.js`
  - `frontend/src/views/__tests__/DashboardWorkspace.spec.js`
  - `frontend/src/views/contracts/__tests__/ContractListTableDensity.spec.js`

- [ ] **Step 1: Add a failing mobile visual test**

```js
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const mobileContracts = readFileSync(path.resolve(process.cwd(), 'src/views/mobile/ContractListMobile.vue'), 'utf-8')
const mobileExpenses = readFileSync(path.resolve(process.cwd(), 'src/views/mobile/ExpenseListMobile.vue'), 'utf-8')

describe('mobile visual migration', () => {
  it('moves mobile pages onto the same card and toolbar language', () => {
    expect(mobileContracts).toContain('mobile-contract-list__toolbar')
    expect(mobileContracts).not.toContain('24px')
    expect(mobileExpenses).toContain('mobile-expense-list__toolbar')
  })
})
```

- [ ] **Step 2: Run mobile tests to verify failure**

Run: `npm --prefix frontend test -- MobileWorkspace MobileAdaptation MobileVisualShell`
Expected: FAIL because mobile pages still use older, separate styling language.

- [ ] **Step 3: Apply the mobile page migration**

```scss
.mobile-contract-list__toolbar,
.mobile-expense-list__toolbar {
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  background: hsl(var(--card));
  box-shadow: var(--shadow-soft);
}

.mobile-contract-card,
.mobile-expense-card {
  border-radius: var(--radius);
  border: 1px solid hsl(var(--border));
  background: hsl(var(--card));
}
```

- [ ] **Step 4: Run final frontend verification**

Run:

```bash
npm --prefix frontend test -- AppMetricCard AppSectionCard AppChartPanel LayoutWorkspaceVisual DashboardWorkspace ReportDashboardVisual ContractListTableDensity ContractDetailWorkspace OrdinaryExpenseList SystemSettingsWorkspace LoginWorkspace MobileWorkspace MobileAdaptation MobileVisualShell chartOptions dashboardRanking
npm --prefix frontend run build
```

Expected:
- all targeted Vitest suites PASS
- production build PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/mobile/ContractListMobile.vue frontend/src/views/mobile/ExpenseListMobile.vue frontend/src/views/mobile/MobileLayout.vue frontend/src/views/mobile/__tests__/MobileWorkspace.spec.js frontend/src/views/mobile/__tests__/MobileAdaptation.spec.js frontend/src/views/mobile/__tests__/MobileVisualShell.spec.js frontend/src/views/__tests__/LayoutWorkspaceVisual.spec.js frontend/src/views/reports/__tests__/ReportDashboardVisual.spec.js
git commit -m "refactor: complete mobile frontend visual unification"
```

## Self-Review

### Spec Coverage

- Whole-site scope: covered by Tasks 5 and 7.
- Desktop and mobile together: covered by Tasks 3, 5, and 7.
- Light and dark themes: covered by Task 1 token normalization.
- shadcn/ui-inspired visual direction: covered by Tasks 1 through 3.
- Chart readability and no overlap: covered by Task 4 and downstream page migration in Task 5.
- Stronger page consistency: covered by shared primitive work in Task 2 and page migration in Tasks 5 and 7.

### Placeholder Scan

- No `TODO`, `TBD`, or “similar to previous task” placeholders remain.
- Every task names exact files and exact verification commands.
- Every code-changing step includes concrete code snippets for the intended change.

### Type Consistency

- Shared surfaces consistently use `AppMetricCard`, `AppSectionCard`, `AppWorkspacePanel`, and `AppChartPanel`.
- Chart helper naming is consistent across `chartTheme.js`, `chartOptions.js`, and `dashboardRanking.js`.
- Mobile and desktop shell tasks both depend on the same token ladder defined in Task 1.

Plan complete and saved to `docs/superpowers/plans/2026-04-11-frontend-visual-unification-implementation-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
