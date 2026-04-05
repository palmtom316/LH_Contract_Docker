# Frontend Minimalist SaaS Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the frontend shell and core business surfaces into a unified minimalist SaaS interface with light/dark themes, a sidebar-bottom user card, a top-right notification center, consistent shared UI primitives, and responsive chart-safe layouts.

**Architecture:** Keep Vue 3 + Element Plus + existing routes, but introduce a semantic theme/token layer, shared shell subcomponents, a small UI preference store, and reusable chart option helpers. Rework the application shell first, then normalize shared primitives, then restyle dashboard, reports, and contract list pages against the new system, with responsive behavior built into each phase.

**Tech Stack:** Vue 3, Vite, Pinia, Vue Router, Element Plus, Vant, ECharts, Sass, Vitest, Vue Test Utils

---

## File Structure Map

### Existing files to modify
- `frontend/package.json`
- `frontend/src/main.js`
- `frontend/src/router/index.js`
- `frontend/src/styles/tokens.scss`
- `frontend/src/styles/index.scss`
- `frontend/src/views/Layout.vue`
- `frontend/src/views/mobile/MobileLayout.vue`
- `frontend/src/views/home/Overview.vue`
- `frontend/src/views/reports/ReportDashboard.vue`
- `frontend/src/views/contracts/UpstreamList.vue`
- `frontend/src/views/contracts/DownstreamList.vue`
- `frontend/src/views/contracts/ManagementList.vue`
- `frontend/src/stores/system.js`
- `frontend/src/stores/user.js`
- `frontend/src/utils/echarts.js`

### New files to create
- `frontend/src/stores/ui.js`
- `frontend/src/composables/useTheme.js`
- `frontend/src/components/layout/AppNotificationBell.vue`
- `frontend/src/components/layout/SidebarUserCard.vue`
- `frontend/src/components/layout/AppTopbarActions.vue`
- `frontend/src/components/layout/AppPageHeader.vue`
- `frontend/src/components/ui/AppSectionCard.vue`
- `frontend/src/components/ui/AppFilterBar.vue`
- `frontend/src/components/ui/AppEmptyState.vue`
- `frontend/src/components/ui/AppDataTable.vue`
- `frontend/src/components/ui/AppMetricCard.vue`
- `frontend/src/components/ui/AppThemeToggle.vue`
- `frontend/src/views/notifications/NotificationCenter.vue`
- `frontend/src/api/notifications.js`
- `frontend/src/utils/notificationAdapter.js`
- `frontend/src/utils/chartTheme.js`
- `frontend/src/utils/chartOptions.js`
- `frontend/src/test/setup.js`
- `frontend/src/stores/__tests__/ui.spec.js`
- `frontend/src/utils/__tests__/notificationAdapter.spec.js`
- `frontend/src/utils/__tests__/chartOptions.spec.js`

---

### Task 1: Add Theme And UI Preference Infrastructure

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/main.js`
- Modify: `frontend/src/styles/tokens.scss`
- Modify: `frontend/src/styles/index.scss`
- Create: `frontend/src/stores/ui.js`
- Create: `frontend/src/composables/useTheme.js`
- Create: `frontend/src/test/setup.js`
- Test: `frontend/src/stores/__tests__/ui.spec.js`

- [x] **Step 1: Add Vitest and test scripts so UI infrastructure can be developed with TDD**

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^6.0.2",
    "@vue/test-utils": "^2.4.6",
    "jsdom": "^26.1.0",
    "vitest": "^3.2.4"
  }
}
```

- [x] **Step 2: Write the failing test for theme persistence and toggle behavior**

```js
import { beforeEach, describe, expect, it } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUiStore } from '../ui'

describe('ui store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    document.documentElement.removeAttribute('data-theme')
  })

  it('defaults to light theme and persists manual toggle', () => {
    const store = useUiStore()

    expect(store.theme).toBe('light')

    store.setTheme('dark')

    expect(store.theme).toBe('dark')
    expect(localStorage.getItem('lh-theme')).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
  })
})
```

- [x] **Step 3: Run the test to verify it fails because the store does not exist yet**

Run: `cd frontend && npm run test -- src/stores/__tests__/ui.spec.js`

Expected:
- FAIL with module resolution error for `../ui`

- [x] **Step 4: Create the UI preference store and theme composable**

```js
// frontend/src/stores/ui.js
import { defineStore } from 'pinia'

const THEME_KEY = 'lh-theme'

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme
}

export const useUiStore = defineStore('ui', {
  state: () => ({
    theme: localStorage.getItem(THEME_KEY) || 'light',
    notificationDrawerOpen: false
  }),
  actions: {
    initTheme() {
      applyTheme(this.theme)
    },
    setTheme(theme) {
      this.theme = theme
      localStorage.setItem(THEME_KEY, theme)
      applyTheme(theme)
    },
    toggleTheme() {
      this.setTheme(this.theme === 'light' ? 'dark' : 'light')
    }
  }
})
```

