# 全站前端精修 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 以共享设计系统为起点，对桌面端、移动端、登录页和首页看板完成一轮可验证的全站前端精修，并让改动自然辐射到大部分业务页面。

**Architecture:** 先通过测试锁定共享视觉契约，再收紧设计令牌、全局样式和应用外壳，随后统一共享基础组件与首页高频页面。实施顺序遵循“测试先行 -> 共享层 -> 页面层 -> 回归验证”，避免页面级样式分叉重新出现。

**Tech Stack:** Vue 3, Vite, Vitest, Element Plus, Vant, SCSS, ECharts

---

## 文件结构与职责

- `frontend/src/styles/tokens.scss`
  - 维护全站颜色、圆角、阴影、间距和工作台语义变量
- `frontend/src/styles/index.scss`
  - 统一 Element Plus、Vant 与全站基础排版、按钮、面板、表格的视觉契约
- `frontend/src/views/Layout.vue`
  - 桌面端外壳、侧边栏、顶栏与主工作区容器
- `frontend/src/views/mobile/MobileLayout.vue`
  - 移动端外壳、顶部栏、抽屉与底部导航框架
- `frontend/src/views/Login.vue`
  - 登录入口的同系统视觉语言
- `frontend/src/components/layout/AppTopbarActions.vue`
  - 顶栏操作区统一视觉壳层
- `frontend/src/components/layout/SidebarUserCard.vue`
  - 侧栏用户卡与下拉触发器状态反馈
- `frontend/src/components/ui/AppMetricCard.vue`
  - 指标卡的低噪声信息承载
- `frontend/src/components/ui/AppSectionCard.vue`
  - 分区卡片与头部操作区
- `frontend/src/components/ui/AppWorkspacePanel.vue`
  - 页面工作区共享容器
- `frontend/src/components/ui/AppPageHeader.vue`
  - 页面标题区与操作栏的统一节奏
- `frontend/src/components/ui/AppFilterBar.vue`
  - 高密度筛选区布局、控件和按钮节奏
- `frontend/src/components/ui/AppDataTable.vue`
  - 数据表格外层容器与滚动/表头视觉契约
- `frontend/src/views/Dashboard.vue`
  - 首页页签外壳和工作区节奏
- `frontend/src/views/home/Overview.vue`
  - 概览看板信息层级和图表区组合
- `frontend/src/views/home/Business.vue`
  - 经营看板筛选区、指标区、摘要区和图表区
- `frontend/src/components/ui/__tests__/*.spec.js`
  - 共享基础组件视觉契约测试
- `frontend/src/views/__tests__/*.spec.js`
  - 桌面端、登录页视觉外壳契约测试
- `frontend/src/views/mobile/__tests__/*.spec.js`
  - 移动端视觉外壳契约测试

### Task 1: 锁定共享视觉契约测试

**Files:**
- Modify: `frontend/src/components/ui/__tests__/AppMetricCard.spec.js`
- Modify: `frontend/src/components/ui/__tests__/AppSectionCard.spec.js`
- Modify: `frontend/src/components/ui/__tests__/AppPageHeader.spec.js`
- Modify: `frontend/src/components/ui/__tests__/AppFilterBar.spec.js`
- Modify: `frontend/src/views/__tests__/LayoutWorkspaceVisual.spec.js`
- Modify: `frontend/src/views/__tests__/LoginWorkspace.spec.js`
- Modify: `frontend/src/views/mobile/__tests__/MobileVisualShell.spec.js`

- [ ] **Step 1: 先写失败测试，锁定“专业、温和、非企业灰”的共享视觉规则**

```js
it('uses warmer workspace tokens and calmer panel spacing', () => {
  expect(metricCardSource).toContain('padding: 18px;')
  expect(metricCardSource).toContain('border-radius: calc(var(--radius) + 2px);')
  expect(metricCardSource).toContain('transition: transform 180ms ease')
})
```

```js
it('keeps login and shell surfaces aligned to the refined workspace framing', () => {
  expect(desktopShell).toContain('background: var(--surface-page-gradient);')
  expect(mobileShell).toContain('box-shadow: var(--shadow-frame);')
})
```

