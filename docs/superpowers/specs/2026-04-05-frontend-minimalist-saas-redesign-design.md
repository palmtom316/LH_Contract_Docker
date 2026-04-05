# Frontend Minimalist SaaS Redesign Design

Date: 2026-04-05
Project: LH Contract Management System
Scope: Global shell, theme system, shared UI language, dashboard, reports, contract list surfaces, notification center, responsive behavior
Status: Approved for design, pending implementation plan

## 1. Goals

This redesign establishes a consistent minimalist SaaS visual system across the frontend while preserving current business flows and Vue + Element Plus foundations.

Primary goals:
- Move login user information from the top-right area into the lower section of the left sidebar.
- Replace the top-right user area with a complete notification center entry.
- Introduce two unified themes: default light theme and manual dark theme.
- Standardize buttons, cards, tables, filters, pagination, forms, and chart presentation across modules.
- Use color-blind-friendly palettes and maintain strong text readability.
- Improve desktop and mobile adaptation across shell, workspaces, and charts.
- Raise visual quality through spacing, depth, shadows, and tactile interaction feedback without clutter.

Non-goals:
- No frontend framework migration.
- No replacement of Element Plus as the base component library.
- No full rewrite of all feature modules in one pass.
- No brand-heavy or decorative marketing-style visuals.

## 2. Constraints And Existing Context

The current frontend uses Vue 3, Vite, Element Plus, Pinia, Vue Router, and ECharts.

Relevant files and current responsibilities:
- [Layout.vue](/Users/palmtom/Projects/LH_Contract_Docker/frontend/src/views/Layout.vue): desktop shell, sidebar, navbar, user area.
- [MobileLayout.vue](/Users/palmtom/Projects/LH_Contract_Docker/frontend/src/views/mobile/MobileLayout.vue): mobile shell.
- [Overview.vue](/Users/palmtom/Projects/LH_Contract_Docker/frontend/src/views/home/Overview.vue): dashboard cards and charts.
- [ReportDashboard.vue](/Users/palmtom/Projects/LH_Contract_Docker/frontend/src/views/reports/ReportDashboard.vue): reporting workspace and chart-heavy views.
- [tokens.scss](/Users/palmtom/Projects/LH_Contract_Docker/frontend/src/styles/tokens.scss): starting point for theme tokens.
- [index.scss](/Users/palmtom/Projects/LH_Contract_Docker/frontend/src/styles/index.scss): global styles and overrides.

Implementation must work within the current route structure and preserve existing business permissions.

## 3. Recommended Approach

Use a system-first redesign rather than page-by-page visual patching.

This means:
- Build a semantic token layer for light and dark themes first.
- Refactor the application shell second.
- Normalize shared interaction patterns third.
- Rework dashboard, reports, and contract list pages against the new system.
- Pull remaining modules onto the new design language by using shared wrappers and utility classes, not isolated per-page hacks.

This approach balances visual improvement, maintainability, and delivery risk.

## 4. Visual Direction

Design direction: minimalist executive SaaS.

Characteristics:
- Clean negative space and clear hierarchy.
- Low-noise surfaces with depth from layered shadows and subtle borders.
- Precise typography and restrained motion.
- Sharp but soft-feeling cards using medium radii and clear elevation.
- A dense-enough workspace for business users without feeling cramped.

Light theme:
- Backgrounds: fog white and cool neutral surface layers.
- Text: graphite and slate neutrals.
- Accent: blue-cyan primary for key actions and focus states.
- Supporting semantic colors: amber for warning, magenta-rose for critical signals, teal for positive states.

Dark theme:
- Backgrounds: graphite, charcoal, and elevated panel surfaces.
- Text: soft white and muted cool gray.
- Accent: the same blue-cyan family with tuned luminance for contrast.
- Borders and dividers become low-contrast luminous neutrals instead of pure black lines.

Accessibility requirements:
- Avoid red-vs-green-only distinctions.
- Pair color meaning with iconography, labels, and badges.
- Preserve accessible contrast in both themes.
- Keep focus rings visible and consistent.

## 5. Information Architecture And Shell Changes

### 5.1 Desktop Shell