```js
// frontend/src/composables/useTheme.js
import { computed } from 'vue'
import { useUiStore } from '@/stores/ui'

export function useTheme() {
  const uiStore = useUiStore()

  return {
    theme: computed(() => uiStore.theme),
    isDark: computed(() => uiStore.theme === 'dark'),
    setTheme: uiStore.setTheme,
    toggleTheme: uiStore.toggleTheme
  }
}
```

- [x] **Step 5: Wire the UI store into app startup**

```js
// frontend/src/main.js
import { createPinia } from 'pinia'
import { useUiStore } from '@/stores/ui'

const pinia = createPinia()
app.use(pinia)

const uiStore = useUiStore(pinia)
uiStore.initTheme()
```

- [x] **Step 6: Replace the current token file with semantic light/dark variables**

```scss
:root,
:root[data-theme='light'] {
  --font-family-base: "PingFang SC", "Noto Sans SC", "Helvetica Neue", Arial, sans-serif;
  --brand-primary: #2563eb;
  --brand-primary-strong: #1d4ed8;
  --brand-primary-soft: #e8f0ff;
  --brand-accent: #0f766e;
  --status-success: #0f766e;
  --status-warning: #b45309;
  --status-danger: #b83280;
  --status-info: #475569;
  --surface-page: #f5f7fb;
  --surface-panel: #ffffff;
  --surface-panel-muted: #eef2f7;
  --surface-sidebar: #0f172a;
  --surface-sidebar-hover: #162033;
  --surface-sidebar-active: #1f2a44;
  --surface-overlay: rgba(15, 23, 42, 0.48);
  --border-subtle: #d7dfeb;
  --border-strong: #b6c2d2;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #64748b;
  --text-inverse: #f8fafc;
  --shadow-card: 0 18px 40px rgba(15, 23, 42, 0.08);
  --shadow-soft: 0 8px 20px rgba(15, 23, 42, 0.06);
  --shadow-focus: 0 0 0 3px rgba(37, 99, 235, 0.2);
  --radius-sm: 10px;
  --radius-md: 16px;
  --radius-lg: 22px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --sidebar-width: 248px;
  --header-height: 72px;
}

:root[data-theme='dark'] {
  --brand-primary: #60a5fa;
  --brand-primary-strong: #3b82f6;
  --brand-primary-soft: rgba(96, 165, 250, 0.16);
  --brand-accent: #2dd4bf;
  --status-success: #2dd4bf;
  --status-warning: #f59e0b;
  --status-danger: #f472b6;
  --status-info: #94a3b8;
  --surface-page: #09111f;
  --surface-panel: #0f172a;
  --surface-panel-muted: #111c31;
  --surface-sidebar: #050b16;
  --surface-sidebar-hover: #0c1524;
  --surface-sidebar-active: #122038;
  --surface-overlay: rgba(2, 6, 23, 0.68);
  --border-subtle: #22314b;
  --border-strong: #334155;
  --text-primary: #e5eefb;
  --text-secondary: #c7d2e3;
  --text-muted: #8aa0ba;
  --text-inverse: #f8fafc;
  --shadow-card: 0 20px 42px rgba(0, 0, 0, 0.28);
  --shadow-soft: 0 10px 28px rgba(0, 0, 0, 0.22);
  --shadow-focus: 0 0 0 3px rgba(96, 165, 250, 0.28);
}
```

- [x] **Step 7: Normalize global base styles for both themes**

```scss
html,
body,
#app {
  min-height: 100vh;
}

body {
  margin: 0;
  background: var(--surface-page);
  color: var(--text-primary);
  transition: background-color 160ms ease, color 160ms ease;
}

.el-button,
.el-input__wrapper,
.el-select__wrapper,
.el-textarea__inner,
.el-card {
  transition: background-color 160ms ease, border-color 160ms ease, box-shadow 160ms ease, color 160ms ease;
}
```

- [x] **Step 8: Run the focused test to verify the theme store works**

Run: `cd frontend && npm run test -- src/stores/__tests__/ui.spec.js`

Expected:
- PASS with 1 passing test

- [x] **Step 9: Run a production build to catch SCSS or import regressions**

Run: `cd frontend && npm run build`

Expected:
- `vite build` completes successfully

- [x] **Step 10: Commit**

```bash
git add frontend/package.json frontend/src/main.js frontend/src/styles/tokens.scss frontend/src/styles/index.scss frontend/src/stores/ui.js frontend/src/composables/useTheme.js frontend/src/test/setup.js frontend/src/stores/__tests__/ui.spec.js
git commit -m "feat: add theme preference infrastructure"
```