- [ ] **Step 2: 运行共享视觉测试，确认先红灯**

Run:

```bash
npm test --prefix frontend -- AppMetricCard.spec.js AppSectionCard.spec.js AppPageHeader.spec.js AppFilterBar.spec.js LayoutWorkspaceVisual.spec.js LoginWorkspace.spec.js MobileVisualShell.spec.js
```

Expected:

```text
FAIL
Expected substring not found in updated visual contract assertions
```

- [ ] **Step 3: 若失败原因不是“缺少新视觉实现”，先修正测试表达**

```js
expect(metricCardSource).not.toContain('22px')
expect(metricCardSource).not.toContain('::before')
```

- [ ] **Step 4: 红灯确认后提交测试基线**

```bash
git add frontend/src/components/ui/__tests__/AppMetricCard.spec.js \
  frontend/src/components/ui/__tests__/AppSectionCard.spec.js \
  frontend/src/components/ui/__tests__/AppPageHeader.spec.js \
  frontend/src/components/ui/__tests__/AppFilterBar.spec.js \
  frontend/src/views/__tests__/LayoutWorkspaceVisual.spec.js \
  frontend/src/views/__tests__/LoginWorkspace.spec.js \
  frontend/src/views/mobile/__tests__/MobileVisualShell.spec.js
git commit -m "test: lock refined workspace visual contracts"
```

### Task 2: 精修设计令牌与全局样式

**Files:**
- Modify: `frontend/src/styles/tokens.scss`
- Modify: `frontend/src/styles/index.scss`
- Test: `frontend/src/styles/__tests__/colorSystem.spec.js`

- [ ] **Step 1: 先写失败测试，锁定更温和的中性色和统一工作台语义**

```js
it('defines warmer neutrals and a stronger workspace surface hierarchy', () => {
  expect(tokensSource).toContain('--background: 32 24% 97%')
  expect(tokensSource).toContain('--surface-panel-muted:')
  expect(tokensSource).toContain('--shadow-frame:')
  expect(tokensSource).toContain('--workspace-control-height: 40px')
})
```

- [ ] **Step 2: 运行颜色系统测试，确认失败**

Run:

```bash
npm test --prefix frontend -- colorSystem.spec.js
```

Expected:

```text
FAIL
Expected '--background: 32 24% 97%' to be present
```

- [ ] **Step 3: 只写最小实现，先把设计令牌收紧**

```scss
:root,
:root[data-theme='light'] {
  --background: 32 24% 97%;
  --card: 36 18% 99%;
  --muted: 36 22% 94%;
  --border: 24 16% 84%;
  --workspace-control-height: 40px;
  --shadow-frame: 0 18px 40px hsl(24 30% 18% / 0.08);
}
```

```scss
body {
  background: var(--surface-page-gradient);
  color: var(--text-primary);
}
```

- [ ] **Step 4: 跑测试转绿，再补充全局控件和表格细节**

Run:

```bash
npm test --prefix frontend -- colorSystem.spec.js
```

Expected:

```text
PASS
```

- [ ] **Step 5: 提交共享令牌与全局样式**

```bash
git add frontend/src/styles/tokens.scss frontend/src/styles/index.scss frontend/src/styles/__tests__/colorSystem.spec.js
git commit -m "feat: refine workspace design tokens and global chrome"
```

### Task 3: 精修桌面端、移动端和登录外壳

**Files:**
- Modify: `frontend/src/views/Layout.vue`
- Modify: `frontend/src/views/mobile/MobileLayout.vue`
- Modify: `frontend/src/views/Login.vue`
- Modify: `frontend/src/components/layout/AppTopbarActions.vue`
- Modify: `frontend/src/components/layout/SidebarUserCard.vue`
- Test: `frontend/src/views/__tests__/LayoutWorkspaceVisual.spec.js`
- Test: `frontend/src/views/__tests__/LoginWorkspace.spec.js`
- Test: `frontend/src/views/mobile/__tests__/MobileVisualShell.spec.js`

- [ ] **Step 1: 先写失败测试，锁定外壳应该更轻、更稳、更一致**