The desktop shell will be reorganized into three stable zones:
- Left: navigation sidebar.
- Center: main page workspace.
- Top-right: system actions and notification entry.

Sidebar changes:
- Keep main navigation in the upper and middle sections.
- Add a fixed bottom user card inside the sidebar.
- User card contains avatar, username, role, online/current status hint, and quick actions such as profile/settings/logout.

Top bar changes:
- Remove the current login user information block from the top-right.
- Add theme toggle.
- Add notification bell with unread indicator.
- Keep the current page title and any route-defined contextual actions in a consistent action slot.

### 5.2 Mobile Shell

Mobile layout will map the same hierarchy instead of inventing a separate visual language:
- Sidebar becomes a slide-in drawer.
- The user card stays at the bottom of that drawer.
- Top bar keeps page title, notification entry, and theme toggle.
- Primary content uses one-column stacked modules with tighter but touch-safe spacing.

## 6. Notification Center

The notification center will replace the current top-right user area and will be implemented as a complete workflow.

### 6.1 Entry

Top-right bell button includes:
- unread badge
- hover/focus/active feedback
- dropdown entry point

### 6.2 Dropdown

The dropdown shows:
- grouped notifications
- unread emphasis
- timestamps
- type icons
- “view all” action

### 6.3 Notification Page

A dedicated notification route/page provides:
- all notifications
- unread-only filter
- type/category filters
- mark-as-read actions
- batch status actions where practical

### 6.4 Data Sources

Instead of a fake isolated notification model, the first implementation derives notifications from existing system data:
- audit log events
- contract expiry reminders
- payment or receivable milestone reminders
- system or configuration warnings
- report-related status reminders where available

Aggregation logic will be introduced in the frontend for the first phase. If existing APIs prove insufficient during implementation, the follow-up plan may add backend aggregation support as a separate extension task rather than blocking the redesign.

## 7. Theme System

Theme strategy:
- default theme is light
- user can manually switch to dark
- preference persists locally

Implementation structure:
- semantic CSS variables for background, surface, text, border, shadow, primary, status, focus, and chart tokens
- theme state managed centrally in a small store or composable
- `data-theme="light|dark"` applied at the application root
- Element Plus variables bridged to internal semantic tokens to minimize one-off overrides

Theme tokens must cover:
- backgrounds
- text hierarchy
- icon colors
- borders and dividers
- shadows
- button variants
- tags, badges, alerts
- chart palette

## 8. Shared UI Normalization

The redesign will define consistent shared patterns for all major business modules.

### 8.1 Buttons

All modules will use a normalized button system:
- unified heights by density level
- consistent radius
- consistent padding and icon spacing
- consistent hover, active, disabled, loading, and focus states

Button family:
- primary
- secondary
- ghost
- danger
- text

### 8.2 Cards And Panels

Cards become the standard information container:
- shared header spacing
- shared body padding
- shared elevation levels
- sticky action regions for toolbars on pages that contain persistent filter or action bars

### 8.3 Forms And Filters

All forms and filter bars must align to the same rhythm:
- unified field heights
- unified label style
- consistent inline and stacked form behavior
- consistent collapse behavior on mobile

### 8.4 Tables And Pagination

Business-heavy modules rely on tables, so they must be consistent:
- sticky or visually anchored headers where appropriate
- uniform row density and zebra/hover strategy
- standardized empty states and loading states
- mobile fallback through stacked cards or simplified columns where necessary

## 9. Page-Level Coverage

The implementation phase will prioritize these areas:

### 9.1 Global Shell
- desktop layout
- mobile layout
- sidebar
- top bar
- user card
- theme toggle
- notification entry

### 9.2 Dashboard
- summary cards
- trend charts
- category and company pie charts
- mobile tab/stack behavior

### 9.3 Reports Workspace
- chart card styling
- page header structure
- export area styling
- mobile chart stacking and readable controls

### 9.4 Contract Lists
- filters
- toolbars
- tables
- bulk actions
- mobile card rendering

Remaining modules will adopt the new tokens and shared visual primitives so the system looks unified even before every page receives a full bespoke pass.

## 10. Charts And Data Visualization Rules

Chart readability is a hard requirement.

