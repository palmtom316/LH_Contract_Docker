# Contract Query Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current contract query bot with a top-right contract query entry and a hybrid upstream-contract query panel that supports dynamic filters, aggregate metrics, Excel export, keyboard shortcut access, and drill-down navigation.

**Architecture:** Add a dedicated upstream aggregate query/export backend pair instead of stretching the existing chatbot search response. On the frontend, split the current floating bot into a topbar entry component and a workspace-aligned query panel component that owns debounced filter state, export, and drill-down routing.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Vue 3, Element Plus, Vitest, existing app workspace UI components

---

## File Map

### Backend

- Modify: `backend/app/routers/contract_search.py`
  - add upstream aggregate response models
  - add list query endpoint
  - add export endpoint
- Modify: `backend/tests/test_contract_search_permissions.py`
  - cover permission boundaries for the new endpoint
- Modify: `backend/tests/test_api_integration.py`
  - cover aggregation math and export shape

### Frontend

- Replace: `frontend/src/components/ContractQueryBot.vue`
  - convert from floating assistant to query panel container
- Create: `frontend/src/components/layout/ContractQueryEntry.vue`
  - small top-right icon entry with tooltip and shortcut wiring
- Modify: `frontend/src/components/layout/AppTopbarActions.vue`
  - mount the new query entry
- Modify: `frontend/src/api/contractSearch.js`
  - add aggregate list and export API helpers
- Modify: `frontend/src/components/__tests__/ContractQueryBot.spec.js`
  - rewrite tests around panel interaction
- Create: `frontend/src/components/layout/__tests__/ContractQueryEntry.spec.js`
  - cover icon rendering, tooltip text, click open, shortcut open
- Modify: `frontend/src/views/contracts/DownstreamList.vue`
  - preserve upstream-contract drill-down query handling
- Modify: `frontend/src/views/contracts/ManagementList.vue`
  - preserve upstream-contract drill-down query handling
- Modify: `frontend/src/views/expenses/OrdinaryExpenseList.vue`
  - hydrate upstream filter from route query for drill-down
- Modify: `frontend/src/views/expenses/ZeroHourLaborList.vue`
  - hydrate upstream filter from route query for drill-down

---

### Task 1: Build the failing backend contract-query tests

**Files:**
- Modify: `backend/tests/test_api_integration.py`
- Modify: `backend/tests/test_contract_search_permissions.py`
- Modify: `backend/app/routers/contract_search.py`

- [ ] **Step 1: Write the failing aggregate query integration test**

```python
@pytest.mark.asyncio
async def test_upstream_query_returns_aggregated_related_metrics(
    client,
    admin_token,
    seeded_contract_graph,
):
    response = await client.get(
        "/api/v1/contracts/search/upstream-query",
        params={"keyword": "权限上游合同"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    row = payload["items"][0]
    assert row["contract_name"] == "权限上游合同"
    assert row["downstream_contract_count"] == 1
    assert row["management_contract_count"] == 1
    assert "non_contract_expense_total" in row
    assert "zero_hour_labor_total" in row
```

- [ ] **Step 2: Write the failing export coverage test**

```python
@pytest.mark.asyncio
async def test_upstream_query_export_respects_filters(client, admin_token, seeded_contract_graph):
    response = await client.get(
        "/api/v1/contracts/search/upstream-query/export",
        params={"party_a_name": "甲方公司"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
```

- [ ] **Step 3: Write the failing permission test**

```python
@pytest.mark.asyncio
async def test_user_without_upstream_visibility_cannot_query_upstream_aggregate(client, general_affairs_token):
    response = await client.get(
        "/api/v1/contracts/search/upstream-query",
        headers={"Authorization": f"Bearer {general_affairs_token}"},
    )

    assert response.status_code == 403
```

- [ ] **Step 4: Run targeted backend tests to verify failure**

Run:

```bash
pytest backend/tests/test_api_integration.py -k upstream_query -q
pytest backend/tests/test_contract_search_permissions.py -k upstream_aggregate -q
```

Expected:

- missing route or failing assertions for aggregate fields

- [ ] **Step 5: Commit the red tests**

```bash
git add backend/tests/test_api_integration.py backend/tests/test_contract_search_permissions.py
git commit -m "test: cover upstream contract query aggregates"
```

### Task 2: Implement backend aggregate query and export

**Files:**
- Modify: `backend/app/routers/contract_search.py`
- Test: `backend/tests/test_api_integration.py`
- Test: `backend/tests/test_contract_search_permissions.py`

- [ ] **Step 1: Add explicit response models for the new query**