```js
it('uses quieter shell framing instead of glossy accent chrome', () => {
  expect(desktopShell).toContain('background: var(--surface-page-gradient);')
  expect(desktopShell).toContain('box-shadow: var(--shadow-frame);')
  expect(desktopShell).not.toContain('translateX(-18%)')
})
```

```js
it('keeps login panel in the same workspace family', () => {
  expect(loginSource).toContain('background: color-mix(in srgb, hsl(var(--card)) 92%')
  expect(loginSource).toContain('min-height: 40px;')
})
```

- [ ] **Step 2: 跑外壳测试，确认红灯**

Run:

```bash
npm test --prefix frontend -- LayoutWorkspaceVisual.spec.js LoginWorkspace.spec.js MobileVisualShell.spec.js
```

Expected:

```text
FAIL
Expected refined shell framing tokens to be present
```

- [ ] **Step 3: 写最小实现，统一桌面/移动/登录外壳**

```scss
.workspace {
  background: transparent;
}

.app-main__frame,
.mobile-shell__frame,
.login-shell__panel {
  border: 1px solid var(--workspace-panel-border);
  box-shadow: var(--shadow-frame);
}
```

```scss
.topbar-actions {
  border-radius: 999px;
  box-shadow: none;
  backdrop-filter: none;
}
```

- [ ] **Step 4: 跑外壳测试转绿**

Run:

```bash
npm test --prefix frontend -- LayoutWorkspaceVisual.spec.js LoginWorkspace.spec.js MobileVisualShell.spec.js
```

Expected:

```text
PASS
```

- [ ] **Step 5: 提交外壳精修**

```bash
git add frontend/src/views/Layout.vue frontend/src/views/mobile/MobileLayout.vue frontend/src/views/Login.vue frontend/src/components/layout/AppTopbarActions.vue frontend/src/components/layout/SidebarUserCard.vue frontend/src/views/__tests__/LayoutWorkspaceVisual.spec.js frontend/src/views/__tests__/LoginWorkspace.spec.js frontend/src/views/mobile/__tests__/MobileVisualShell.spec.js
git commit -m "feat: refine desktop mobile and login workspace shells"
```

### Task 4: 精修共享基础组件与首页看板

**Files:**
- Modify: `frontend/src/components/ui/AppMetricCard.vue`
- Modify: `frontend/src/components/ui/AppSectionCard.vue`
- Modify: `frontend/src/components/ui/AppWorkspacePanel.vue`
- Modify: `frontend/src/components/ui/AppPageHeader.vue`
- Modify: `frontend/src/components/ui/AppFilterBar.vue`
- Modify: `frontend/src/components/ui/AppDataTable.vue`
- Modify: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/views/home/Overview.vue`
- Modify: `frontend/src/views/home/Business.vue`
- Test: `frontend/src/components/ui/__tests__/AppMetricCard.spec.js`
- Test: `frontend/src/components/ui/__tests__/AppSectionCard.spec.js`
- Test: `frontend/src/components/ui/__tests__/AppPageHeader.spec.js`
- Test: `frontend/src/components/ui/__tests__/AppFilterBar.spec.js`
- Test: `frontend/src/views/__tests__/DashboardWorkspace.spec.js`

- [ ] **Step 1: 先写失败测试，锁定共享组件需要更安静但更有质感**

```js
it('renders metric cards as denser and calmer workspace surfaces', () => {
  expect(metricCardSource).toContain('padding: 18px;')
  expect(metricCardSource).toContain('border-radius: calc(var(--radius) + 2px);')
  expect(metricCardSource).toContain('transform 180ms ease')
})
```

```js
it('keeps dashboard tabs and chart regions inside the refined workspace rhythm', () => {
  expect(dashboardSource).toContain('gap: var(--space-5);')
  expect(dashboardSource).toContain('padding: var(--space-5);')
})
```

- [ ] **Step 2: 跑共享组件和首页测试，确认失败**

Run:

```bash
npm test --prefix frontend -- AppMetricCard.spec.js AppSectionCard.spec.js AppPageHeader.spec.js AppFilterBar.spec.js DashboardWorkspace.spec.js
```

Expected:

```text
FAIL
Expected refined spacing and surface tokens to be present
```

- [ ] **Step 3: 写最小实现，统一组件与首页节奏**

```scss
.app-metric-card,
.app-section-card,
.app-workspace-panel {
  border-radius: calc(var(--radius) + 2px);
}

