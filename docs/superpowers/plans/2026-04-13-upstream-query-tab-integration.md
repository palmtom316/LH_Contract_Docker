# Upstream Query Tab Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move upstream contract query into the existing `上游合同` tab set, remove the global topbar entry and `Ctrl/Cmd + K` flow, and preserve the existing query/export/drill-down behavior.

**Architecture:** Reuse the existing `ContractQueryBot.vue` file as an embedded query workspace component instead of a dialog. Integrate it as a new `上游合同查询` tab in `UpstreamList.vue`, keep tab state in a lightweight `route.query.tab`, and remove the now-dead topbar trigger chain from `AppTopbarActions.vue`, `Layout.vue`, and `ContractQueryEntry.vue`.

**Tech Stack:** Vue 3 `<script setup>`, Vue Router 4, Element Plus, Vitest, existing workspace UI components

---

## File Map

### Frontend application files

- Modify: `frontend/src/components/ContractQueryBot.vue`
  - convert from dialog-driven component to embedded query workspace component
- Modify: `frontend/src/views/contracts/UpstreamList.vue`
  - add `上游合同查询` tab after the default tab
  - render embedded query component only when the query tab is active
  - sync active tab with `route.query.tab`
- Modify: `frontend/src/views/contracts/UpstreamDetail.vue`
  - preserve `tab=query` when returning from detail back to upstream list
- Modify: `frontend/src/components/layout/AppTopbarActions.vue`
  - remove contract query trigger and emit contract
- Modify: `frontend/src/views/Layout.vue`
  - remove global query dialog state, component mount, and event wiring
- Delete: `frontend/src/components/layout/ContractQueryEntry.vue`
  - no longer needed after removing topbar entry

### Test files

- Modify: `frontend/src/components/__tests__/ContractQueryBot.spec.js`
  - rewrite around embedded query panel behavior instead of `modelValue` dialog behavior
- Modify: `frontend/src/views/contracts/__tests__/UpstreamList.spec.js`
  - verify new tab order and `route.query.tab` hydration
- Modify: `frontend/src/views/contracts/__tests__/ContractDetailWorkspace.spec.js`
  - verify upstream detail preserves `tab=query` in the back-navigation URL
- Modify: `frontend/src/views/__tests__/LayoutTopbarActions.spec.js`
  - assert the global query trigger and dialog wiring are gone
- Delete: `frontend/src/components/layout/__tests__/ContractQueryEntry.spec.js`
  - obsolete with deleted component

---

### Task 1: Write the failing tab-integration regression tests

**Files:**
- Modify: `frontend/src/components/__tests__/ContractQueryBot.spec.js`
- Modify: `frontend/src/views/contracts/__tests__/UpstreamList.spec.js`
- Modify: `frontend/src/views/contracts/__tests__/ContractDetailWorkspace.spec.js`
- Modify: `frontend/src/views/__tests__/LayoutTopbarActions.spec.js`

- [ ] **Step 1: Rewrite the query component test around embedded behavior**

Replace the mount helper in `frontend/src/components/__tests__/ContractQueryBot.spec.js` so the component is mounted without a `modelValue` prop and loads immediately on mount:

```js
const createWrapper = () =>
  mount(ContractQueryBot, {
    global: {
      stubs: {
        'el-input': ElInputStub,
        'el-button': ElButtonStub,
        'el-pagination': ElPaginationStub,
        'el-icon': true,
        'el-tooltip': true,
        'el-tag': true,
        AppWorkspacePanel: slotStub('AppWorkspacePanel'),
        AppSectionCard: slotStub('AppSectionCard'),
        AppFilterBar: slotStub('AppFilterBar'),
        AppDataTable: slotStub('AppDataTable'),
        AppEmptyState: slotStub('AppEmptyState'),
        DictSelect: DictSelectStub,
        AppRangeField: AppRangeFieldStub
      }
    }
  })

it('loads upstream aggregate rows when the panel mounts', async () => {
  createWrapper()
  await flushPromises()

  expect(queryUpstreamContracts).toHaveBeenCalledWith({
    keyword: '',
    partyAName: '',
    contractCategory: '',
    companyCategory: '',
    signDateStart: '',
    signDateEnd: '',
    page: 1,
    pageSize: 20
  })
})
```

- [ ] **Step 2: Add upstream-tab and route-query expectations**

Extend `frontend/src/views/contracts/__tests__/UpstreamList.spec.js` to assert the new tab order and `tab=query` hydration:

```js
it('renders the query tab immediately after the default upstream tab', () => {
  const wrapper = mountPage()
  const labels = wrapper.findAll('.tab-label').map(node => node.text())

  expect(labels.slice(0, 3)).toEqual(['合同管理', '上游合同查询', '上游合同基本信息'])
})

it('hydrates the active tab from route query', async () => {
  routeMock.query = { tab: 'query' }
  const wrapper = mountPage()
  await wrapper.vm.$nextTick()

  expect(wrapper.vm.activeTab).toBe('query')
})
```

- [ ] **Step 3: Add detail and layout cleanup assertions**

Update `frontend/src/views/contracts/__tests__/ContractDetailWorkspace.spec.js` and `frontend/src/views/__tests__/LayoutTopbarActions.spec.js` with direct assertions for the new route/query behavior and removed topbar flow:

```js
it('preserves tab=query in upstream detail back-navigation source', () => {
  expect(detailSources[0]).toContain("if (query.tab) params.append('tab', query.tab)")
})

it('removes the global contract query trigger and dialog wiring', () => {
  expect(topbarActionsSource).not.toContain('ContractQueryEntry')
  expect(topbarActionsSource).not.toContain('open-contract-query')
  expect(layoutSource).not.toContain('ContractQueryBot')
  expect(layoutSource).not.toContain('contractQueryVisible')
  expect(layoutSource).not.toContain('openContractQuery')
})
```

- [ ] **Step 4: Run the focused frontend tests to confirm they fail**

Run:

```bash
cd frontend
npm test -- src/components/__tests__/ContractQueryBot.spec.js src/views/contracts/__tests__/UpstreamList.spec.js src/views/contracts/__tests__/ContractDetailWorkspace.spec.js src/views/__tests__/LayoutTopbarActions.spec.js
```

Expected:

- `ContractQueryBot.spec.js` fails because the component still requires dialog state
- `UpstreamList.spec.js` fails because the query tab does not exist yet
- `ContractDetailWorkspace.spec.js` fails because `tab=query` is not preserved
- `LayoutTopbarActions.spec.js` fails because the topbar trigger and dialog wiring still exist

- [ ] **Step 5: Commit the red tests**

```bash
git add frontend/src/components/__tests__/ContractQueryBot.spec.js frontend/src/views/contracts/__tests__/UpstreamList.spec.js frontend/src/views/contracts/__tests__/ContractDetailWorkspace.spec.js frontend/src/views/__tests__/LayoutTopbarActions.spec.js
git commit -m "test: cover upstream query tab integration"
```

### Task 2: Convert `ContractQueryBot` into an embedded query workspace

**Files:**
- Modify: `frontend/src/components/ContractQueryBot.vue`
- Test: `frontend/src/components/__tests__/ContractQueryBot.spec.js`

- [ ] **Step 1: Remove the dialog wrapper and `v-model` contract**

Replace the template root in `frontend/src/components/ContractQueryBot.vue` with an embedded workspace shell:

```vue
<template>
  <div class="contract-query-panel">
    <AppWorkspacePanel panel-class="contract-query-panel__workspace">
      <AppSectionCard class="contract-query-panel__section">
        <template #header>动态筛选</template>
        <template #actions>
          <button
            data-testid="contract-query-export"
            type="button"
            class="contract-query-panel__action-button"
            :disabled="exportLoading || !total"
            @click="handleExport"
          >
            {{ exportLoading ? '导出中...' : '导出 Excel' }}
          </button>
          <button type="button" class="contract-query-panel__action-button" @click="resetFilters">重置</button>
        </template>
        <AppFilterBar inline-actions>
          <el-input
            v-model="keyword"
            data-testid="contract-query-keyword"
            class="filter-control--search contract-query-panel__keyword"
            placeholder="合同名称 / 合同编号 / 合同序号"
            clearable
          />
          <el-input
            v-model="partyAName"
            data-testid="contract-query-party-a"
            class="filter-control--wide contract-query-panel__party-a"
            placeholder="甲方单位"
            clearable
          />
          <DictSelect v-model="contractCategory" category="contract_category" placeholder="合同类别" clearable />
          <DictSelect v-model="companyCategory" category="project_category" placeholder="合同公司分类" clearable />
          <AppRangeField
            v-model="signDateRange"
            class="filter-control--range-wide"
            start-placeholder="签约开始日期"
            end-placeholder="签约结束日期"
          />
          <template #actions>
            <div class="contract-query-panel__filter-tip">按输入与选择自动筛选，结果始终限定为上游合同。</div>
          </template>
        </AppFilterBar>
      </AppSectionCard>
      <AppSectionCard class="contract-query-panel__section">
        <template #header>筛选结果</template>
        <template #actions>
          <div class="contract-query-panel__stats">
            <span>{{ total }} 份上游合同</span>
            <span v-if="loading">刷新中...</span>
          </div>
        </template>
        <!-- Keep the existing AppEmptyState, table, and pagination markup unchanged here. -->
      </AppSectionCard>
    </AppWorkspacePanel>
  </div>
</template>
```

