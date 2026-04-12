# Contract Query Panel Design

Date: 2026-04-12
Status: Proposed and user-approved for spec drafting
Scope: Replace the current "合同查询助手" floating assistant with a top-right contract query entry and a hybrid command-palette/query-panel experience aligned with the existing application visual system.

## Background

The current `ContractQueryBot` is a floating dialog-driven helper. It does not match the desired interaction model:

- Entry should live in the top-right app chrome instead of as a floating button.
- Users should be able to open it with `Ctrl+K` and click a small icon.
- The opened experience should focus on dynamic filtering of upstream contracts rather than chat-style querying.
- Results should be tabular, exportable, and support drill-down into related downstream contracts, management contracts, non-contract expenses, and zero-hour labor.

The new experience should feel like part of the existing LH Contract workspace, not like a separate AI/chat tool.

## Goals

1. Replace the current "合同查询助手" entry with a top-right icon button consistent with the existing layout.
2. Open a hybrid query panel by click, `Ctrl+K`, or `Cmd+K`.
3. Query only upstream contracts.
4. Support dynamic filtering by:
   - Fuzzy keyword input
   - 甲方单位
   - 合同类别
   - 合同公司分类
   - 签约日期范围
5. Show a result table with upstream contract data plus related aggregate metrics.
6. Support Excel export for the current filtered result set.
7. Support drill-down from metric cells into related list pages.
8. Preserve the visual language and interaction patterns already used by the rest of the application.

## Non-Goals

1. Do not build a chat assistant or LLM-style conversation UI.
2. Do not introduce a new global design system or a visually divergent command palette.
3. Do not replace existing downstream, management, expense, or zero-hour list pages; the query panel links into them.
4. Do not implement client-side full-dataset filtering. Filtering should be server-backed.

## Primary User Flow

1. User hovers the top-right small icon.
2. Tooltip shows `合同查询`.
3. User clicks the icon or presses `Ctrl+K` / `Cmd+K`.
4. A wide query panel opens.
5. User enters keyword and/or adjusts filters.
6. Results update dynamically with debounce.
7. User can:
   - inspect upstream contract metrics in the table
   - export the filtered result set
   - click related metric cells to jump to downstream/management/expense/zero-hour detail lists

## UX Model

### Entry

- Location: top-right app chrome, next to existing topbar actions in `Layout.vue`
- Form: small icon button
- Hover behavior:
  - standard tooltip text: `合同查询`
  - subtle hover emphasis consistent with current topbar interactions
- Keyboard:
  - `Ctrl+K` on Windows/Linux
  - `Cmd+K` on macOS
  - if the panel is already open, shortcut focuses the main search input

### Opened Panel

The panel is hybrid rather than purely command-palette style:

- Top section behaves like a command palette:
  - one prominent main search input
  - compact contextual filters directly below
  - fast open/close and fast keyboard access
- Main body behaves like a query workspace:
  - filter chips / compact controls
  - result table
  - export action
  - row and cell interactions

### Visual Direction

The panel must match the rest of the system:

- use existing workspace shell patterns
- use existing app surface tokens and shadows
- use existing table/filter card components where practical
- avoid a neon, AI, or chat-app aesthetic
- use the same typography, spacing rhythm, and panel framing already present in workspace pages

The visual style should read as "native advanced query tool inside the system" rather than "assistant popup".

## Search and Filter Model

### Query Scope

Returned rows represent upstream contracts only.

### Filter Inputs

1. Main keyword
   - fuzzy match against upstream contract name and optionally contract code / serial number
2. 甲方单位
   - selectable and searchable
   - supports fuzzy input
3. 合同类别
4. 合同公司分类
5. 签约日期范围

### Filtering Behavior

- Filter changes trigger server-side query with debounce.
- Search should not require pressing a dedicated button, though a manual refresh/search button may remain for clarity.
- Clear action resets all filters and results.
- Active filters should be visually obvious.

## Result Table

Each row represents one upstream contract and displays:

1. 合同名称
2. 甲方单位
3. 乙方单位
4. 签约金额
5. 签约日期
6. 应收款
7. 挂账金额
8. 已收款
9. 结算金额
10. 关联下游合同个数
11. 关联下游合同签约总金额
12. 关联下游合同结算总金额
13. 关联下游合同已付款总金额
14. 关联管理合同个数
15. 关联管理合同签约总金额
16. 关联管理合同结算总金额
17. 关联管理合同已付款总金额
18. 关联无合同费用总金额
19. 关联零星用工总金额

### Table Behavior

