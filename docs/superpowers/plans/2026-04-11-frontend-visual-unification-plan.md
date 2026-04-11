# Frontend Visual Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify the entire frontend, including desktop and mobile surfaces plus chart rendering, around a cleaner shadcn/ui-inspired visual system with stronger readability, consistent component styling, and zero chart label overlap.

**Architecture:** The work should be executed as a layered frontend refactor instead of isolated page polishing. First stabilize tokens, theme semantics, and reusable display primitives; then migrate high-traffic shell and page surfaces to the new primitives; then rebuild all chart option factories and chart containers so typography, spacing, legends, tooltips, and collision handling are driven by one shared contract. The plan intentionally preserves the existing `Vue 3 + Element Plus + Vant + ECharts` stack while allowing a limited expansion of in-repo display primitives that behave more like self-owned shadcn-style components.

**Tech Stack:** Vue 3, Pinia, Element Plus, Vant, ECharts, SCSS design tokens, Tailwind utility classes, Vitest

---

## Context Summary

This plan is based on:

- Full `frontend/` codebase review
- The audit memo at `/Users/palmtom/Desktop/前端审核`
- The chart refactor memo at `/Users/palmtom/Desktop/图表改造`
- Current project constraints confirmed by the user:
  - full-site scope, not dashboard-only
  - desktop and mobile included in one round
  - light and dark themes both included
  - allowed to introduce more shadcn-like in-repo base display components

## Recommended Approach

### Option A: Dashboard-First Cosmetic Refresh

- Rework only `Dashboard.vue`, `home/Overview.vue`, `home/Business.vue`, and chart helpers.
- Lowest immediate cost.
- Does not solve system-wide shell inconsistency, table density inconsistency, or mobile divergence.
- Not recommended because the visual gap would remain obvious in contract, report, and system pages.

### Option B: Full Visual System Unification in Layers

- Phase 1: tokens, theme contract, shell, cards, filters, tables, buttons, tabs
- Phase 2: migrate all desktop pages to shared surface language
- Phase 3: migrate mobile pages to the same language
- Phase 4: rebuild chart option system and page-level chart compositions
- Best balance of consistency, risk control, and maintainability
- Recommended

### Option C: Component Library Replacement Push

- Try to aggressively replace large parts of Element Plus presentation with new bespoke primitives immediately.
- Highest future purity, but too disruptive for this codebase because page count is large and current business forms/tables still rely heavily on Element Plus semantics.
- Not recommended in one pass.

## Final Recommendation

Adopt **Option B**. Keep Element Plus and Vant as the underlying interaction stack, but narrow their visible styling range through shared tokens and a new in-repo display layer. This matches the current codebase better than a full replacement while still achieving the shadcn/ui visual direction.

---

## Design Targets

### Visual Direction

- Use a restrained, neutral, admin-workspace style inspired by `ui.shadcn.com`
- Reduce decorative gradients, glossy highlights, pseudo-element gleams, and oversized radii
- Favor `rounded-lg` / `rounded-xl` equivalent rhythm, subtle borders, low-elevation shadows, and strong content hierarchy
- Replace “panel as decoration” with “panel as quiet container”

### Typography and Readability

- Establish one clear type scale for:
  - page titles
  - section titles
  - metric values
  - labels and helper text
  - table headers
  - chart labels / legends / tooltip text
- Reduce light-gray-on-gray text combinations
- Ensure dense enterprise tables remain readable at realistic widths

### Chart Quality

- No overlapping labels in pie, donut, bar, horizontal rank, or trend charts
- Tooltips and legends must share one theme contract
- Chart fonts, axis spacing, grid margins, and truncation logic must be standardized
- Mobile chart readability must be treated as first-class, not desktop shrinkage

### Theme Consistency

- Light and dark themes must both use the same semantic token map
- Dark mode should not be a decorative inversion; it should preserve contrast and hierarchy
- Component states like hover, active, selected, muted, and disabled should come from shared semantics

---

## Scope Map

### Foundational Style Files