### Task 2: Build Notification Aggregation And Dedicated Notification Route

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/stores/system.js`
- Create: `frontend/src/api/notifications.js`
- Create: `frontend/src/utils/notificationAdapter.js`
- Create: `frontend/src/views/notifications/NotificationCenter.vue`
- Test: `frontend/src/utils/__tests__/notificationAdapter.spec.js`

- [x] **Step 1: Write the failing test for notification aggregation**

```js
import { describe, expect, it } from 'vitest'
import { buildNotifications } from '../notificationAdapter'

describe('buildNotifications', () => {
  it('maps audit and contract reminders into sorted notification items', () => {
    const result = buildNotifications({
      audits: [
        { id: 1, action: 'LOGIN', description: '管理员登录', created_at: '2026-04-05T08:00:00Z' }
      ],
      reminders: [
        { id: 'exp-1', type: 'contract_expiry', title: '合同将到期', due_at: '2026-04-06T08:00:00Z' }
      ]
    })

    expect(result[0]).toMatchObject({
      type: 'contract_expiry',
      title: '合同将到期'
    })
    expect(result[1]).toMatchObject({
      type: 'audit',
      title: '管理员登录'
    })
  })
})
```

- [x] **Step 2: Run the test to verify it fails because the adapter does not exist**

Run: `cd frontend && npm run test -- src/utils/__tests__/notificationAdapter.spec.js`

Expected:
- FAIL with module resolution error for `../notificationAdapter`

- [x] **Step 3: Create the notification adapter with stable categories**

```js
// frontend/src/utils/notificationAdapter.js
function toEpoch(value) {
  return value ? new Date(value).getTime() : 0
}

export function buildNotifications({ audits = [], reminders = [] }) {
  const auditItems = audits.map(item => ({
    id: `audit-${item.id}`,
    type: 'audit',
    title: item.description || item.action,
    subtitle: '系统审计事件',
    createdAt: item.created_at,
    unread: true
  }))

  const reminderItems = reminders.map(item => ({
    id: String(item.id),
    type: item.type,
    title: item.title,
    subtitle: item.subtitle || '业务提醒',
    createdAt: item.due_at || item.created_at,
    unread: true
  }))

  return [...auditItems, ...reminderItems].sort((a, b) => toEpoch(b.createdAt) - toEpoch(a.createdAt))
}
```

- [x] **Step 4: Add a lightweight notifications API facade that reuses existing endpoints**

```js
// frontend/src/api/notifications.js
import request from '@/utils/request'
import { buildNotifications } from '@/utils/notificationAdapter'

export async function fetchNotifications() {
  const [audits, expiringContracts] = await Promise.all([
    request.get('/audit/logs', { params: { page: 1, page_size: 10 } }).catch(() => ({ items: [] })),
    request.get('/dashboard/stats').catch(() => ({ reminders: [] }))
  ])

  return buildNotifications({
    audits: audits.items || audits.results || [],
    reminders: expiringContracts.reminders || []
  })
}
```

- [x] **Step 5: Add the dedicated notification route**

```js
{
  path: 'notifications',
  name: 'NotificationCenter',
  component: () => import('@/views/notifications/NotificationCenter.vue'),
  meta: { title: '系统通知' }
}
```

- [x] **Step 6: Create the notification page shell with grouped filters**

```vue
<template>
  <div class="notification-center-page app-container">
    <app-page-header
      title="系统通知"
      description="查看系统提醒、合同到期提醒与关键审计事件"
    />

    <app-section-card>
      <template #actions>
        <el-segmented v-model="activeFilter" :options="filterOptions" />
      </template>

      <div v-if="filteredNotifications.length" class="notification-list">
        <article v-for="item in filteredNotifications" :key="item.id" class="notification-item">
          <div class="notification-item__title">{{ item.title }}</div>
          <div class="notification-item__meta">{{ item.subtitle }} · {{ formatTime(item.createdAt) }}</div>
        </article>
      </div>
      <app-empty-state v-else title="暂无通知" description="当前没有新的系统提醒。" />
    </app-section-card>
  </div>
