# Upstream Query Tab Integration

Date: 2026-04-13
Status: Proposed and user-approved for spec drafting
Scope: Move the upstream contract query experience out of the global topbar dialog and into the existing `上游合同` module as a first-class tab in the current tab set.

## Background

The current upstream contract query experience is built around a global topbar trigger and a modal-style `ContractQueryBot`:

- users open it from the top-right chrome
- users can also open it with `Ctrl+K` / `Cmd+K`
- the main query surface lives inside a dialog rather than the `上游合同` workspace

That interaction model no longer matches the desired information architecture. The query feature should belong to the `上游合同` module itself and should be reached through the page's existing top tab bar, not through a separate global entry or keyboard shortcut.

## Goals

1. Make `上游合同查询` a tab inside the current `上游合同` page tab set.
2. Place the new query tab immediately after the default tab.
3. Remove the global topbar entry for upstream contract query.
4. Remove the `Ctrl+K` / `Cmd+K` modal-open behavior entirely.
5. Preserve the existing query feature set:
   - dynamic filtering
   - export
   - result table
   - drill-down navigation to related modules
6. Keep the visual language aligned with the existing `上游合同` workspace rather than modal tooling.

## Non-Goals

1. Do not redesign the actual query fields or result columns.
2. Do not change backend query APIs or the export API.
3. Do not merge the default list tab filters with the query tab filters.
4. Do not add a new global search framework or reusable command palette pattern.
5. Do not change unrelated contract modules unless required by navigation compatibility.

## Approved Direction

Use a split-component approach:

- extract the reusable query content from `ContractQueryBot.vue`
- render that content inside a new tab in `UpstreamList.vue`
- remove the dialog shell and all global opening mechanisms

This is preferred over copying the query markup directly into `UpstreamList.vue` because it keeps the query logic cohesive and avoids further inflating an already large page component.

## Information Architecture

### Current

- `上游合同` page has its own tab set
- upstream query is a separate global affordance in the topbar
- the query UI opens in a dialog

### Target

- upstream query becomes a sibling tab within the existing `上游合同` tab set
- the new tab sits directly after the default tab
- users enter query mode by switching tabs inside the module
- no topbar button remains for this feature
- no keyboard shortcut remains for this feature

## Component Design

### `UpstreamList.vue`

Responsibilities after the change:

- continue to own the existing upstream module tab set
- add a new tab named `上游合同查询`
- place the new tab after the default tab
- optionally sync the active tab with route query state such as `?tab=query`

It should not absorb the full internal implementation of the query panel.

### Extracted query content component

Create a focused reusable component for the current query workspace content. This component should own:

- query filter state
- debounced server-side refresh
- result loading and error state
- pagination
- export behavior
- drill-down navigation

It should render the existing filter card and result table as page content rather than dialog content.

Suggested shape:

- keep the current `ContractQueryBot.vue` file only if it is repurposed as the extracted content component
- otherwise introduce a clearer name such as `UpstreamContractQueryPanel.vue`

The key requirement is that the dialog shell and `modelValue` contract disappear from the final structure.

### Removed global entry components

The following global integration should be removed:

- topbar query button in `AppTopbarActions.vue`
- `ContractQueryEntry.vue`
- dialog mount and visibility state in `Layout.vue`
- `open-contract-query` event wiring
- keyboard shortcut listener for `Ctrl+K` / `Cmd+K`

## UX and Behavior

### Tab order

Required order:

1. existing default tab
2. `上游合同查询`
3. existing subsequent tabs in their current order

### Default entry behavior

- opening `/contracts/upstream` should still land on the current default tab
- users must switch manually to `上游合同查询`

### Query tab behavior

The query tab preserves current behavior:

- keyword filter
- 甲方单位 filter
- 合同类别 filter
- 公司分类 filter
- 签约日期范围 filter
- automatic refresh with debounce
- result pagination
- Excel export
- click-through navigation to:
  - upstream detail
  - downstream contract list
  - management contract list
  - expense list
  - zero-hour labor list

### State separation

The default tab and query tab should maintain separate local filter state.

Reasoning:

- they are different tools serving different workflows
- shared state would create accidental cross-contamination
- separate state is simpler to reason about and test

### Optional route-state sync

Recommended but intentionally light:

- support a route query such as `?tab=query`
- preserve the current tab on refresh or copied links

This route-state sync applies to tab selection only. It does not need to serialize the full query tab filter model in this change.

## Data and API Contract

No backend contract changes are required.

The tab-integrated query view should continue using the existing upstream contract query endpoints and export endpoint. Parameter names and response handling remain unchanged.

## Cleanup Scope

Files expected to change:

- `frontend/src/views/contracts/UpstreamList.vue`
- `frontend/src/components/ContractQueryBot.vue` or its replacement
- `frontend/src/views/Layout.vue`
- `frontend/src/components/layout/AppTopbarActions.vue`
- `frontend/src/components/layout/ContractQueryEntry.vue`
- related tests for upstream list, layout actions, and query entry behavior

Files likely to be removed:

- `frontend/src/components/layout/ContractQueryEntry.vue`
- its dedicated test file if no replacement is needed

## Testing

Minimum verification scope:

1. `UpstreamList` renders the new `上游合同查询` tab in the correct position.
2. default navigation to `/contracts/upstream` still opens the original default tab.
3. switching to the query tab renders the extracted query content.
4. topbar actions no longer render the old contract query entry.
5. `Layout.vue` no longer mounts the old dialog or manages its open state.
6. keyboard shortcut tests for `Ctrl+K` / `Cmd+K` are removed or replaced with assertions that no shortcut entry exists.
7. query component tests continue to cover:
   - result loading
   - empty/error state
   - export disabled state
   - drill-down navigation triggers

## Risks and Mitigations

- Risk: query functionality regresses while extracting content from the dialog shell.
  - Mitigation: keep the query logic together in a dedicated component rather than spreading it across `UpstreamList.vue`.

- Risk: removing the topbar entry leaves stale event contracts and dead state in layout components.
  - Mitigation: remove the full event chain from trigger component through layout mount point in one change.

- Risk: tab refresh behavior feels inconsistent if state is not persisted.
  - Mitigation: add lightweight `tab` query synchronization.

- Risk: existing tests are tightly coupled to the dialog implementation.
  - Mitigation: rewrite tests around observable user behavior instead of modal internals where possible.

## Implementation Boundary

This is one focused frontend refactor:

- one module-level navigation change
- one query component extraction
- one global entry removal
- no backend work

It does not need decomposition into multiple specs.

## Approval Baseline

Approved by user:

- use the split-component approach
- integrate query into the existing upstream page tab set
- place the query tab after the default tab
- remove the global topbar entry
- remove `Ctrl+K` / `Cmd+K` opening behavior