.app-metric-card:hover {
  transform: translateY(-1px);
}
```

```scss
.dashboard-shell,
.overview-page,
.business-dashboard {
  gap: var(--space-5);
}
```

- [ ] **Step 4: 跑共享组件和首页测试转绿**

Run:

```bash
npm test --prefix frontend -- AppMetricCard.spec.js AppSectionCard.spec.js AppPageHeader.spec.js AppFilterBar.spec.js DashboardWorkspace.spec.js
```

Expected:

```text
PASS
```

- [ ] **Step 5: 提交共享组件与首页改造**

```bash
git add frontend/src/components/ui/AppMetricCard.vue frontend/src/components/ui/AppSectionCard.vue frontend/src/components/ui/AppWorkspacePanel.vue frontend/src/components/ui/AppPageHeader.vue frontend/src/components/ui/AppFilterBar.vue frontend/src/components/ui/AppDataTable.vue frontend/src/views/Dashboard.vue frontend/src/views/home/Overview.vue frontend/src/views/home/Business.vue frontend/src/components/ui/__tests__/AppMetricCard.spec.js frontend/src/components/ui/__tests__/AppSectionCard.spec.js frontend/src/components/ui/__tests__/AppPageHeader.spec.js frontend/src/components/ui/__tests__/AppFilterBar.spec.js frontend/src/views/__tests__/DashboardWorkspace.spec.js
git commit -m "feat: refine shared surfaces and dashboard workspace"
```

### Task 5: 全量回归验证

**Files:**
- Test: `frontend/src/components/ui/__tests__/AppMetricCard.spec.js`
- Test: `frontend/src/components/ui/__tests__/AppSectionCard.spec.js`
- Test: `frontend/src/components/ui/__tests__/AppPageHeader.spec.js`
- Test: `frontend/src/components/ui/__tests__/AppFilterBar.spec.js`
- Test: `frontend/src/views/__tests__/LayoutWorkspaceVisual.spec.js`
- Test: `frontend/src/views/__tests__/LoginWorkspace.spec.js`
- Test: `frontend/src/views/mobile/__tests__/MobileVisualShell.spec.js`
- Test: `frontend/src/views/__tests__/DashboardWorkspace.spec.js`

- [ ] **Step 1: 运行共享精修相关的定向测试**

Run:

```bash
npm test --prefix frontend -- AppMetricCard.spec.js AppSectionCard.spec.js AppPageHeader.spec.js AppFilterBar.spec.js LayoutWorkspaceVisual.spec.js LoginWorkspace.spec.js MobileVisualShell.spec.js DashboardWorkspace.spec.js
```

Expected:

```text
PASS
```

- [ ] **Step 2: 运行前端完整测试集**

Run:

```bash
npm test --prefix frontend
```

Expected:

```text
PASS
Test Files  x passed
Tests       x passed
```

- [ ] **Step 3: 检查变更范围**

Run:

```bash
git status --short
git diff -- frontend/src/styles frontend/src/views frontend/src/components
```

Expected:

```text
Only intended frontend refinement files changed
```

- [ ] **Step 4: 提交最终精修**

```bash
git add frontend/src
git commit -m "feat: complete full frontend refinement pass"
```

## 自检

- 规格覆盖：设计说明里的共享系统、外壳、共享组件、首页高频页面、微交互和验证环节都已映射到任务
- 占位符扫描：计划中未使用 TBD / TODO / “稍后实现”
- 类型与命名一致：围绕现有 `App*` 组件、`Layout.vue`、`MobileLayout.vue`、`Login.vue`、`Dashboard.vue` 等真实文件展开

## 执行方式

计划已保存到 `docs/superpowers/plans/2026-04-11-full-frontend-refinement-implementation-plan.md`。你已经明确要求开始实施，因此本次默认在当前会话中直接内联执行。