</template>
```

- [x] **Step 7: Run the notification adapter test**

Run: `cd frontend && npm run test -- src/utils/__tests__/notificationAdapter.spec.js`

Expected:
- PASS with 1 passing test

- [x] **Step 8: Run a production build**

Run: `cd frontend && npm run build`

Expected:
- build succeeds with the new notification route and imports

- [x] **Step 9: Commit**

```bash
git add frontend/src/router/index.js frontend/src/api/notifications.js frontend/src/utils/notificationAdapter.js frontend/src/views/notifications/NotificationCenter.vue frontend/src/utils/__tests__/notificationAdapter.spec.js
git commit -m "feat: add notification center data layer"
```

### Task 3: Refactor The Application Shell Into A Minimalist SaaS Layout

**Files:**
- Modify: `frontend/src/views/Layout.vue`
- Modify: `frontend/src/views/mobile/MobileLayout.vue`
- Create: `frontend/src/components/layout/AppNotificationBell.vue`
- Create: `frontend/src/components/layout/SidebarUserCard.vue`
- Create: `frontend/src/components/layout/AppTopbarActions.vue`
- Create: `frontend/src/components/ui/AppThemeToggle.vue`
- Test: `frontend/src/stores/__tests__/ui.spec.js`

- [x] **Step 1: Extend the UI store test to cover notification drawer state**

```js
it('tracks notification drawer visibility', () => {
  const store = useUiStore()

  store.notificationDrawerOpen = true

  expect(store.notificationDrawerOpen).toBe(true)
})
```

- [x] **Step 2: Run the UI store test to ensure the new assertion fails first**

Run: `cd frontend && npm run test -- src/stores/__tests__/ui.spec.js`

Expected:
- FAIL because the store lacks explicit open/close actions

- [x] **Step 3: Add explicit UI store actions for shell overlays**

```js
openNotificationDrawer() {
  this.notificationDrawerOpen = true
},
closeNotificationDrawer() {
  this.notificationDrawerOpen = false
}
```

- [x] **Step 4: Create the bottom-left sidebar user card component**

```vue
<template>
  <section class="sidebar-user-card">
    <el-avatar :size="40" :icon="UserFilled" class="sidebar-user-card__avatar" />
    <div class="sidebar-user-card__meta">
      <div class="sidebar-user-card__name">{{ user.full_name || user.username }}</div>
      <div class="sidebar-user-card__role">{{ roleDisplay }}</div>
    </div>
    <el-dropdown @command="$emit('command', $event)">
      <button type="button" class="sidebar-user-card__trigger" aria-label="打开用户操作">
        <el-icon><MoreFilled /></el-icon>
      </button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="profile">个人信息</el-dropdown-item>
          <el-dropdown-item command="changePassword">修改密码</el-dropdown-item>
          <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </section>
</template>
```

- [x] **Step 5: Create the top-right notification bell and theme toggle**

```vue
<template>
  <div class="topbar-actions">
    <app-theme-toggle />
    <app-notification-bell :items="items" @view-all="router.push('/notifications')" />
  </div>
</template>
```

- [x] **Step 6: Replace the top-right user block in the desktop shell with the new action cluster**

```vue
<!-- frontend/src/views/Layout.vue -->
<div class="right-panel">
  <app-topbar-actions :notifications="notifications" />
</div>

<sidebar-user-card
  v-if="!isCollapse"
  class="sidebar-user-slot"
  :user="userStore.user"
  :role-display="userStore.roleDisplay"
  @command="handleCommand"
/>
```

- [x] **Step 7: Rebuild the mobile shell so the drawer contains the user card at the bottom and the top bar contains theme + notifications**

```vue
<van-nav-bar fixed placeholder>
  <template #left>
    <button type="button" class="mobile-nav-trigger" @click="drawerOpen = true">
      <el-icon><Expand /></el-icon>
    </button>
  </template>
  <template #title>{{ pageTitle }}</template>
  <template #right>
    <app-topbar-actions :notifications="notifications" compact />
  </template>
</van-nav-bar>
```

- [x] **Step 8: Run the UI store test and the build**

Run: `cd frontend && npm run test -- src/stores/__tests__/ui.spec.js && npm run build`

Expected:
- Tests pass
- Build succeeds

- [x] **Step 9: Commit**

```bash
git add frontend/src/stores/ui.js frontend/src/views/Layout.vue frontend/src/views/mobile/MobileLayout.vue frontend/src/components/layout/AppNotificationBell.vue frontend/src/components/layout/SidebarUserCard.vue frontend/src/components/layout/AppTopbarActions.vue frontend/src/components/ui/AppThemeToggle.vue frontend/src/stores/__tests__/ui.spec.js
git commit -m "feat: refactor app shell for minimalist saas layout"
```

### Task 4: Introduce Shared UI Primitives For Cards, Filters, Tables, And Page Headers

**Files:**
- Create: `frontend/src/components/ui/AppSectionCard.vue`
- Create: `frontend/src/components/ui/AppFilterBar.vue`
- Create: `frontend/src/components/ui/AppEmptyState.vue`
- Create: `frontend/src/components/ui/AppDataTable.vue`
- Create: `frontend/src/components/ui/AppMetricCard.vue`
- Create: `frontend/src/components/layout/AppPageHeader.vue`
- Modify: `frontend/src/styles/index.scss`
- Test: `frontend/src/stores/__tests__/ui.spec.js`

- [x] **Step 1: Add a render-level smoke test for a shared metric card**

```js
import { mount } from '@vue/test-utils'
import AppMetricCard from '@/components/ui/AppMetricCard.vue'