```python
class UpstreamAggregateRow(BaseModel):
    id: int
    contract_name: str
    party_a_name: str
    party_b_name: str
    category: str | None = None
    company_category: str | None = None
    sign_date: date | None = None
    contract_amount: float = 0
    receivable_amount: float = 0
    invoiced_amount: float = 0
    received_amount: float = 0
    settlement_amount: float = 0
    downstream_contract_count: int = 0
    downstream_contract_amount: float = 0
    downstream_settlement_amount: float = 0
    downstream_paid_amount: float = 0
    management_contract_count: int = 0
    management_contract_amount: float = 0
    management_settlement_amount: float = 0
    management_paid_amount: float = 0
    non_contract_expense_total: float = 0
    zero_hour_labor_total: float = 0


class UpstreamAggregateListResponse(BaseModel):
    total: int
    items: list[UpstreamAggregateRow]
    page: int
    page_size: int
```

- [ ] **Step 2: Implement a shared query builder for upstream aggregate filters**

```python
def _apply_upstream_query_filters(stmt, *, keyword, party_a_name, contract_category, company_category, sign_date_start, sign_date_end):
    if keyword:
        stmt = stmt.where(
            or_(
                ContractUpstream.contract_name.ilike(f"%{keyword}%"),
                ContractUpstream.contract_code.ilike(f"%{keyword}%"),
                cast(ContractUpstream.serial_number, String).ilike(f"%{keyword}%"),
            )
        )
    if party_a_name:
        stmt = stmt.where(ContractUpstream.party_a_name.ilike(f"%{party_a_name}%"))
    if contract_category:
        stmt = stmt.where(ContractUpstream.category.ilike(f"%{contract_category}%"))
    if company_category:
        stmt = stmt.where(ContractUpstream.company_category.ilike(f"%{company_category}%"))
    if sign_date_start:
        stmt = stmt.where(ContractUpstream.sign_date >= sign_date_start)
    if sign_date_end:
        stmt = stmt.where(ContractUpstream.sign_date <= sign_date_end)
    return stmt
```

- [ ] **Step 3: Implement the list endpoint with aggregate joins and sums**

```python
@router.get("/upstream-query", response_model=UpstreamAggregateListResponse)
async def query_upstream_contracts(...):
    if not _search_scope(current_user)["upstream"]:
        raise HTTPException(status_code=403, detail="权限不足")

    base_stmt = select(ContractUpstream)
    base_stmt = _apply_upstream_query_filters(base_stmt, ...)
    total = await _scalar(db, select(func.count()).select_from(base_stmt.subquery()))

    rows = (await db.execute(
        base_stmt.order_by(ContractUpstream.sign_date.desc(), ContractUpstream.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all()

    items = [await _build_upstream_aggregate_row(db, row, current_user) for row in rows]
    return UpstreamAggregateListResponse(total=total, items=items, page=page, page_size=page_size)
```

- [ ] **Step 4: Implement export by reusing the same aggregate row builder**

```python
@router.get("/upstream-query/export")
async def export_upstream_contract_query(...):
    rows = await _list_upstream_contract_aggregates(db, current_user=current_user, export_all=True, ...)
    df = pd.DataFrame([row.model_dump() for row in rows])
    ...
```

- [ ] **Step 5: Run the targeted backend tests to verify pass**

Run:

```bash
pytest backend/tests/test_api_integration.py -k upstream_query -q
pytest backend/tests/test_contract_search_permissions.py -k upstream_aggregate -q
```

Expected:

- PASS for aggregate response and permission checks

- [ ] **Step 6: Commit the backend implementation**

```bash
git add backend/app/routers/contract_search.py backend/tests/test_api_integration.py backend/tests/test_contract_search_permissions.py
git commit -m "feat: add upstream contract query aggregates"
```

### Task 3: Build the failing frontend entry and panel tests

**Files:**
- Create: `frontend/src/components/layout/__tests__/ContractQueryEntry.spec.js`
- Modify: `frontend/src/components/__tests__/ContractQueryBot.spec.js`
- Modify: `frontend/src/components/layout/AppTopbarActions.vue`
- Replace: `frontend/src/components/ContractQueryBot.vue`

- [ ] **Step 1: Write the failing topbar entry test**

```javascript
it('renders a topbar contract query trigger with tooltip copy', async () => {
  const wrapper = mount(AppTopbarActions, { global: { stubs: { AppThemeToggle: true, AppNotificationBell: true } } })
  expect(wrapper.text()).toContain('合同查询')
  expect(wrapper.find('[aria-label=\"打开合同查询\"]').exists()).toBe(true)
})
```

