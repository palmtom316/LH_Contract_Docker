# Dashboard, Table, and Export Refinement

## Summary

Refine three existing product areas without changing route structure or core business behavior:

- Rework the chart presentation on the overview page and business dashboard so the data reads clearly at a glance
- Reduce table density issues on the three desktop contract list pages by shrinking text and allowing long content to wrap
- Add `公司合同分类` to the two specified Excel exports

The preferred implementation is a moderate frontend-led redesign: keep existing APIs where possible, improve composition and readability, and only touch backend export assembly where the extra Excel column is required.

## Goals

- Make dashboard charts readable for operational users without forcing them to decode multiple crowded pies
- Improve scan efficiency in contract tables while preventing long names from truncating important information
- Align exported Excel data with the fields users already rely on in the application

## Non-Goals

- Rebuilding dashboard APIs from scratch
- Changing the meaning of existing dashboard metrics
- Restyling mobile card views for the three contract pages
- Changing export filters, filenames, or permission logic

## Confirmed Scope

### 1. Chart pages

- `frontend/src/views/home/Overview.vue`
- `frontend/src/views/home/Business.vue`

### 2. Contract list pages

- `frontend/src/views/contracts/UpstreamList.vue`
- `frontend/src/views/contracts/DownstreamList.vue`
- `frontend/src/views/contracts/ManagementList.vue`

### 3. Export flow

- `frontend/src/views/reports/ReportDashboard.vue`
- `backend/app/routers/reports/exports.py`

## Constraints

- Keep current Vue 3 + Element Plus + SCSS structure
- Prefer reusing current datasets rather than adding new dashboard endpoints
- Preserve existing filters, actions, summaries, and permission gates
- Limit table typography changes to the three requested contract list pages
- Export semantics are fixed:
  - `上游合同综合报表` uses the upstream contract's own `company_category`
  - `上下游合同关联报表` uses the associated upstream contract's `company_category`

## Design Direction

The dashboards should move away from "many pies on one screen" toward comparison-first charts:

- horizontal ranking bars for category distributions
- grouped or stacked bars where users need comparison across series
- Top 6 plus `其他` when long-tail categories would otherwise create noisy legends
- cleaner tooltips showing amount and share together

The tables should become denser but not cramped:

- slightly smaller body text
- desktop table body text set to 12px with a 1.45 line-height baseline
- vertical top alignment for multi-line cells
- long names and company fields wrap naturally instead of forcing tooltip-only reading

The exports should surface `公司合同分类` near the core contract identity fields so downstream spreadsheet users can filter immediately.

## Architecture

### 1. Overview page

Current state:

- Annual and period bars are already present
- The weakest section is the final `合同分类` block, which currently uses two pie charts fed by `/dashboard/stats`

Planned refinement:

- Keep the annual trend and period charts structurally intact
- Replace the two pie-based composition charts with horizontal ranking bars
- Continue consuming `charts.pie_category` and `charts.pie_company`, but transform those arrays into ranked bar series in the frontend
- If category counts are large, fold the remainder into `其他` before rendering

Outcome:

- no backend schema change for `Overview.vue`
- improved readability with lower label collision and clearer category ordering

### 2. Business dashboard

Current state:

- One trend chart plus four composition pies in `Business.vue`
- The page currently overuses pie/rose charts for category-heavy data

Planned refinement:

- Keep the top metric cards and trend chart
- Replace the four pie cards with a two-row, two-column grid of ranking/comparison bar charts
- Recommended chart mapping:
  - `上游合同分类`: horizontal bar ranking
  - `上游公司分类`: horizontal bar ranking
  - `支出构成`: stacked horizontal or simple bar comparison for downstream / management / non-contract / zero-hour labor
  - `无合同费用分类`: Top N horizontal ranking with `其他`
- Keep the same report endpoints:
  - `getContractSummary`
  - `getFinanceTrend`
  - `getExpenseBreakdown`
  - `getArApStats`

Outcome:

- frontend-only chart re-composition
- no change to report query contracts unless a small helper extraction materially simplifies repeated chart config

### 3. Contract list tables

Current state:

- The three pages already contain ad hoc inline wrapping styles
- Typography and wrapping rules are inconsistent across pages and columns

Planned refinement:

- Apply a shared table density style on the desktop `el-table` instances of the three pages
- Reduce body font size to 12px
- Normalize line-height to 1.45 and reduce cell vertical padding to a compact desktop density
- Set long-text columns to wrap by default, especially:
  - contract name
  - party name fields
  - any similar long identity field already rendered with custom cell templates
- Keep numeric amount cells on one line for scan stability
- Preserve overflow tooltips where they still help, but stop depending on them as the primary way to read long content

Implementation preference:

- use shared class hooks plus scoped page styles instead of repeated inline style objects
- avoid broad global table overrides in `frontend/src/styles/index.scss` unless a very small token-level adjustment is clearly safe

### 4. Excel exports

#### 上游合同综合报表

File:

- `backend/app/routers/reports/exports.py`

Change:

- add `公司合同分类` using `c.company_category`
- place the column near the contract identity fields, before downstream aggregate metrics

#### 上下游合同关联报表

File:

- `backend/app/routers/reports/exports.py`

Change:

- add `公司合同分类` sourced from the associated upstream contract `up.company_category`
- include it in the `base_info` block so the exported row remains self-contained

Frontend impact:

- `ReportDashboard.vue` export triggers remain unchanged unless labels/help text need a minor update

## File Plan

- `frontend/src/views/home/Overview.vue`
- `frontend/src/views/home/Business.vue`
- `frontend/src/views/contracts/UpstreamList.vue`
- `frontend/src/views/contracts/DownstreamList.vue`
- `frontend/src/views/contracts/ManagementList.vue`
- `backend/app/routers/reports/exports.py`

Optional only if repetition warrants it:

- shared chart helper under `frontend/src/utils/echarts`
- shared table utility class in an existing UI style layer

## Data and Behavior Rules

- Dashboard ranking charts sort by amount descending
- Long-tail categories collapse into `其他` only when there are more than 6 categories in the source data
- Empty datasets still render stable empty-state chart placeholders rather than broken panels
- Table row height may grow for wrapped text, but pagination, summary rows, and action columns must continue working
- Export column additions must not remove or rename existing columns

## Error Handling

- Existing dashboard fetch error handling stays in place
- If a chart dataset is empty, render a readable empty chart state instead of an empty legend-heavy pie
- If `company_category` is missing during export, output empty string rather than failing the export

## Testing and Verification

### Frontend

- Validate overview page chart rendering on desktop and current mobile behavior
- Validate business dashboard rendering for full-year and month-filtered views
- Validate the three contract list pages with long contract names and long party names
- Confirm summary rows, fixed columns, and action buttons still align after row-height changes

### Backend

- Verify `上游合同综合报表` exported workbook contains `公司合同分类`
- Verify `上下游合同关联报表` exported workbook contains upstream `公司合同分类`
- Confirm existing export endpoints still open successfully in Excel after column insertion

### Regression focus

- no route changes
- no permission regressions
- no filter behavior regressions
- no broken mobile list cards from desktop-only table styling

## Risks and Mitigations

- Risk: chart rewrites become visually better but structurally inconsistent across pages
  - Mitigation: use a small set of repeated chart conventions for ranking bars, tooltip formatting, and empty-state handling

- Risk: wrapped table content causes over-tall rows or broken fixed-column alignment
  - Mitigation: limit wrapping to text columns, keep numeric columns single-line, and verify with real long strings

- Risk: export column insertion accidentally shifts downstream parsing expectations
  - Mitigation: add the new column without renaming existing headers and verify the final header order explicitly

## Implementation Boundary

This spec is sized for one implementation plan and one focused delivery cycle. It does not require decomposing into separate projects because:

- chart work is limited to two known frontend pages
- table work is limited to three known desktop list pages
- export work is limited to two known backend export builders

## Approval Baseline

This design reflects the already confirmed choices:

- use a moderate redesign, not a deep backend rebuild
- prefer less pie, more bar/column-based comparison
- limit table styling changes to the three contract list pages
- add `公司合同分类` to the two requested exports using the confirmed field semantics