it('renders metric title and value content', () => {
  const wrapper = mount(AppMetricCard, {
    props: { title: '年度上游签约', value: '12 单' }
  })

  expect(wrapper.text()).toContain('年度上游签约')
  expect(wrapper.text()).toContain('12 单')
})
```

- [x] **Step 2: Run the test and verify it fails because the component does not exist yet**

Run: `cd frontend && npm run test -- src/stores/__tests__/ui.spec.js`

Expected:
- FAIL due to missing `AppMetricCard.vue`

- [x] **Step 3: Create the shared UI primitive components**

```vue
<!-- frontend/src/components/ui/AppSectionCard.vue -->
<template>
  <el-card class="app-section-card" shadow="never">
    <template v-if="$slots.header || $slots.actions" #header>
      <div class="app-section-card__header">
        <div class="app-section-card__title"><slot name="header" /></div>
        <div class="app-section-card__actions"><slot name="actions" /></div>
      </div>
    </template>
    <slot />
  </el-card>
</template>
```

```vue
<!-- frontend/src/components/layout/AppPageHeader.vue -->
<template>
  <header class="app-page-header">
    <div>
      <h1 class="app-page-header__title">{{ title }}</h1>
      <p v-if="description" class="app-page-header__description">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="app-page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>
```

- [x] **Step 4: Add global primitive styles that normalize buttons, cards, form controls, and tables**

```scss
.el-button {
  min-height: 40px;
  border-radius: 12px;
  font-weight: 600;
  padding-inline: 16px;
  box-shadow: none;
}

.el-button--primary {
  background: var(--brand-primary);
  border-color: var(--brand-primary);
}

.el-card {
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-panel);
  box-shadow: var(--shadow-soft);
}

.el-input__wrapper,
.el-select__wrapper,
.el-textarea__inner {
  min-height: 42px;
  border-radius: 12px;
  background: var(--surface-panel);
}
```

- [x] **Step 5: Run the metric-card test and production build**

Run: `cd frontend && npm run test -- src/stores/__tests__/ui.spec.js && npm run build`

Expected:
- Tests pass
- Build succeeds

- [x] **Step 6: Commit**

```bash
git add frontend/src/components/ui/AppSectionCard.vue frontend/src/components/ui/AppFilterBar.vue frontend/src/components/ui/AppEmptyState.vue frontend/src/components/ui/AppDataTable.vue frontend/src/components/ui/AppMetricCard.vue frontend/src/components/layout/AppPageHeader.vue frontend/src/styles/index.scss frontend/src/stores/__tests__/ui.spec.js
git commit -m "feat: add shared saas ui primitives"
```

### Task 5: Centralize Chart Theme And Collision-Safe Option Builders

**Files:**
- Modify: `frontend/src/utils/echarts.js`
- Create: `frontend/src/utils/chartTheme.js`
- Create: `frontend/src/utils/chartOptions.js`
- Test: `frontend/src/utils/__tests__/chartOptions.spec.js`

- [x] **Step 1: Write a failing test that locks in chart label spacing and legend behavior**

```js
import { describe, expect, it } from 'vitest'
import { createBarChartOption } from '../chartOptions'

describe('createBarChartOption', () => {
  it('reserves legend and label space for readability', () => {
    const option = createBarChartOption({
      categories: ['2026-01', '2026-02'],
      series: [{ name: '收入', data: [10, 20], color: '#2563eb' }]
    })

    expect(option.grid.containLabel).toBe(true)
    expect(option.legend.bottom).toBe(0)
    expect(option.xAxis.axisLabel.hideOverlap).toBe(true)
  })
})
```

- [x] **Step 2: Run the test to verify it fails because the option builder does not exist**

Run: `cd frontend && npm run test -- src/utils/__tests__/chartOptions.spec.js`

Expected:
- FAIL with module resolution error for `../chartOptions`

- [x] **Step 3: Create theme-aware chart token readers**

```js
// frontend/src/utils/chartTheme.js
export function readChartTheme() {
  const styles = getComputedStyle(document.documentElement)

  return {
    text: styles.getPropertyValue('--text-secondary').trim(),
    textStrong: styles.getPropertyValue('--text-primary').trim(),
    border: styles.getPropertyValue('--border-subtle').trim(),
    panel: styles.getPropertyValue('--surface-panel').trim(),
    primary: styles.getPropertyValue('--brand-primary').trim(),
    success: styles.getPropertyValue('--status-success').trim(),
    warning: styles.getPropertyValue('--status-warning').trim(),
    danger: styles.getPropertyValue('--status-danger').trim(),
    info: styles.getPropertyValue('--status-info').trim()
  }
}
```

- [x] **Step 4: Create reusable collision-safe chart builders**

```js
// frontend/src/utils/chartOptions.js
import { readChartTheme } from './chartTheme'