- supports loading state
- supports empty state
- supports horizontal scrolling for desktop widths where needed
- column formatting uses the same money/date formatting conventions as the rest of the app
- header and row styling stays consistent with existing table pages

## Drill-Down Behavior

Specific cells act as navigable metrics.

### Downstream Drill-Down

Clickable cells:

- 关联下游合同个数
- 关联下游合同签约总金额
- 关联下游合同结算总金额
- 关联下游合同已付款总金额

Action:

- navigate to downstream contract detail list view filtered to records associated with the selected upstream contract

### Management Drill-Down

Clickable cells:

- 关联管理合同个数
- 关联管理合同签约总金额
- 关联管理合同结算总金额
- 关联管理合同已付款总金额

Action:

- navigate to management contract detail list view filtered to records associated with the selected upstream contract

### Expense Drill-Down

Clickable cell:

- 关联无合同费用总金额

Action:

- navigate to non-contract expense list filtered by the selected upstream contract

### Zero-Hour Labor Drill-Down

Clickable cell:

- 关联零星用工总金额

Action:

- navigate to zero-hour labor list filtered by the selected upstream contract

### Navigation Contract

- Current query panel closes after navigation.
- Filter context in destination pages should be passed by route query parameters whenever supported.
- At minimum, upstream contract id must be passed.

## Export

### Behavior

- Export button exports the currently filtered upstream contract result set.
- Export respects all active filters.

### Output

- Excel file
- columns mirror the result table
- file naming follows existing report/export conventions

## Data Contract

The current `contract_search` response shape is not ideal for this use case. A dedicated aggregate query endpoint is recommended.

### Recommended Endpoint

`GET /api/v1/contract-search/upstream-query`

Parameters:

- `keyword`
- `party_a_name`
- `contract_category`
- `company_category`
- `sign_date_start`
- `sign_date_end`
- `page`
- `page_size`

Response row shape:

- upstream contract base info
- upstream finance summary
- downstream aggregate summary
- management aggregate summary
- non-contract expense aggregate summary
- zero-hour labor aggregate summary

### Recommended Export Endpoint

`GET /api/v1/contract-search/upstream-query/export`

Uses the same filters and returns Excel.

## Frontend Implementation Plan Shape

### Existing Component Evolution

The current `ContractQueryBot.vue` should be replaced in role, not merely restyled.

Recommended split:

1. `ContractQueryEntry.vue`
   - top-right icon trigger
   - tooltip
   - shortcut registration

2. `ContractQueryPanel.vue`
   - open/close state
   - main search input
   - compact filter controls
   - export action
   - result table
   - cell drill-down interactions

3. Supporting composable or module for:
   - debounce query state
   - URL/navigation helpers
   - export request

### Placement

- entry mounted from `Layout.vue`
- panel likely teleported or rendered near top-level layout content, but visually integrated with topbar/workspace shell

## State and Interaction Rules

1. Opening the panel focuses the main search input.
2. Pressing `Esc` closes the panel unless an inner control should consume it first.
3. Re-triggering `Ctrl+K` while open focuses the main input.
4. Debounce should prevent request spam while typing.
5. Filter changes should preserve a responsive feel even on slower queries.
6. Loading and empty states should be explicit and non-blocking.

## Compatibility and Constraints

1. Must preserve current permissions model.
2. Must not expose related data users cannot normally access.
3. Must work on desktop first.
4. Mobile can continue using existing patterns; `Ctrl+K` is desktop-only.
5. Styling should reuse existing components where possible to reduce drift.

## Testing Strategy

### Frontend

1. Entry icon renders in topbar
2. Hover tooltip shows `合同查询`
3. Click opens the panel
4. `Ctrl+K` / `Cmd+K` opens and focuses search input
5. Filter changes trigger query requests with expected params
6. Table renders expected columns
7. Export action calls the export endpoint
8. Clickable metric cells navigate with correct route/query params

### Backend

1. Aggregate query returns only upstream rows
2. All filters apply correctly
3. Aggregated downstream/management/expense/zero-hour values match fixture data
4. Export output respects the current filters
5. Permission boundaries remain intact

## Risks

1. Existing search APIs may not provide enough aggregate data efficiently.
2. Drill-down route targets may need query-parameter support in destination pages.
3. Wide metric tables can become unreadable if spacing and sticky columns are not handled carefully.
4. Shortcut registration must avoid interfering with text inputs already focused elsewhere.

## Recommendation

Implement the query panel as a dedicated topbar query workspace, not as a reskinned chatbot. Keep the visual language consistent with current pages and optimize for fast upstream filtering plus metric-based drill-down.