- `frontend/src/styles/tokens.scss`
- `frontend/src/styles/index.scss`
- `frontend/src/styles/variables.scss`
- `frontend/src/assets/main.scss`

### Shell and Layout

- `frontend/src/views/Layout.vue`
- `frontend/src/views/mobile/MobileLayout.vue`
- `frontend/src/components/layout/AppTopbarActions.vue`
- `frontend/src/components/layout/SidebarUserCard.vue`

### Core Display Primitives

- `frontend/src/components/ui/AppMetricCard.vue`
- `frontend/src/components/ui/AppSectionCard.vue`
- `frontend/src/components/ui/AppWorkspacePanel.vue`
- `frontend/src/components/ui/AppFilterBar.vue`
- `frontend/src/components/ui/AppDataTable.vue`
- `frontend/src/components/ui/AppPageHeader.vue`
- `frontend/src/components/ui/AppEmptyState.vue`
- `frontend/src/components/ui/AppRangeField.vue`
- optional additions:
  - `frontend/src/components/ui/AppSurfaceCard.vue`
  - `frontend/src/components/ui/AppStatList.vue`
  - `frontend/src/components/ui/AppToolbarGroup.vue`
  - `frontend/src/components/ui/AppChartPanel.vue`

### Chart System

- `frontend/src/utils/chartTheme.js`
- `frontend/src/utils/chartOptions.js`
- `frontend/src/utils/dashboardRanking.js`
- `frontend/src/utils/echarts.js`

### Dashboard and Reports

- `frontend/src/views/Dashboard.vue`
- `frontend/src/views/home/Overview.vue`
- `frontend/src/views/home/Business.vue`
- `frontend/src/views/reports/ReportDashboard.vue`

### Contract and Business Pages

- `frontend/src/views/contracts/UpstreamList.vue`
- `frontend/src/views/contracts/DownstreamList.vue`
- `frontend/src/views/contracts/ManagementList.vue`
- `frontend/src/views/contracts/UpstreamDetail.vue`
- `frontend/src/views/contracts/DownstreamDetail.vue`
- `frontend/src/views/contracts/ManagementDetail.vue`
- `frontend/src/views/expenses/ExpenseList.vue`
- `frontend/src/views/expenses/OrdinaryExpenseList.vue`
- `frontend/src/views/expenses/ZeroHourLaborList.vue`
- `frontend/src/views/system/SystemManagement.vue`
- `frontend/src/views/system/SystemSettings.vue`
- `frontend/src/views/users/UserManagement.vue`
- `frontend/src/views/audit/AuditLog.vue`
- `frontend/src/views/notifications/NotificationCenter.vue`
- `frontend/src/views/Login.vue`

### Mobile Pages

- `frontend/src/views/mobile/ContractListMobile.vue`
- `frontend/src/views/mobile/ExpenseListMobile.vue`
- `frontend/src/views/mobile/MobileLayout.vue`

---

## Problem Inventory

### Style-System Problems

- `tokens.scss` currently contains too many decorative surface variants and gradient-heavy semantic tokens
- `index.scss` hardcodes multiple Element Plus values that are only partially aligned with `--radius`
- SCSS-heavy local styling coexists with Tailwind utility classes without a clear boundary
- shell, cards, filters, tables, and mobile surfaces do not share a disciplined spacing or radius system

### Layout and Component Problems

- `Layout.vue` sidebar and topbar still use visual effects that feel heavier than the target style
- `AppMetricCard.vue` still uses large radius, top highlight rails, and elevated decorative treatment
- `AppSectionCard.vue` and `AppWorkspacePanel.vue` overlap in responsibility and styling
- `AppFilterBar.vue` contains page-specific layout assumptions that are hard to maintain globally
- `AppDataTable.vue` is visually cleaner than raw tables, but still needs tighter header, border, density, and empty-state consistency

### Chart Problems

- chart utilities only partially encode readability rules
- `createPieChartOption()` still renders outside labels and label lines, which are the main source of overlap risk
- `Overview.vue` and `Business.vue` still contain hand-built chart options that bypass shared standards
- rank charts truncate labels, but axis width, legend rhythm, and tooltip surfaces are still inconsistent
- mobile chart surfaces are not built from a dedicated responsive chart container pattern