All chart implementations must follow these rules:
- Titles, legends, axes, and series labels must never overlap.
- Prefer external labels and legend summaries over dense in-chart text.
- Use `grid.containLabel: true` where applicable.
- Reserve padding for titles and legends explicitly.
- Reduce label density on mobile.
- Long labels must truncate visually and expose full content through tooltip.
- Pie chart labels should use outside layout with collision avoidance; if still crowded, move detail into legends/tooltips.
- Tooltip styles must be theme-aware and high-contrast.
- Series colors must remain distinguishable for color-blind users.
- Mobile charts should prefer vertical stacking, tab switching, or simplified legend modes over squeezing multiple plots into one viewport.

Reusable chart styling will be centralized so dashboard and reports do not drift apart.

## 11. Responsive Strategy

This redesign is not desktop-only reskinning.

Responsive strategy:
- Desktop: full sidebar, multi-column dashboard and workspace layouts.
- Tablet: reduced columns, compressed toolbars, fewer side-by-side charts.
- Mobile: one-column stack, slide-in navigation, drawer-bottom user card, simplified chart density, touch-safe controls.

Responsive requirements:
- touch targets at least 44px where interaction is primary
- tables degrade to cards or curated columns
- toolbar actions collapse intelligently
- page headers wrap cleanly without collisions
- filters support stacked layouts

## 12. Interaction And Motion

Motion should be restrained and premium, not playful.

Allowed patterns:
- subtle hover lift on cards
- clear button press feedback
- smooth drawer and dropdown transitions
- theme transition that avoids flash and preserves legibility
- notification unread/read transitions with minimal emphasis

Disallowed patterns:
- excessive parallax
- attention-grabbing loops
- decorative animation that competes with data density

## 13. Technical Architecture

Implementation should introduce structure that reduces future visual drift.

Recommended additions:
- shared theme composable/store
- reusable shell subcomponents for sidebar user card and notification entry
- shared utility classes for page sections, toolbars, and card headers
- shared chart option helpers for spacing, typography, and palette defaults
- shared responsive helpers where current logic is duplicated

The design system should live primarily in styles/tokens and lightweight shared wrappers, not a large custom component framework.

## 14. Testing And Verification Expectations

Verification must include:
- desktop checks for main shell, dashboard, reports, and contract list pages
- mobile checks for drawer, user card, notification entry, chart readability, and tables/cards
- theme toggle validation in both light and dark modes
- chart checks for label collision and readability
- visual regression review for shared button, card, table, and form behavior

Preferred verification tools:
- local dev run with manual route inspection
- browser/mobile emulation
- focused visual comparison screenshots when useful

## 15. Risks And Mitigations

Risk: Element Plus defaults may fight the new visual system.
Mitigation: bridge through semantic tokens and scoped overrides instead of page-local hard-coded CSS.

Risk: Chart pages may remain inconsistent if each page keeps separate option logic.
Mitigation: extract shared ECharts styling helpers early.

Risk: Mobile complexity increases if desktop table layouts are forced into narrow screens.
Mitigation: treat mobile as a first-class layout with intentional card/list fallbacks.

Risk: Notification center may become shallow if data sources are weak.
Mitigation: derive from existing audit, reminder, and system event sources first. If a gap remains after implementation, capture it as a separate backend/data follow-up rather than weakening the shell redesign.

## 16. Implementation Phasing

Implementation will follow this order:
1. Theme tokens and root theme switching
2. Layout shell refactor
3. Shared button/card/form/table normalization
4. Notification center entry and dedicated page
5. Dashboard redesign
6. Reports redesign
7. Contract list redesign
8. Remaining modules aligned to the new shared system

This keeps the highest-visibility areas consistent first while limiting regressions.

## 17. Success Criteria

The redesign is successful when:
- the app clearly reads as one coherent product, not mixed module styles
- the left-bottom user card replaces the old top-right user area across shell states
- the top-right notification center is functional and visible on desktop and mobile
- users can switch between light and dark themes manually
- buttons, cards, forms, tables, and filters feel uniform across modules
- charts remain readable without text collisions in desktop and mobile layouts
- the overall interface feels simpler, more premium, and more business-ready