export function createBarChartOption({ categories, series }) {
  const theme = readChartTheme()

  return {
    tooltip: { trigger: 'axis', confine: true },
    legend: {
      bottom: 0,
      textStyle: { color: theme.text, fontSize: 12 }
    },
    grid: {
      left: '8%',
      right: '4%',
      top: '12%',
      bottom: '64px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        hideOverlap: true,
        color: theme.text,
        fontSize: 11
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: theme.text },
      splitLine: { lineStyle: { color: theme.border } }
    },
    series: series.map(item => ({
      ...item,
      type: 'bar',
      barMaxWidth: 18
    }))
  }
}
```

- [x] **Step 5: Export the helper functions from the shared chart utility layer**

```js
// frontend/src/utils/echarts.js
export { createBarChartOption } from './chartOptions'
export { readChartTheme } from './chartTheme'
```

- [x] **Step 6: Run the chart option test and build**

Run: `cd frontend && npm run test -- src/utils/__tests__/chartOptions.spec.js && npm run build`

Expected:
- Tests pass
- Build succeeds

- [x] **Step 7: Commit**

```bash
git add frontend/src/utils/echarts.js frontend/src/utils/chartTheme.js frontend/src/utils/chartOptions.js frontend/src/utils/__tests__/chartOptions.spec.js
git commit -m "feat: centralize chart theme and spacing helpers"
```

### Task 6: Redesign Dashboard With Shared Primitives And Safe Charts

**Files:**
- Modify: `frontend/src/views/home/Overview.vue`
- Modify: `frontend/src/views/Dashboard.vue`
- Reuse: `frontend/src/components/ui/AppMetricCard.vue`
- Reuse: `frontend/src/components/layout/AppPageHeader.vue`
- Reuse: `frontend/src/components/ui/AppSectionCard.vue`
- Reuse: `frontend/src/utils/chartOptions.js`
- Test: `frontend/src/utils/__tests__/chartOptions.spec.js`

- [x] **Step 1: Add a regression test for pie-chart label configuration**

```js
import { createPieChartOption } from '../chartOptions'

it('moves pie labels outside the plot area', () => {
  const option = createPieChartOption({
    title: '合同分类',
    data: [{ name: '工程', value: 30 }]
  })

  expect(option.series[0].label.position).toBe('outside')
  expect(option.series[0].avoidLabelOverlap).toBe(true)
})
```

- [x] **Step 2: Run the chart test to verify the pie helper fails first**

Run: `cd frontend && npm run test -- src/utils/__tests__/chartOptions.spec.js`

Expected:
- FAIL because `createPieChartOption` is not implemented

- [x] **Step 3: Extend chart options with a pie builder**

```js
export function createPieChartOption({ title, data }) {
  const theme = readChartTheme()

  return {
    title: {
      text: title,
      left: 'center',
      textStyle: { color: theme.textStrong, fontSize: 14 }
    },
    tooltip: { trigger: 'item', confine: true },
    legend: {
      bottom: 0,
      type: 'scroll',
      textStyle: { color: theme.text }
    },
    series: [
      {
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['50%', '42%'],
        avoidLabelOverlap: true,
        label: { position: 'outside', color: theme.text },
        labelLine: { show: true, length: 10, length2: 8 },
        data
      }
    ]
  }
}
```

- [x] **Step 4: Replace the current dashboard metric cards with `AppMetricCard` and page framing primitives**

```vue
<app-page-header
  title="首页概览"
  description="统一查看经营指标、趋势和合同分类表现"
/>

<section class="dashboard-metric-grid">
  <app-metric-card
    v-for="item in cardData"
    :key="item.title"
    :title="item.title"
    :value="item.count !== undefined ? `${item.count} 单` : `¥ ${formatWan(item.value)} 万`"
    :subtitle="item.subInfo"
    :tone="item.tone"
  />
</section>
```

- [x] **Step 5: Replace inline chart option objects with shared builders and eliminate hard-coded colors**

```js
import { createBarChartOption, createPieChartOption } from '@/utils/chartOptions'

barChart.setOption(createBarChartOption({
  categories: data.months,
  series: [
    { name: '月度收入', data: data.income.map(v => Number((v / 10000).toFixed(2))), color: 'var(--status-success)' }
  ]
}))

pieCategoryChart.setOption(createPieChartOption({
  title: '合同类别',
  data: normalizedCategoryData
}))
```

- [x] **Step 6: Collapse the mobile dashboard into stacked cards and tab-safe charts using the new spacing system**

```scss
.dashboard-metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