### Page-Level Problems

- dashboard pages are visually ahead of some legacy pages, but the whole site still looks mixed-version
- contract list pages, report dashboard, and system pages still show different card, tabs, filters, and spacing language
- mobile pages use a noticeably different radius, panel, and chrome language from desktop pages
- login and system pages do not yet clearly participate in the same design system

---

## Implementation Strategy

### Phase 1: Define the Unified Visual System

Objective:
- Normalize the visual primitives before touching many pages

Planned changes:
- simplify token surface model
- reduce redundant gradient variables
- align all radius values around a small semantic scale
- define one consistent shadow ladder
- establish shared semantic text colors for headings, labels, helper text, and chart text
- tighten Element Plus overrides to token-driven values only
- define a reusable chart token contract in `chartTheme.js`

Acceptance criteria:
- light and dark themes use the same semantic structure
- no component should need custom one-off radii like `22px` or `24px`
- page background and surface backgrounds feel related, not independently designed

### Phase 2: Rebuild Shared Display Primitives

Objective:
- Move visual consistency into a small set of trusted base components

Planned changes:
- refactor `AppMetricCard`, `AppSectionCard`, `AppWorkspacePanel`, `AppFilterBar`, `AppDataTable`
- add optional new wrappers for chart panels, stat groups, and toolbar composition
- remove pseudo-element highlight bars and heavy gleam effects
- standardize content padding, header layout, action alignment, and responsive wrapping

Acceptance criteria:
- base cards and work panels look like one family
- filters and actions align consistently across desktop widths
- page authors can assemble most admin surfaces without adding new local decoration CSS

### Phase 3: Unify Shell and Navigation

Objective:
- Make desktop and mobile shells feel like the same product

Planned changes:
- simplify sidebar active, hover, and background states in `Layout.vue`
- standardize header spacing, icon buttons, and shell framing
- align `MobileLayout.vue` radius, border, topbar, tabbar, and drawer treatment with the same token system
- reduce visual noise in top-level chrome so business content has priority

Acceptance criteria:
- desktop and mobile share one clear shell language
- primary navigation states are readable in both themes
- user/profile chrome does not visually overpower the content area

### Phase 4: Rebuild the Chart System

Objective:
- Eliminate label collisions and enforce chart readability across all pages

Planned changes:
- expand `chartTheme.js` so charts read full semantic tokens:
  - axis text
  - muted text
  - grid line
  - panel background
  - tooltip background
  - tooltip border
  - series palette
- rewrite `chartOptions.js`:
  - bar charts with stronger margin budgeting, axis label truncation, and no decorative clutter
  - pie / donut charts defaulting to center emphasis + legend-driven reading, not risky outside label layouts
- rewrite `dashboardRanking.js`:
  - shared horizontal rank layout budget
  - stronger y-axis label handling
  - consistent data formatting
- extract page-level custom chart options from `Overview.vue` and `Business.vue` into shared builders where possible
- add mobile-specific chart height and label strategies

Acceptance criteria:
- no chart on desktop or mobile shows overlapping labels
- tooltip, legend, and axis typography are visually consistent
- `Overview.vue` and `Business.vue` no longer handcraft divergent chart styles unless business-specific structure requires it

### Phase 5: Migrate All Desktop Business Pages

Objective:
- Remove mixed-generation UI patterns across contracts, expenses, reports, system, and audit pages

Planned changes:
- convert page shells to shared surface hierarchy
- align tabs, page headers, filter zones, data table wrappers, and action bars
- reduce per-page decorative SCSS where a shared primitive already exists
- improve list/detail page rhythm, empty states, and dense table readability
- ensure report pages visually match dashboard pages rather than legacy CRUD pages

Acceptance criteria:
- moving between dashboard, contracts, expenses, reports, and system pages feels visually continuous
- table-heavy pages are easier to scan
- all primary pages look like one release, not an accumulation of styles

### Phase 6: Migrate All Mobile Pages

