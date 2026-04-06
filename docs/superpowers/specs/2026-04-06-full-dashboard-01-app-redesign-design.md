# Full Dashboard-01 App Redesign

## Summary

Rebuild the full frontend experience so the application reads as one coherent `shadcn/ui` `new-york-v4/dashboard-01` inspired product rather than one redesigned upstream page inside an older interface.

This redesign extends the existing upstream workspace work to all major page families:

- Desktop shell and primary business pages
- Desktop list pages
- Desktop detail pages
- Utility pages such as dashboard, reports, notifications, system, and audit
- Mobile routes under `/m`
- Login page

The redesign keeps the current Vue 3 + Element Plus + SCSS stack, existing routes, existing permissions, and all current backend-driven behavior.

## Goals

- Make the entire product feel visually unified under one workspace design language
- Reuse shared primitives so list pages, detail pages, utility pages, mobile pages, and auth pages are not styled independently
- Preserve all current business behavior while changing layout, hierarchy, framing, and control treatment
- Finish the redesign in a way that can be verified incrementally without destabilizing the app

## Non-Goals

- Replacing Vue or Element Plus
- Changing route structure or permission logic
- Removing business fields, filters, columns, or actions
- Introducing new analytics modules, charts, or feature workflows that do not already exist
- Making mobile pages identical to desktop layouts

## Constraints

- The codebase remains on Vue 3, Vite, Element Plus, Vant, Pinia, and SCSS
- Existing APIs, data models, and route behavior must stay intact
- Desktop and mobile flows must remain usable on their current routes
- Shared component changes must not silently break existing list or form behavior
- The redesign should prefer structural reuse over page-specific style hacks

## Design Direction

The whole application should inherit the same high-level language already started on the upstream contracts workspace:

- Framed but calm workspaces
- Light neutral surfaces
- Low-contrast borders
- Controlled radii rather than inflated cards
- Consistent 40px control heights where applicable
- Cleaner spacing between page header, filters, content blocks, and action areas
- Reduced reliance on heavy shadows, gradients, and inconsistent Element Plus defaults

The product should feel like one system, but not every page family should be forced into the exact same layout:

- Desktop business pages use the main workspace shell
- Mobile pages use a compact adaptive version of the same system
- Login uses the same tokens and interaction language, but an auth-specific composition

## Page Families

### 1. List Workspace

Applies to:

- `frontend/src/views/contracts/UpstreamList.vue`
- `frontend/src/views/contracts/ManagementList.vue`
- `frontend/src/views/contracts/DownstreamList.vue`
- `frontend/src/views/expenses/ExpenseList.vue`
- Embedded expense list blocks such as `OrdinaryExpenseList.vue` and `ZeroHourLaborList.vue`

Shared structure:

- Page header
- Optional tab switcher
- Filter region
- Data region
- Pagination region
- Mobile card region where already supported

Preserved behavior:

- All existing filters
- All existing table columns
- Existing imports, exports, details, edits, deletes, and permission gates

### 2. Detail Workspace

Applies to:

- `frontend/src/views/contracts/UpstreamDetail.vue`
- `frontend/src/views/contracts/ManagementDetail.vue`
- `frontend/src/views/contracts/DownstreamDetail.vue`

Shared structure:

- Page header and return context
- Overview block for key identity information
- Grouped form or detail sections
- Attachment and document blocks
- Consistent action area

Preserved behavior:

- Existing fields
- Existing save and navigation flows
- Existing attachment and preview behavior

### 3. Utility Workspace

Applies to:

- `frontend/src/views/Dashboard.vue`
- `frontend/src/views/reports/ReportDashboard.vue`
- `frontend/src/views/notifications/NotificationCenter.vue`
- `frontend/src/views/system/SystemManagement.vue`
- `frontend/src/views/audit/AuditLog.vue`

Shared structure:

- Page header
- Toolbar or utility actions
- Content cards or table sections
- Optional stats or summary rows where the page already contains them

Preserved behavior:

- Existing report behavior
- Existing notification actions
- Existing settings management
- Existing audit log filtering and viewing

### 4. Mobile Workspace

Applies to:

- `frontend/src/views/mobile/MobileLayout.vue`
- `frontend/src/views/mobile/ContractListMobile.vue`
- `frontend/src/views/mobile/ExpenseListMobile.vue`
- Mobile use of `ReportDashboard.vue`
- Mobile use of `SystemManagement.vue`