@media (max-width: 767px) {
  .dashboard-metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
```

- [x] **Step 7: Run the chart tests and build**

Run: `cd frontend && npm run test -- src/utils/__tests__/chartOptions.spec.js && npm run build`

Expected:
- Tests pass
- Build succeeds

- [x] **Step 8: Commit**

```bash
git add frontend/src/views/home/Overview.vue frontend/src/views/Dashboard.vue frontend/src/utils/chartOptions.js frontend/src/utils/__tests__/chartOptions.spec.js
git commit -m "feat: redesign dashboard with shared charts"
```

### Task 7: Redesign Reports Workspace With Unified Filters, Cards, And Mobile Layout

**Files:**
- Modify: `frontend/src/views/reports/ReportDashboard.vue`
- Reuse: `frontend/src/components/layout/AppPageHeader.vue`
- Reuse: `frontend/src/components/ui/AppSectionCard.vue`
- Reuse: `frontend/src/components/ui/AppFilterBar.vue`
- Reuse: `frontend/src/components/ui/AppDataTable.vue`
- Reuse: `frontend/src/components/ui/AppEmptyState.vue`
- Reuse: `frontend/src/styles/index.scss`
- Test: `frontend/src/utils/__tests__/chartOptions.spec.js`

- [x] **Step 1: Write a small render test for the report page header and filter arrangement**

```js
import { mount } from '@vue/test-utils'
import AppPageHeader from '@/components/layout/AppPageHeader.vue'

it('renders page title and description', () => {
  const wrapper = mount(AppPageHeader, {
    props: { title: '报表统计', description: '查看和导出统计结果' }
  })

  expect(wrapper.text()).toContain('报表统计')
  expect(wrapper.text()).toContain('查看和导出统计结果')
})
```

- [x] **Step 2: Run the UI test to ensure the contract from Task 4 still passes before refactoring**

Run: `cd frontend && npm run test -- src/stores/__tests__/ui.spec.js`

Expected:
- PASS, creating a safe baseline before the report refactor

- [x] **Step 3: Replace the ad-hoc page header and export blocks with shared cards and filter bars**

```vue
<app-page-header
  title="报表统计"
  description="统一查询成本报表、导出业务报表和查看结果表格"
/>

<app-section-card>
  <template #header>月度 / 季度成本报表</template>
  <app-filter-bar>
    <el-date-picker v-model="costMonth" type="month" value-format="YYYY-MM" />
    <el-button type="primary" :loading="costLoading" @click="handleQueryCostReport">查询报表</el-button>
    <el-button type="primary" plain :loading="costExportLoading" @click="handleExportCostReport">导出 Excel</el-button>
  </app-filter-bar>
</app-section-card>
```

- [x] **Step 4: Convert the report export grid to responsive cards with uniform action buttons**

```scss
.report-export-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

@media (max-width: 1279px) {
  .report-export-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 767px) {
  .report-export-grid {
    grid-template-columns: 1fr;
  }
}
```

- [x] **Step 5: Normalize the main report tables to the shared table wrapper and mobile-friendly scroll behavior**

```vue
<app-data-table>
  <el-table
    :data="monthlyTableData"
    v-loading="costLoading"
    class="cost-report-table"
  >
    <!-- existing columns stay, but card, spacing, and header styles move to wrapper -->
  </el-table>
</app-data-table>
```

- [x] **Step 6: Run build verification**

Run: `cd frontend && npm run build`

Expected:
- Build succeeds with the refactored report view

- [x] **Step 7: Commit**

```bash
git add frontend/src/views/reports/ReportDashboard.vue frontend/src/styles/index.scss
git commit -m "feat: redesign reports workspace"
```

### Task 8: Redesign Contract Lists And Align Remaining Core Business Surfaces

**Files:**
- Modify: `frontend/src/views/contracts/UpstreamList.vue`
- Modify: `frontend/src/views/contracts/DownstreamList.vue`
- Modify: `frontend/src/views/contracts/ManagementList.vue`
- Reuse: `frontend/src/components/ui/AppFilterBar.vue`
- Reuse: `frontend/src/components/ui/AppDataTable.vue`
- Reuse: `frontend/src/components/ui/AppSectionCard.vue`
- Reuse: `frontend/src/components/ui/AppEmptyState.vue`
- Reuse: `frontend/src/styles/index.scss`
- Test: `frontend/src/stores/__tests__/ui.spec.js`

- [x] **Step 1: Add a contract-list smoke test for empty-state rendering**

```js
import { mount } from '@vue/test-utils'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'

it('renders reusable empty-state copy', () => {
  const wrapper = mount(AppEmptyState, {
    props: { title: '暂无合同', description: '调整筛选条件后重试。' }
  })

  expect(wrapper.text()).toContain('暂无合同')
  expect(wrapper.text()).toContain('调整筛选条件后重试。')
})
```

- [x] **Step 2: Run the smoke test to verify the shared UI primitives still behave correctly**

Run: `cd frontend && npm run test -- src/stores/__tests__/ui.spec.js`

Expected:
- PASS before modifying large list pages

- [x] **Step 3: Replace the current filter cards with `AppFilterBar` and unify action ordering**

```vue
<app-section-card>
  <template #header>合同管理</template>
  <app-filter-bar>
    <el-input v-model="queryParams.keyword" placeholder="合同序号/编号/名称/甲方" clearable />
    <el-select v-model="queryParams.status" clearable placeholder="合同状态" />
    <el-button type="primary" @click="handleQuery">搜索</el-button>
    <el-button @click="resetQuery">重置</el-button>
    <el-button type="primary" plain @click="handleExport">导出 Excel</el-button>
  </app-filter-bar>
</app-section-card>
```

- [x] **Step 4: Normalize desktop tables and mobile cards to one visual language**

```scss
.contract-mobile-card {
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-panel);
  box-shadow: var(--shadow-soft);
}

