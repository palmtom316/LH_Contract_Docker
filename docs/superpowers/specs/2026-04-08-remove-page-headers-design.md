# Remove Top Page Headers

## Summary

Remove the top `AppPageHeader` title band from the main desktop page views so the content starts directly at the functional workspace surface instead of leaving a large empty gap above the page tabs, filters, tables, and detail sections.

This change is intentionally structural and narrow:

- remove page-level `AppPageHeader` usage from the affected views
- remove header-only wrapper classes or spacing rules that become dead after the header is removed
- keep actions, tabs, filters, cards, tables, and detail content intact

## Goals

- Eliminate the large blank area above page content
- Make pages open directly into the working area
- Apply the same treatment consistently across dashboard, contract, report, system, audit, notification, and expense views

## Non-Goals

- Redesigning page internals
- Changing routes, permissions, or data flow
- Replacing `AppPageHeader` globally
- Reworking mobile-specific layouts unless they share the same desktop view file naturally

## Scope

Affected views:

- `frontend/src/views/Dashboard.vue`
- `frontend/src/views/reports/ReportDashboard.vue`
- `frontend/src/views/expenses/ExpenseList.vue`
- `frontend/src/views/system/SystemManagement.vue`
- `frontend/src/views/system/SystemSettings.vue`
- `frontend/src/views/contracts/UpstreamList.vue`
- `frontend/src/views/contracts/DownstreamList.vue`
- `frontend/src/views/contracts/ManagementList.vue`
- `frontend/src/views/contracts/UpstreamDetail.vue`
- `frontend/src/views/contracts/DownstreamDetail.vue`
- `frontend/src/views/contracts/ManagementDetail.vue`
- `frontend/src/views/notifications/NotificationCenter.vue`
- `frontend/src/views/audit/AuditLog.vue`

Not in scope:

- `frontend/src/components/ui/AppPageHeader.vue` component removal
- sidebar menu labels such as `首页概览`
- internal section headers inside cards and panels

## Approach

### Recommended approach

Remove `AppPageHeader` usage from each affected page directly.

Why this approach:

- lowest risk to unrelated pages or future reuse
- no hidden empty DOM or collapsed borders left behind
- easiest to verify per-page

### Rejected alternatives

#### 1. Change `AppPageHeader` globally to render nothing

Rejected because:

- it changes behavior for every existing caller
- it removes the option to keep headers on selected pages later

#### 2. Collapse the header with CSS only

Rejected because:

- it leaves dead markup in place
- spacing and border artifacts are more likely

## Page-Level Design

For every affected page:

- remove the top `AppPageHeader` import
- remove the top `AppPageHeader` node from the template
- remove header-only classes such as `*-page-header`, `*-dashboard-header`, or similar if they become unused
- keep existing page shell, workspace panels, tabs, filters, detail forms, action buttons, and cards unchanged

Expected visual outcome:

- page content starts near the top of the viewport
- the first visible block is usually the page’s workspace panel, tabs, or filter card
- no separate title strip remains above that content

## Testing

Add source-level regression checks that the affected views no longer import or render `AppPageHeader`.

Verification focus:

- dashboard page no longer renders `首页概览` header band
- contract list pages no longer render top title bands
- contract detail pages no longer render top title bands
- utility pages such as reports, system, notifications, audit, and expenses no longer render top title bands
- no business actions disappear with the header removal

## Risks and Mitigations

- Risk: some page-level action buttons may currently live inside the header slot
  - Mitigation: verify each affected page before deletion and preserve actions in-place if any exist

- Risk: removing the header may expose too little top spacing on some pages
  - Mitigation: keep the page shell and panel spacing; only remove header-specific gaps

## Implementation Boundary

This is one focused frontend cleanup and does not need decomposition:

- one shared pattern removal
- one finite set of page files
- no backend changes

## Approval Baseline

Approved direction:

- use direct page-level removal
- remove the top title area together with its blank space
- apply the same treatment to homepage, contract pages, and the other pages using the same top header pattern