Shared structure:

- Compact page header
- Touch-friendly navigation and action targets
- Card-based content stacks
- Responsive filter presentation
- Consistent bottom navigation or shell framing

Preserved behavior:

- Existing mobile routes
- Existing mobile navigation affordances
- Existing mobile access to reports and system pages

### 5. Auth Workspace

Applies to:

- `frontend/src/views/Login.vue`

Shared structure:

- Brand block
- Login form card
- Clear primary action
- Same control and button language as the rest of the product

Preserved behavior:

- Existing login form flow
- Existing validation behavior

## Shared Design System Targets

The redesign should be driven through shared layers first and page-level overrides second.

Primary shared targets:

- `frontend/src/views/Layout.vue`
- `frontend/src/styles/tokens.scss`
- `frontend/src/components/ui/AppSectionCard.vue`
- `frontend/src/components/ui/AppFilterBar.vue`
- `frontend/src/components/ui/AppDataTable.vue`
- `frontend/src/components/ui/AppRangeField.vue`

Additional shared page-level primitives may be introduced where repetition becomes clear, especially for:

- Page headers
- Detail section grouping
- Mobile content cards
- Auth layout framing

## Visual Rules

### Shell

- Use a calmer framed workspace on desktop
- Keep sidebar and topbar visually lighter than before
- Make the content canvas feel deliberate and bounded

### Surfaces

- White or near-white surfaces
- 1px low-contrast borders
- Minimal shadows for separation only

### Controls

- Normalize list and form controls to consistent heights where possible
- Use restrained radius values
- Keep primary actions visually clear without over-saturating the page

### Typography

- Stronger page titles
- Lighter support text
- Cleaner section titles
- More disciplined label and table heading tone

### Mobile

- Preserve touch comfort and density balance
- Avoid shrinking desktop patterns mechanically
- Keep the same tokens and hierarchy with mobile-specific composition

## Implementation Architecture

The redesign should proceed by expanding the current upstream work into reusable page templates rather than repeating one-off CSS across files.

Recommended template layers:

1. Workspace shell
2. Page header
3. Section card
4. List page template
5. Detail page template
6. Utility page template
7. Mobile page template
8. Auth template

The code should stay pragmatic:

- Extend existing wrappers before introducing new abstractions
- Extract new page-level primitives only when multiple pages need the same structure
- Avoid converting every page at once without intermediate verification

## Implementation Order

1. Finish shared primitives needed by all list pages
2. Convert remaining desktop list pages to the workspace language
3. Convert desktop detail pages to a shared detail workspace structure
4. Convert utility pages to the same page-header and section system
5. Convert mobile pages to the mobile workspace system
6. Convert login to the auth workspace system
7. Run final verification across desktop, mobile, and auth flows

## Verification Strategy

Verification must be incremental and evidence-based:

- Add or expand targeted frontend tests where page structure becomes part of the contract
- Re-run affected list and related-page tests after each batch
- Run `npm run build` after major UI batches
- Run `./.venv39/bin/pytest backend/tests/test_contracts.py -q` for contract-related redesign batches
- Manually verify desktop and mobile rendering for each page family before calling the redesign complete

## Risks

### Shared Component Spillover

Changing shared wrappers will affect pages before they are fully restyled.

Mitigation:

- Roll out by page family
- Use page-scoped classes where a page needs extra fidelity

### Detail Page Variance

The three contract detail pages are similar but not identical.

Mitigation:

- Share the structural skeleton
- Keep field-specific layouts page-local where needed

### Mobile/Desktop Drift

Desktop patterns do not map directly to small screens.

Mitigation:

- Share tokens and hierarchy, not identical composition

### Utility Page Diversity

Dashboard, reports, notifications, system, and audit have different content models.

Mitigation:

- Share header and section primitives
- Allow content-specific internal layouts

## Acceptance Criteria

- The full product visually reads as one `dashboard-01` inspired system
- Desktop list pages share a consistent filter, card, table, and pagination language
- Desktop detail pages share a consistent page header and section structure
- Utility pages no longer feel visually disconnected from business pages
- Mobile pages feel like the same product, adapted for small screens
- Login matches the system visually without reusing the business-page layout directly
- Existing routes, permissions, and business behavior remain intact