Objective:
- Bring mobile pages to the same design system, not a separate visual dialect

Planned changes:
- align mobile cards, topbar, section surfaces, and spacing
- ensure chart containers on mobile preserve readable text, legend placement, and scrolling behavior
- standardize touch targets and button hierarchy
- ensure desktop-to-mobile translation feels like adaptation, not redesign

Acceptance criteria:
- mobile pages inherit the same visual identity as desktop pages
- touch interactions remain clear and uncluttered
- chart readability remains intact on narrow widths

### Phase 7: QA, Regression Tests, and Visual Acceptance

Objective:
- Lock in the new system and prevent visual backsliding

Planned changes:
- add or update targeted component and page tests where structural expectations changed
- add focused tests for chart option generation where overlap-prevention logic is encoded
- run desktop and mobile viewport checks
- run theme verification for both light and dark
- add a visual acceptance checklist for major routes

Acceptance criteria:
- no broken layout in primary desktop or mobile routes
- chart option helpers are covered by tests for the most failure-prone cases
- light/dark theme regressions are visible early

---

## Chart-Specific Revision Rules

These are mandatory plan constraints for the chart work:

- Pie and donut charts should not rely on dense external labels when category count is high
- Legend blocks must support scroll or truncation before overlap occurs
- Axis label width, rotation, and truncation should be driven by container-aware defaults
- Chart cards must reserve explicit vertical space for titles, legends, and plot area
- Tooltip design must use the same border, radius, and typography language as the rest of the app
- Grid lines should support reading values without dominating the visual field
- Horizontal ranking charts should reserve enough y-axis space for Chinese labels
- Mobile chart layouts should prefer fewer simultaneously visible labels over unreadable density

---

## Verification Plan

### Automated Checks

- run existing Vitest suites for affected UI primitives and pages
- add tests for:
  - unified card class structure
  - shell layout structural expectations
  - chart option generation defaults
  - pie / donut label strategy
  - responsive chart sizing helpers if introduced
- run `npm --prefix frontend run build`

### Manual Visual QA

Desktop:
- dashboard overview
- dashboard business
- upstream/downstream/management lists and details
- expenses pages
- report dashboard
- system management
- audit log
- login

Mobile:
- mobile shell
- contract list mobile
- expense list mobile
- report-related mobile routes if exposed

Theme QA:
- light theme full pass
- dark theme full pass

Chart QA:
- long Chinese labels
- many-category donut / pie data
- low-value and zero-value datasets
- narrow-width mobile charts
- legend-heavy datasets

---

## Risk Management

### Primary Risks

- wide-scope visual change causing inconsistent in-between states
- overcorrecting toward custom primitives and breaking Element Plus-based business forms
- chart readability regression on mobile
- dark theme regressions if token simplification is only tested in light mode

### Mitigations

- land the work in layers, not random page edits
- prioritize base primitives before page rewrites
- keep form behavior on Element Plus; change presentation contract, not field semantics
- test chart helpers independently from pages
- verify every phase in both themes and both viewport families

---

## Execution Order

1. Foundation tokens and global overrides
2. Shared primitives
3. Shell and navigation
4. Chart system
5. Desktop pages
6. Mobile pages
7. QA and regression locking

This order is required. If page migration starts before tokens and shared primitives stabilize, the refactor will generate duplicated local fixes and the final style drift will remain.

---

## Deliverables

- Unified token and theme contract for light and dark themes
- Refactored shared display primitives
- Desktop shell and mobile shell aligned to one visual system
- Chart option system with no label overlap by default
- Dashboard, reports, contracts, expenses, system, audit, and login pages visually unified
- Mobile views visually aligned with desktop
- Verification evidence and updated tests

---

## Out of Scope

- Backend API changes
- Business logic changes
- Replacing Element Plus or Vant as the application stack
- Rebuilding all forms into a different component framework
- Marketing-site style visuals or highly animated showcase effects

---

## Approval Gate

This plan is intended to be approved before implementation begins. After approval, the next step should be writing a task-by-task execution plan and then implementing in a dedicated worktree.