- [ ] **Step 2: Make loading and navigation panel-local instead of dialog-local**

Replace the dialog-specific script with mount-driven loading and direct navigation:

```js
import { onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const keyword = ref('')
const partyAName = ref('')
const contractCategory = ref('')
const companyCategory = ref('')
const signDateRange = ref([])
const rows = shallowRef([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const exportLoading = ref(false)
const hasLoaded = ref(false)
const errorMessage = ref('')

let refreshTimer = null

async function loadRows() {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await queryUpstreamContracts(buildQueryParams(true))
    rows.value = response.items || []
    total.value = response.total || 0
    hasLoaded.value = true
  } catch (error) {
    rows.value = []
    total.value = 0
    errorMessage.value = error?.response?.data?.detail || '请稍后重试或联系管理员'
  } finally {
    loading.value = false
  }
}

function openUpstreamDetail(row) {
  router.push({
    name: 'UpstreamDetail',
    params: { id: row.id },
    query: { tab: 'query' }
  })
}

function openRelatedList(type, row) {
  const upstreamContractId = String(row.id)
  const routeMap = {
    downstream: { path: '/contracts/downstream', query: { upstream_contract_id: upstreamContractId } },
    management: { path: '/contracts/management', query: { upstream_contract_id: upstreamContractId } },
    expense: { path: '/expenses', query: { tab: 'valuable', upstream_contract_id: upstreamContractId } },
    labor: { path: '/expenses', query: { tab: 'zeroHourLabor', upstream_contract_id: upstreamContractId } }
  }

  const target = routeMap[type]
  if (target) router.push(target)
}

watch(
  () => [keyword.value, partyAName.value, contractCategory.value, companyCategory.value, ...(Array.isArray(signDateRange.value) ? signDateRange.value : [])],
  () => {
    page.value = 1
    scheduleRefresh()
  }
)

onMounted(() => {
  loadRows()
})

onUnmounted(() => {
  clearRefreshTimer()
})
```

- [ ] **Step 3: Remove dead dialog-only styles and assertions**

Delete dialog/header/shortcut-specific styles from `frontend/src/components/ContractQueryBot.vue` and keep only the panel/table styles:

```scss
.contract-query-panel {
  min-width: 0;
}

.contract-query-panel__workspace,
.contract-query-panel__section {
  gap: 0;
}

.contract-query-panel__filter-tip,
.contract-query-panel__stats {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  color: hsl(var(--muted-foreground));
  font-size: 13px;
}

.contract-query-panel__pagination {
  display: flex;
  justify-content: flex-end;
}
```

- [ ] **Step 4: Run the query-panel test to verify it passes**

Run:

```bash
cd frontend
npm test -- src/components/__tests__/ContractQueryBot.spec.js
```

Expected:

- PASS for mount-driven loading
- PASS for debounced filter refresh
- PASS for downstream drill-down routing

- [ ] **Step 5: Commit the embedded query-panel refactor**

```bash
git add frontend/src/components/ContractQueryBot.vue frontend/src/components/__tests__/ContractQueryBot.spec.js
git commit -m "refactor: embed upstream query panel in page workspace"
```

### Task 3: Integrate the query panel into `UpstreamList` and preserve tab state

**Files:**
- Modify: `frontend/src/views/contracts/UpstreamList.vue`
- Modify: `frontend/src/views/contracts/UpstreamDetail.vue`
- Test: `frontend/src/views/contracts/__tests__/UpstreamList.spec.js`
- Test: `frontend/src/views/contracts/__tests__/ContractDetailWorkspace.spec.js`

- [ ] **Step 1: Add the `上游合同查询` tab after the default tab**

Insert a new tab pane immediately after the existing `合同管理` tab in `frontend/src/views/contracts/UpstreamList.vue`:

```vue
<el-tabs v-model="activeTab" class="contract-tabs app-tabs--line" @tab-change="handleTabChange">
  <el-tab-pane label="合同管理" name="management">
    <!-- existing management tab content -->
  </el-tab-pane>

  <el-tab-pane label="上游合同查询" name="query">
    <ContractQueryBot v-if="activeTab === 'query'" />
  </el-tab-pane>

  <el-tab-pane label="上游合同基本信息" name="basic_info">
    <!-- existing basic_info tab content -->
  </el-tab-pane>
</el-tabs>
```

- [ ] **Step 2: Add explicit tab constants and route-query synchronization**

Refactor the tab state logic in `frontend/src/views/contracts/UpstreamList.vue` so `tab=query` survives refresh and copy-paste, while list filters still reset only for list tabs:

```js
import { useRouter, useRoute } from 'vue-router'
import ContractQueryBot from '@/components/ContractQueryBot.vue'

const TAB_MANAGEMENT = 'management'
const TAB_QUERY = 'query'
const TAB_BASIC_INFO = 'basic_info'
const TAB_NAMES = new Set([TAB_MANAGEMENT, TAB_QUERY, TAB_BASIC_INFO])

const router = useRouter()
const route = useRoute()
const activeTab = ref(TAB_MANAGEMENT)

function getRouteTab() {
  const tab = typeof route.query.tab === 'string' ? route.query.tab : TAB_MANAGEMENT
  return TAB_NAMES.has(tab) ? tab : TAB_MANAGEMENT
}

function syncRouteTab(tab) {
  const nextQuery = { ...route.query }
  if (tab === TAB_MANAGEMENT) {
    delete nextQuery.tab
  } else {
    nextQuery.tab = tab
  }
  router.replace({ query: nextQuery })
}

const handleTabChange = (nextTab) => {
  syncRouteTab(nextTab)
  if (nextTab === TAB_QUERY) {
    activeTab.value = TAB_QUERY
    return
  }

  activeTab.value = nextTab
  queryParams.page = 1
  queryParams.keyword = ''
  queryParams.status = ''
  queryParams.company_category = ''
  queryParams.category = ''
  queryParams.management_mode = ''
  dateRange.value = []
  monthRange.value = []
  getList()
}

onMounted(() => {
  activeTab.value = getRouteTab()
  if (activeTab.value !== TAB_QUERY) {
    if (route.query.page) queryParams.page = parseInt(route.query.page, 10)
    if (route.query.keyword) queryParams.keyword = route.query.keyword
    if (route.query.status) queryParams.status = route.query.status
    getList()
  }
})
```

- [ ] **Step 3: Preserve `tab=query` when moving between list and detail**

Update the upstream detail navigation contract so query-tab users return to the query tab instead of the default tab:

```js
// frontend/src/views/contracts/UpstreamList.vue
const handleDetail = (row) => {
  router.push({
    name: 'UpstreamDetail',
    params: { id: row.id },
    query: {
      page: queryParams.page,
      keyword: queryParams.keyword || undefined,
      status: queryParams.status || undefined,
      tab: activeTab.value === TAB_QUERY ? TAB_QUERY : undefined
    }
  })
}

// frontend/src/views/contracts/UpstreamDetail.vue
const handleBack = () => {
  const query = route.query
  const params = new URLSearchParams()
  if (query.page) params.append('page', query.page)
  if (query.keyword) params.append('keyword', query.keyword)
  if (query.status) params.append('status', query.status)
  if (query.tab) params.append('tab', query.tab)
  const queryString = params.toString()
  location.href = '/contracts/upstream' + (queryString ? '?' + queryString : '')
}
```

- [ ] **Step 4: Run the upstream module tests to verify they pass**

Run:

```bash
cd frontend
npm test -- src/views/contracts/__tests__/UpstreamList.spec.js src/views/contracts/__tests__/ContractDetailWorkspace.spec.js
```

Expected:

- PASS for tab order
- PASS for `tab=query` hydration
- PASS for preserving `tab=query` through detail back-navigation

- [ ] **Step 5: Commit the tab integration**

```bash
git add frontend/src/views/contracts/UpstreamList.vue frontend/src/views/contracts/UpstreamDetail.vue frontend/src/views/contracts/__tests__/UpstreamList.spec.js frontend/src/views/contracts/__tests__/ContractDetailWorkspace.spec.js
git commit -m "feat: move upstream query into contract tabs"
```