.contract-mobile-card__footer {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}
```

- [x] **Step 5: Apply the same structural pattern to upstream, downstream, and management list pages**

```vue
<app-data-table>
  <el-table :data="contractList" border highlight-current-row>
    <!-- existing columns preserved -->
  </el-table>
</app-data-table>
```

- [x] **Step 6: Run build verification**

Run: `cd frontend && npm run build`

Expected:
- Build succeeds for all contract list routes

- [x] **Step 7: Commit**

```bash
git add frontend/src/views/contracts/UpstreamList.vue frontend/src/views/contracts/DownstreamList.vue frontend/src/views/contracts/ManagementList.vue frontend/src/styles/index.scss
git commit -m "feat: redesign contract list surfaces"
```

### Task 9: Final Cross-Module Alignment, Manual Verification, And Cleanup

**Files:**
- Modify: `frontend/src/styles/index.scss`
- Modify: `frontend/src/styles/tokens.scss`
- Modify: `frontend/src/views/system/SystemManagement.vue`
- Modify: `frontend/src/views/audit/AuditLog.vue`
- Modify: `frontend/src/views/expenses/ExpenseList.vue`
- Modify: `frontend/src/views/expenses/OrdinaryExpenseList.vue`
- Modify: `frontend/src/views/expenses/ZeroHourLaborList.vue`

- [x] **Step 1: Sweep secondary modules for token adoption and hard-coded color removal**

```scss
.text-gray {
  color: var(--text-muted) !important;
}

.page-surface {
  background: var(--surface-panel);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}
```

- [x] **Step 2: Replace the most visible remaining hard-coded button and card styles in audit, expense, and system pages**

```vue
<app-page-header
  title="系统管理"
  description="统一管理系统配置、通知和权限设置"
/>
```

- [x] **Step 3: Run the full frontend verification suite**

Run:
- `cd frontend && npm run test`
- `cd frontend && npm run build`

Expected:
- All Vitest suites pass
- Production build succeeds

- [x] **Step 4: Run manual verification in the browser**

Checklist:
- Desktop `/` shows bottom-left sidebar user card and top-right notification center
- Desktop `/reports` uses unified buttons, cards, filters, and responsive export cards
- Desktop `/contracts/upstream` uses unified filters and table styling
- Mobile width `390x844` shows drawer-bottom user card, top-right notifications, stacked dashboard cards, readable charts, and no text overlap
- Theme toggle persists between reloads and correctly recolors charts and page chrome

- [x] **Step 5: Commit**

```bash
git add frontend/src/styles/index.scss frontend/src/styles/tokens.scss frontend/src/views/system/SystemManagement.vue frontend/src/views/audit/AuditLog.vue frontend/src/views/expenses/ExpenseList.vue frontend/src/views/expenses/OrdinaryExpenseList.vue frontend/src/views/expenses/ZeroHourLaborList.vue
git commit -m "feat: complete minimalist saas redesign alignment"
```

---

## Self-Review

### Spec coverage
- Theme system: covered by Task 1 and Task 9.
- Sidebar-bottom user card and top-right notifications: covered by Task 3.
- Full notification center with dedicated page: covered by Task 2 and Task 3.
- Unified buttons/cards/forms/tables: covered by Task 4 and Task 9.
- Dashboard redesign: covered by Task 6.
- Reports redesign: covered by Task 7.
- Contract list redesign: covered by Task 8.
- Responsive behavior and mobile drawer behavior: covered by Task 3, Task 6, Task 7, and Task 8.
- Chart readability and no label overlap: covered by Task 5 and Task 6.

No spec requirements are currently uncovered.

### Placeholder scan
- Removed generic “TODO” language.
- Each task lists exact files and concrete commands.
- Code-change steps contain concrete snippets rather than abstract instructions.

### Type consistency
- Theme state uses `useUiStore` consistently.
- Notification aggregation centers on `buildNotifications`.
- Chart helpers use `createBarChartOption` and `createPieChartOption` consistently across tasks.
