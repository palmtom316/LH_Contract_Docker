# Upstream Dashboard-01 Redesign

## Summary

Rebuild the upstream contract experience to follow the visual structure and interaction language of `shadcn/ui` `new-york-v4/dashboard-01`, while keeping the existing Vue 3 + Element Plus + SCSS stack and preserving current upstream contract functionality.

This redesign covers:

- The global application shell used by the upstream contract page
- The upstream contract page content area
- The two existing upstream page tabs
- The shared visual treatment of section cards, filter bars, range fields, and data tables used on this page

This redesign does not cover:

- React, Tailwind, or shadcn/ui migration
- New metrics cards, charts, or summary panels
- Breaking functional changes to filters, table columns, exports, imports, permissions, or routing
- Splitting the two current upstream tabs into separate pages

## Goals

- Make the upstream contract page feel structurally and visually close to `dashboard-01`
- Preserve all current upstream contract capabilities
- Keep both existing tabs in one page
- Keep all current filter fields, table columns, and actions
- Upgrade the app shell so the page does not feel visually disconnected from the rest of the layout
- Build the redesign in a way that can later be extended to downstream contracts, management contracts, expenses, and audit pages

## Non-Goals

- Exact 1:1 source-code parity with the upstream React example
- Replacing Element Plus controls with a new component library
- Functional simplification of upstream contract workflows
- New dashboard analytics content

## Constraints

- The project remains on Vue 3, Vite, Element Plus, Pinia, and SCSS
- Existing route names, permission checks, API calls, and page behaviors must remain intact
- The upstream page must keep the current two-tab behavior
- Existing mobile behavior must continue to work after the redesign
- Shared component changes must avoid breaking existing consumers

## Design Direction

The target should be interpreted as a block-level design language, not as a direct component port.

The redesign should borrow these characteristics from `dashboard-01`:

- A calmer, flatter application shell
- More deliberate page framing and spacing
- Strong separation between page header, filters, and data regions
- Medium-radius cards with low-contrast borders
- Inputs and buttons with consistent height and restrained styling
- Cleaner table framing with lighter header and hover states
- Tighter visual rhythm and less decorative gradient or glow styling

The redesign should avoid:

- Heavy gradients
- High-contrast shadows
- Oversized radii that make surfaces feel inflated
- Mixed control heights
- Element Plus default visual styling bleeding through unchanged

## Scope

### 1. Global Shell

Update the shell in `frontend/src/views/Layout.vue` so the upstream page sits inside a more `dashboard-01`-like frame.

Changes include:

- Rework sidebar spacing, item height, active state, and background treatment
- Rework topbar layout and visual weight
- Make the content canvas feel more like a framed workspace than a plain full-width content column
- Preserve all current navigation items, permission logic, notification drawer behavior, and collapse behavior

### 2. Upstream Page Structure

Update `frontend/src/views/contracts/UpstreamList.vue` to use a clearer block layout:

- Page intro/header area
- Tab switcher area
- Filter section
- Table section
- Mobile list section

The two current tabs remain:

- `合同管理`
- `上游合同基本信息`

Their behavior remains unchanged. Only structure and visual presentation are redesigned.

### 3. Filter Section

The filter section must preserve all current fields and actions.

Management tab filters remain:

- Keyword
- Status
- Company contract category
- Contract category
- Management mode
- Start/end date range
- Search
- Reset
- Export
- Import
- Create contract

Basic info tab filters remain aligned with current behavior.

The redesign will:

- Use a more disciplined grid
- Give the keyword field the highest width priority
- Normalize all input, select, and date-range heights
- Reduce border and shadow emphasis
- Move the overall look closer to shared shadcn-style control framing

### 4. Table Section

The data table remains functionally equivalent.

Preserved behaviors:

- Current columns
- Summary/footer behavior
- Pagination
- Fixed columns
- Detail, edit, delete actions
- Desktop table and mobile card variants

The redesign will:

- Put the table in a more restrained data card
- Improve table header/body contrast hierarchy
- Normalize padding and row density
- Integrate pagination into the card layout more cleanly

### 5. Shared Components

The upstream redesign will be built partly through shared components so the page does not require one-off styling hacks.

Primary shared targets:

- `frontend/src/components/ui/AppSectionCard.vue`
- `frontend/src/components/ui/AppFilterBar.vue`
- `frontend/src/components/ui/AppDataTable.vue`
- `frontend/src/components/ui/AppRangeField.vue`

These shared changes should be designed so they can support later rollouts to other list pages, while the first fidelity target remains the upstream page.

## Visual Rules

### Surfaces

- Page canvas: soft neutral background
- Card surfaces: flat or near-flat white/light surfaces
- Borders: low-contrast, 1px, consistent
- Shadows: minimal, mostly for separation not decoration

### Radii

- Shell and cards should use medium radii
- Filter controls and buttons should use smaller but still rounded radii
- Avoid oversized pill or inflated radii except where the existing UI demands them

### Controls

- Normalize filter controls to a shared height
- Search input should visually anchor the filter row
- Primary action should be clear but not overly saturated
- Secondary actions should sit back visually

### Typography

- Stronger page title hierarchy
- Lighter support text
- Tighter control labels and table header tone
- Avoid overly bold body copy

## Behavior Requirements

- No filter is removed
- No table column is removed
- No current route behavior changes
- No permission gating changes
- Existing import/export flows keep working
- Existing detail navigation keeps working
- Existing mobile rendering keeps working

## Risks

### Shared Component Spillover

Because the redesign touches shared UI wrappers, downstream pages may change appearance even before they are explicitly redesigned.

Mitigation:

- Keep shared primitives neutral
- Add page-scoped styling where upstream needs stronger fidelity

### Element Plus Visual Leakage

Element Plus internals may resist the target look in some controls.

Mitigation:

- Override wrapper-level control styling in shared components
- Prefer structural restyling over fragile one-off deep selectors where possible

### Layout Density

The upstream page has more filters and controls than the reference block.

Mitigation:

- Keep all controls
- Use a disciplined responsive grid
- Preserve mobile stacking behavior

## Testing Strategy

Verification must include:

- Existing relevant frontend tests for upstream and related filter behavior
- Backend contract tests that cover upstream serial matching and related-list upstream filters
- A production build for the frontend after layout changes
- Manual desktop and mobile checks for upstream tabs, filters, tables, and pagination

## Implementation Order

1. Update the global shell tokens and layout framing
2. Rework the shared card/filter/table visual primitives
3. Restructure the upstream page layout and tab presentation
4. Tune the upstream filter section and table section
5. Verify desktop and mobile rendering
6. Run automated tests and build verification

## Acceptance Criteria

- The upstream contract page visually reads as a `dashboard-01`-style workspace
- The global shell no longer clashes with that page style
- Both existing tabs remain in one page and function as before
- All current upstream filters, actions, and table capabilities remain available
- Shared primitives are improved without introducing regressions in covered tests