### Task 4: Remove the global topbar entry and dead shortcut code

**Files:**
- Modify: `frontend/src/components/layout/AppTopbarActions.vue`
- Modify: `frontend/src/views/Layout.vue`
- Modify: `frontend/src/views/__tests__/LayoutTopbarActions.spec.js`
- Delete: `frontend/src/components/layout/ContractQueryEntry.vue`
- Delete: `frontend/src/components/layout/__tests__/ContractQueryEntry.spec.js`

- [ ] **Step 1: Remove the topbar query trigger component and emit contract**

Simplify `frontend/src/components/layout/AppTopbarActions.vue` to keep only theme toggle and notifications:

```vue
<template>
  <div class="topbar-actions">
    <AppThemeToggle />
    <AppNotificationBell :unread-count="unreadCount" />
  </div>
</template>

<script setup>
import AppNotificationBell from './AppNotificationBell.vue'
import AppThemeToggle from '@/components/ui/AppThemeToggle.vue'

defineProps({
  unreadCount: {
    type: Number,
    default: 0
  }
})
</script>
```

- [ ] **Step 2: Remove layout-level dialog state and mount points**

Delete the contract-query wiring from `frontend/src/views/Layout.vue`:

```vue
<header class="topbar">
  <div class="topbar-left">
    <!-- existing menu button and title -->
  </div>
  <AppTopbarActions :unread-count="unreadCount" />
</header>
```

```js
import AppTopbarActions from '@/components/layout/AppTopbarActions.vue'

const isCollapse = ref(false)
const systemVersion = ref(`Version ${pkg.version}`)
const changePwdVisible = ref(false)
const changingPwd = ref(false)
const pwdFormRef = ref(null)
```

Delete all of the following from the file:

```js
import ContractQueryBot from '@/components/ContractQueryBot.vue'
const contractQueryVisible = ref(false)
function openContractQuery() {
  contractQueryVisible.value = true
}
```

and remove the old mount:

```vue
<ContractQueryBot v-model="contractQueryVisible" />
```

- [ ] **Step 3: Delete the dead trigger component and lock in regression checks**

Remove the obsolete files and tighten the source-level test:

```bash
git rm frontend/src/components/layout/ContractQueryEntry.vue frontend/src/components/layout/__tests__/ContractQueryEntry.spec.js
```

```js
it('removes the global contract query trigger and dialog wiring', () => {
  expect(topbarActionsSource).not.toContain('ContractQueryEntry')
  expect(topbarActionsSource).not.toContain('defineEmits')
  expect(layoutSource).not.toContain('ContractQueryBot')
  expect(layoutSource).not.toContain('contractQueryVisible')
  expect(layoutSource).not.toContain('openContractQuery')
  expect(layoutSource).not.toContain('open-contract-query')
})
```

- [ ] **Step 4: Run focused cleanup and build verification**

Run:

```bash
cd frontend
npm test -- src/views/__tests__/LayoutTopbarActions.spec.js src/components/__tests__/ContractQueryBot.spec.js src/views/contracts/__tests__/UpstreamList.spec.js src/views/contracts/__tests__/ContractDetailWorkspace.spec.js
npm run build
```

Expected:

- all targeted Vitest specs PASS
- Vite production build completes successfully

- [ ] **Step 5: Commit the global-entry removal**

```bash
git add frontend/src/components/layout/AppTopbarActions.vue frontend/src/views/Layout.vue frontend/src/views/__tests__/LayoutTopbarActions.spec.js
git commit -m "refactor: remove global upstream query entry"
```

## Self-Review

### Spec coverage

- `上游合同查询` becomes an in-module tab: covered by Task 3
- tab sits after the default tab: covered by Task 3 tests and template change
- topbar entry is removed: covered by Task 4
- `Ctrl/Cmd + K` flow disappears: covered by Task 4 via deleting `ContractQueryEntry.vue`
- existing query/export/drill-down behavior is preserved: covered by Task 2 tests and component refactor
- `tab=query` survives refresh and detail round-trip: covered by Task 3

### Placeholder scan

- no `TODO`, `TBD`, or deferred implementation notes remain
- every task lists exact files, code snippets, commands, and expected outcomes

### Type and naming consistency

- tab constant is consistently `query`
- existing component name stays `ContractQueryBot` to reduce churn
- route query key is consistently `tab`