- [ ] **Step 2: Rewrite the bot test around shortcut open and panel rendering**

```javascript
it('opens the panel when ctrl+k is pressed', async () => {
  const wrapper = createWrapper()
  window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true }))
  await wrapper.vm.$nextTick()
  expect(wrapper.find('.contract-query-panel').exists()).toBe(true)
})
```

- [ ] **Step 3: Add a failing drill-down interaction test**

```javascript
it('navigates to downstream contracts when a downstream metric cell is clicked', async () => {
  searchUpstreamContracts.mockResolvedValueOnce({
    total: 1,
    items: [{ id: 7, contract_name: '上游A', downstream_contract_count: 2, downstream_contract_amount: 5000 }]
  })
  ...
  await wrapper.find('[data-cell=\"downstream_contract_count\"]').trigger('click')
  expect(routerPush).toHaveBeenCalledWith(expect.objectContaining({
    path: '/contracts/downstream',
    query: expect.objectContaining({ upstream_contract_id: '7' })
  }))
})
```

- [ ] **Step 4: Run the frontend tests to verify failure**

Run:

```bash
npm test -- src/components/__tests__/ContractQueryBot.spec.js src/components/layout/__tests__/ContractQueryEntry.spec.js
```

Expected:

- missing topbar entry
- missing shortcut support
- missing drill-down table UI

- [ ] **Step 5: Commit the red frontend tests**

```bash
git add frontend/src/components/__tests__/ContractQueryBot.spec.js frontend/src/components/layout/__tests__/ContractQueryEntry.spec.js
git commit -m "test: cover contract query panel entry and interactions"
```

### Task 4: Implement the topbar entry, panel, export, and shortcut flow

**Files:**
- Create: `frontend/src/components/layout/ContractQueryEntry.vue`
- Modify: `frontend/src/components/layout/AppTopbarActions.vue`
- Modify: `frontend/src/components/ContractQueryBot.vue`
- Modify: `frontend/src/api/contractSearch.js`
- Test: `frontend/src/components/__tests__/ContractQueryBot.spec.js`
- Test: `frontend/src/components/layout/__tests__/ContractQueryEntry.spec.js`

- [ ] **Step 1: Add the new aggregate query and export API helpers**

```javascript
export function queryUpstreamContracts(params = {}) {
  return request({
    url: '/contracts/search/upstream-query',
    method: 'get',
    params
  })
}

export function exportUpstreamContracts(params = {}) {
  return request({
    url: '/contracts/search/upstream-query/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}
```

- [ ] **Step 2: Implement the topbar trigger component**

```vue
<template>
  <el-tooltip content="合同查询" placement="bottom">
    <button type="button" class="contract-query-entry" aria-label="打开合同查询" @click="$emit('open')">
      <el-icon><Search /></el-icon>
    </button>
  </el-tooltip>
</template>
```

- [ ] **Step 3: Mount the trigger inside the existing topbar action cluster**

```vue
<template>
  <div class="topbar-actions">
    <ContractQueryEntry @open="$emit('open-contract-query')" />
    <AppThemeToggle />
    <AppNotificationBell :unread-count="unreadCount" />
  </div>
</template>
```

- [ ] **Step 4: Rebuild `ContractQueryBot.vue` as a query workspace panel**

```vue
<template>
  <el-dialog v-model="visible" class="contract-query-panel" :width="panelWidth" append-to-body>
    <div class="contract-query-panel__filters">
      <el-input ref="searchInputRef" v-model="filters.keyword" placeholder="搜索合同名称 / 编号 / 甲方单位" />
      <el-input v-model="filters.party_a_name" placeholder="甲方单位" />
      <DictSelect v-model="filters.contract_category" category="upstream_contract_category" placeholder="合同类别" />
      <DictSelect v-model="filters.company_category" category="project_category" placeholder="合同公司分类" />
      <AppRangeField v-model="signDateRange" start-placeholder="签约开始日期" end-placeholder="签约结束日期" />
      <el-button @click="handleExport">导出</el-button>
    </div>
    <AppDataTable>
      <el-table :data="rows" v-loading="loading">
        ...
      </el-table>
    </AppDataTable>
  </el-dialog>
</template>
```

- [ ] **Step 5: Add `Ctrl+K` / `Cmd+K` shortcut lifecycle**

```javascript
const handleShortcut = (event) => {
  const isShortcut = (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k'
  if (!isShortcut) return
  event.preventDefault()
  visible.value = true
  nextTick(() => searchInputRef.value?.focus?.())
}

onMounted(() => window.addEventListener('keydown', handleShortcut))
onUnmounted(() => window.removeEventListener('keydown', handleShortcut))
```

- [ ] **Step 6: Run frontend tests to verify pass**

Run:

```bash
npm test -- src/components/__tests__/ContractQueryBot.spec.js src/components/layout/__tests__/ContractQueryEntry.spec.js
```

Expected:

- PASS for entry rendering, open behavior, shortcut open, export trigger

- [ ] **Step 7: Commit the frontend panel implementation**

```bash
git add frontend/src/api/contractSearch.js frontend/src/components/ContractQueryBot.vue frontend/src/components/layout/AppTopbarActions.vue frontend/src/components/layout/ContractQueryEntry.vue frontend/src/components/__tests__/ContractQueryBot.spec.js frontend/src/components/layout/__tests__/ContractQueryEntry.spec.js
git commit -m "feat: replace contract bot with query panel"
```

### Task 5: Implement drill-down routing and destination page hydration

**Files:**
- Modify: `frontend/src/components/ContractQueryBot.vue`
- Modify: `frontend/src/views/expenses/OrdinaryExpenseList.vue`
- Modify: `frontend/src/views/expenses/ZeroHourLaborList.vue`
- Modify: `frontend/src/views/contracts/DownstreamList.vue`
- Modify: `frontend/src/views/contracts/ManagementList.vue`

- [ ] **Step 1: Add explicit route helpers in the query panel**

```javascript
const openDownstreamDetails = (row) => {
  dialogVisible.value = false
  router.push({ path: '/contracts/downstream', query: { upstream_contract_id: String(row.id) } })
}

const openExpenseDetails = (row) => {
  dialogVisible.value = false
  router.push({ path: '/expenses', query: { tab: 'valuable', upstream_contract_id: String(row.id) } })
}
```

- [ ] **Step 2: Hydrate expense pages from route query on mount**

```javascript
if (route.query.upstream_contract_id) {
  queryParams.upstream_contract_id = parseInt(route.query.upstream_contract_id, 10)
}
```

- [ ] **Step 3: Extend the expense shell to honor tab query**

```javascript
const activeTab = ref(route.query.tab === 'zeroHourLabor' ? 'zeroHourLabor' : 'valuable')
watch(() => route.query.tab, (tab) => {
  activeTab.value = tab === 'zeroHourLabor' ? 'zeroHourLabor' : 'valuable'
})
```

- [ ] **Step 4: Run focused route behavior tests**

Run:

```bash
npm test -- src/components/__tests__/ContractQueryBot.spec.js src/views/expenses/__tests__/OrdinaryExpenseList.spec.js
```

Expected:

- PASS for drill-down navigation and upstream filter hydration

- [ ] **Step 5: Commit the drill-down integration**

```bash
git add frontend/src/components/ContractQueryBot.vue frontend/src/views/expenses/ExpenseList.vue frontend/src/views/expenses/OrdinaryExpenseList.vue frontend/src/views/expenses/ZeroHourLaborList.vue frontend/src/views/contracts/DownstreamList.vue frontend/src/views/contracts/ManagementList.vue
git commit -m "feat: add contract query drill-down navigation"
```

### Task 6: Final verification

**Files:**
- Verify only

- [ ] **Step 1: Run backend targeted verification**

```bash
pytest backend/tests/test_api_integration.py -k upstream_query -q
pytest backend/tests/test_contract_search_permissions.py -k upstream_aggregate -q
```

Expected:

- PASS

- [ ] **Step 2: Run frontend targeted verification**

```bash
npm test -- src/components/__tests__/ContractQueryBot.spec.js src/components/layout/__tests__/ContractQueryEntry.spec.js src/views/expenses/__tests__/OrdinaryExpenseList.spec.js
```

Expected:

- PASS

- [ ] **Step 3: Run production build verification**

```bash
cd frontend && npm run build
```

Expected:

- successful Vite production build

- [ ] **Step 4: Commit any final test or polish adjustments**

```bash
git add -A
git commit -m "chore: finalize contract query panel implementation"
```

## Self-Review

- Spec coverage:
  - top-right icon entry: Task 4
  - `Ctrl+K` / `Cmd+K`: Task 4
  - upstream-only filtered query table: Tasks 1-4
  - export: Tasks 1, 2, 4
  - drill-down cells: Tasks 3 and 5
  - consistent page styling: Task 4
  - destination list filters: Task 5
- Placeholder scan:
  - no TODO/TBD placeholders remain
- Type consistency:
  - backend endpoint names and frontend helper names are aligned around `upstream-query`
