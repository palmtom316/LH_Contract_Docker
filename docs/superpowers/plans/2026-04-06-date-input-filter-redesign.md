# Date Input Filter Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all start/end date filter pickers with user-entered date inputs that support fuzzy parsing, normalize successful entries, preserve invalid raw input with errors, and tighten filter bar layouts across all affected pages.

**Architecture:** Build a small date parsing utility, upgrade the single-date input component to separate display text from committed values, and reimplement the shared range field as a pair of text inputs with validation. Then migrate every affected filter surface to the shared range component and update the filter bar grid so date ranges render consistently across list pages, report cards, and the contract query assistant.

**Tech Stack:** Vue 3 SFCs, Element Plus, Vite, Vitest, Vue Test Utils, SCSS

---

## File Structure

- Modify: `frontend/src/components/SmartDateInput.vue`
  - Shared single-date text input used as the base for all filter date entry.
- Modify: `frontend/src/components/ui/AppRangeField.vue`
  - Shared date range field; convert from Element Plus date pickers to two text inputs.
- Modify: `frontend/src/components/ui/AppFilterBar.vue`
  - Shared filter layout container; adjust grid and responsive behavior for compact dual-input ranges.
- Modify: `frontend/src/components/ContractQueryBot.vue`
  - Replace query assistant daterange picker with the shared text-based range field.
- Modify: `frontend/src/views/contracts/ManagementList.vue`
  - Wire list filters to the new range field output and adjust filter placement.
- Modify: `frontend/src/views/contracts/DownstreamList.vue`
  - Same as management list.
- Modify: `frontend/src/views/contracts/UpstreamList.vue`
  - Same as management list, including any tab-specific query assembly.
- Modify: `frontend/src/views/expenses/OrdinaryExpenseList.vue`
  - Same as contract lists.
- Modify: `frontend/src/views/expenses/ZeroHourLaborList.vue`
  - Same as ordinary expense list.
- Modify: `frontend/src/views/audit/AuditLog.vue`
  - Same as other list pages.
- Modify: `frontend/src/views/reports/ReportDashboard.vue`
  - Keep month range support intact while swapping date-range export cards to text input ranges and updating card layout rules.
- Create: `frontend/src/utils/dateInput.ts`
  - Single source of truth for fuzzy date parsing, formatting, and validation helpers.
- Create: `frontend/src/utils/__tests__/dateInput.spec.ts`
  - Unit coverage for parser and formatter rules from the approved spec.
- Create: `frontend/src/components/__tests__/SmartDateInput.spec.js`
  - Component-level behavior coverage for parsing, formatting, and invalid input preservation.
- Create: `frontend/src/components/ui/__tests__/AppRangeField.spec.js`
  - Range-field behavior coverage for partial validity and range-order validation.

### Task 1: Add the fuzzy date parsing utility

**Files:**
- Create: `frontend/src/utils/dateInput.ts`
- Test: `frontend/src/utils/__tests__/dateInput.spec.ts`

- [ ] **Step 1: Write the failing parser tests**

```ts
import { describe, expect, it } from 'vitest'
import {
  formatDateInputDisplay,
  isValidDateParts,
  parseFlexibleDateInput
} from '@/utils/dateInput'

describe('parseFlexibleDateInput', () => {
  it('parses four-digit year with slash separators', () => {
    expect(parseFlexibleDateInput('2026/04/06')).toEqual({
      isoValue: '2026-04-06',
      displayValue: '2026/04/06',
      year: 2026,
      month: 4,
      day: 6
    })
  })

  it('parses two-digit year into 2000-2099', () => {
    expect(parseFlexibleDateInput('26/4/6')?.isoValue).toBe('2026-04-06')
  })

  it('normalizes mixed separators', () => {
    expect(parseFlexibleDateInput('2026。4-6')?.displayValue).toBe('2026/04/06')
  })

  it('rejects impossible calendar dates', () => {
    expect(parseFlexibleDateInput('2026/2/31')).toBeNull()
  })

  it('rejects incomplete values', () => {
    expect(parseFlexibleDateInput('2026/04')).toBeNull()
  })
})

describe('formatDateInputDisplay', () => {
  it('formats iso values for input display', () => {
    expect(formatDateInputDisplay('2026-04-06')).toBe('2026/04/06')
  })
})

describe('isValidDateParts', () => {
  it('accepts leap day in leap year', () => {
    expect(isValidDateParts(2028, 2, 29)).toBe(true)
  })

  it('rejects leap day in non-leap year', () => {
    expect(isValidDateParts(2027, 2, 29)).toBe(false)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/utils/__tests__/dateInput.spec.ts`
Expected: FAIL with module resolution error for `@/utils/dateInput` or missing exported functions.

- [ ] **Step 3: Write the minimal parser implementation**

```ts
export interface ParsedFlexibleDate {
  isoValue: string
  displayValue: string
  year: number
  month: number
  day: number
}

const FLEXIBLE_SEPARATOR_RE = /[.\-。]/g

export function normalizeFlexibleDateInput(raw: string): string {
  return raw.trim().replace(/\s+/g, '').replace(FLEXIBLE_SEPARATOR_RE, '/')
}

export function isValidDateParts(year: number, month: number, day: number): boolean {
  if (!Number.isInteger(year) || !Number.isInteger(month) || !Number.isInteger(day)) return false
  if (month < 1 || month > 12 || day < 1) return false

  const candidate = new Date(year, month - 1, day)
  return (
    candidate.getFullYear() === year &&
    candidate.getMonth() === month - 1 &&
    candidate.getDate() === day
  )
}

export function formatDateInputDisplay(isoValue?: string | null): string {
  if (!isoValue) return ''
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoValue.trim())
  if (!match) return ''
  return `${match[1]}/${match[2]}/${match[3]}`
}

export function parseFlexibleDateInput(raw?: string | null): ParsedFlexibleDate | null {
  if (!raw) return null

  const normalized = normalizeFlexibleDateInput(raw)
  const match = /^(\d{2}|\d{4})\/(\d{1,2})\/(\d{1,2})$/.exec(normalized)
  if (!match) return null

  const year = match[1].length === 2 ? 2000 + Number(match[1]) : Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])

  if (!isValidDateParts(year, month, day)) return null

  const yyyy = String(year).padStart(4, '0')
  const mm = String(month).padStart(2, '0')
  const dd = String(day).padStart(2, '0')

  return {
    isoValue: `${yyyy}-${mm}-${dd}`,
    displayValue: `${yyyy}/${mm}/${dd}`,
    year,
    month,
    day
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/utils/__tests__/dateInput.spec.ts`
Expected: PASS with the new parser tests green.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/dateInput.ts frontend/src/utils/__tests__/dateInput.spec.ts
git commit -m "feat: add flexible date input parser"
```

### Task 2: Upgrade `SmartDateInput` to preserve invalid raw text and commit normalized values

**Files:**
- Modify: `frontend/src/components/SmartDateInput.vue`
- Test: `frontend/src/components/__tests__/SmartDateInput.spec.js`

- [ ] **Step 1: Write the failing component tests**

```js
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import SmartDateInput from '@/components/SmartDateInput.vue'

describe('SmartDateInput', () => {
  it('formats valid input on blur and emits iso date', async () => {
    const wrapper = mount(SmartDateInput, { props: { modelValue: '' } })
    await wrapper.find('input').setValue('26.4.6')
    await wrapper.find('input').trigger('blur')

    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['2026-04-06'])
    expect(wrapper.find('input').element.value).toBe('2026/04/06')
  })

  it('preserves invalid input and reports error state', async () => {
    const wrapper = mount(SmartDateInput, { props: { modelValue: '2026-04-01' } })
    await wrapper.find('input').setValue('2026/2/31')
    await wrapper.find('input').trigger('blur')

    expect(wrapper.emitted('update:modelValue')).toBeFalsy()
    expect(wrapper.find('input').element.value).toBe('2026/2/31')
    expect(wrapper.text()).toContain('日期格式无法识别')
  })

  it('clears the committed value when the field is emptied', async () => {
    const wrapper = mount(SmartDateInput, { props: { modelValue: '2026-04-06' } })
    await wrapper.find('input').setValue('')
    await wrapper.find('input').trigger('blur')

    expect(wrapper.emitted('update:modelValue')[0]).toEqual([null])
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/components/__tests__/SmartDateInput.spec.js`
Expected: FAIL because the current component emits old formatting behavior and has no visible error handling.

- [ ] **Step 3: Implement the upgraded component**

```vue
<script setup>
import { computed, ref, watch } from 'vue'
import { Calendar } from '@element-plus/icons-vue'
import { formatDateInputDisplay, parseFlexibleDateInput } from '@/utils/dateInput'

const props = defineProps({
  modelValue: {
    type: String,
    default: null
  },
  placeholder: {
    type: String,
    default: '请输入日期'
  }
})

const emit = defineEmits(['update:modelValue', 'validity-change'])

const displayValue = ref(formatDateInputDisplay(props.modelValue))
const errorMessage = ref('')

watch(
  () => props.modelValue,
  (value) => {
    if (!errorMessage.value) {
      displayValue.value = formatDateInputDisplay(value)
    }
  }
)

const hasError = computed(() => Boolean(errorMessage.value))

function commitInput() {
  const raw = displayValue.value?.trim() ?? ''

  if (!raw) {
    errorMessage.value = ''
    emit('update:modelValue', null)
    emit('validity-change', { valid: true, value: null })
    return
  }

  const parsed = parseFlexibleDateInput(raw)
  if (!parsed) {
    errorMessage.value = '日期格式无法识别，请输入如 2026/04/06'
    emit('validity-change', { valid: false, value: null, raw })
    return
  }

  errorMessage.value = ''
  displayValue.value = parsed.displayValue
  emit('update:modelValue', parsed.isoValue)
  emit('validity-change', { valid: true, value: parsed.isoValue, raw: parsed.displayValue })
}
<\/script>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/components/__tests__/SmartDateInput.spec.js`
Expected: PASS with valid formatting, invalid preservation, and clear behavior working.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/SmartDateInput.vue frontend/src/components/__tests__/SmartDateInput.spec.js
git commit -m "feat: upgrade smart date input behavior"
```

### Task 3: Rebuild `AppRangeField` around two `SmartDateInput` instances

**Files:**
- Modify: `frontend/src/components/ui/AppRangeField.vue`
- Test: `frontend/src/components/ui/__tests__/AppRangeField.spec.js`

- [ ] **Step 1: Write the failing range-field tests**

```js
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AppRangeField from '@/components/ui/AppRangeField.vue'

describe('AppRangeField', () => {
  it('emits a normalized range when both dates are valid', async () => {
    const wrapper = mount(AppRangeField, { props: { modelValue: [] } })
    const inputs = wrapper.findAll('input')

    await inputs[0].setValue('26/4/1')
    await inputs[0].trigger('blur')
    await inputs[1].setValue('26/4/6')
    await inputs[1].trigger('blur')

    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([['2026-04-01', '2026-04-06']])
  })

  it('keeps a partial range when only one side is valid', async () => {
    const wrapper = mount(AppRangeField, { props: { modelValue: [] } })
    const inputs = wrapper.findAll('input')

    await inputs[0].setValue('2026/04/01')
    await inputs[0].trigger('blur')
    await inputs[1].setValue('2026/2/31')
    await inputs[1].trigger('blur')

    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([['2026-04-01', '']])
  })

  it('shows range-order error and blocks the range when start is after end', async () => {
    const wrapper = mount(AppRangeField, { props: { modelValue: [] } })
    const inputs = wrapper.findAll('input')

    await inputs[0].setValue('2026/04/08')
    await inputs[0].trigger('blur')
    await inputs[1].setValue('2026/04/06')
    await inputs[1].trigger('blur')

    expect(wrapper.text()).toContain('开始日期不能晚于结束日期')
    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([['', '']])
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/components/ui/__tests__/AppRangeField.spec.js`
Expected: FAIL because `AppRangeField` currently renders Element Plus date pickers and does not preserve partial validity or surface order errors.

- [ ] **Step 3: Implement the new shared range field**

```vue
<script setup>
import { computed, ref, watch } from 'vue'
import { Calendar } from '@element-plus/icons-vue'
import SmartDateInput from '@/components/SmartDateInput.vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  startPlaceholder: {
    type: String,
    default: '开始日期'
  },
  endPlaceholder: {
    type: String,
    default: '结束日期'
  }
})

const emit = defineEmits(['update:modelValue'])

const startValue = ref(props.modelValue?.[0] || '')
const endValue = ref(props.modelValue?.[1] || '')
const startValid = ref(true)
const endValid = ref(true)
const rangeError = ref('')

watch(
  () => props.modelValue,
  (value) => {
    startValue.value = value?.[0] || ''
    endValue.value = value?.[1] || ''
  },
  { deep: true }
)

function emitRange() {
  if (!startValid.value || !endValid.value) {
    rangeError.value = ''
    emit('update:modelValue', [startValid.value ? startValue.value : '', endValid.value ? endValue.value : ''])
    return
  }

  if (startValue.value && endValue.value && startValue.value > endValue.value) {
    rangeError.value = '开始日期不能晚于结束日期'
    emit('update:modelValue', ['', ''])
    return
  }

  rangeError.value = ''
  emit('update:modelValue', [startValue.value || '', endValue.value || ''])
}
<\/script>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- src/components/ui/__tests__/AppRangeField.spec.js`
Expected: PASS with normalized ranges, partial ranges, and order validation.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/AppRangeField.vue frontend/src/components/ui/__tests__/AppRangeField.spec.js
git commit -m "feat: rebuild date range field for text input"
```

### Task 4: Update the shared filter bar layout for the new range field

**Files:**
- Modify: `frontend/src/components/ui/AppFilterBar.vue`

- [ ] **Step 1: Add a focused snapshot/assertion target before CSS changes**

```js
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AppFilterBar from '@/components/ui/AppFilterBar.vue'

describe('AppFilterBar', () => {
  it('renders inline actions after filter controls', () => {
    const wrapper = mount(AppFilterBar, {
      props: { inlineActions: true },
      slots: {
        default: '<div class="filter-control--search">keyword</div><div class="filter-control--time">range</div>',
        actions: '<button>查询</button>'
      }
    })

    expect(wrapper.find('.app-filter-bar__actions--inline').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: Run test to verify current baseline**

Run: `cd frontend && npm test -- src/components/ui/__tests__/AppFilterBar.spec.js`
Expected: PASS or create the test file first if missing; this guards against accidental structural regressions while changing layout rules.

- [ ] **Step 3: Adjust the grid and range-specific CSS**

```scss
.app-filter-bar__main :deep(.filter-control--time) {
  grid-column: span 4;
  width: 100%;
  justify-self: stretch;
}

.app-filter-bar__main :deep(.filter-control--range-wide) {
  grid-column: span 5;
}

.app-filter-bar__main :deep(.app-range-field) {
  min-height: 44px;
}

@media (max-width: 900px) {
  .app-filter-bar__main :deep(.filter-control--time),
  .app-filter-bar__main :deep(.filter-control--range-wide) {
    grid-column: 1 / -1;
  }
}
```

- [ ] **Step 4: Run the filter bar test and a quick targeted component suite**

Run: `cd frontend && npm test -- src/components/ui/__tests__/AppFilterBar.spec.js src/components/ui/__tests__/AppRangeField.spec.js`
Expected: PASS with layout structure still intact.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/AppFilterBar.vue frontend/src/components/ui/__tests__/AppFilterBar.spec.js
git commit -m "style: refine shared filter bar layout"
```

### Task 5: Migrate all list filters to the shared text-based range field

**Files:**
- Modify: `frontend/src/views/contracts/ManagementList.vue`
- Modify: `frontend/src/views/contracts/DownstreamList.vue`
- Modify: `frontend/src/views/contracts/UpstreamList.vue`
- Modify: `frontend/src/views/expenses/OrdinaryExpenseList.vue`
- Modify: `frontend/src/views/expenses/ZeroHourLaborList.vue`
- Modify: `frontend/src/views/audit/AuditLog.vue`

- [ ] **Step 1: Write one representative failing integration test or composable-level assertion**

```js
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import ManagementList from '@/views/contracts/ManagementList.vue'

vi.mock('@/api/contractManagement', () => ({
  getContractManagementList: vi.fn(() => Promise.resolve({ items: [], total: 0 }))
}))

describe('ManagementList filters', () => {
  it('sends normalized start and end date values', async () => {
    const wrapper = mount(ManagementList)
    const inputs = wrapper.findAll('.filter-control--time input')

    await inputs[0].setValue('26/4/1')
    await inputs[0].trigger('blur')
    await inputs[1].setValue('26/4/6')
    await inputs[1].trigger('blur')
    await wrapper.find('button').trigger('click')

    expect(getContractManagementList).toHaveBeenCalledWith(
      expect.objectContaining({ start_date: '2026-04-01', end_date: '2026-04-06' })
    )
  })
})
```

- [ ] **Step 2: Run the representative test to verify it fails**

Run: `cd frontend && npm test -- src/views/contracts/__tests__/ManagementList.filters.spec.js`
Expected: FAIL until the page consumes the new normalized range behavior.

- [ ] **Step 3: Apply the page-level wiring changes consistently**

```vue
<AppFilterBar inline-actions>
  <el-input v-model="queryParams.keyword" class="filter-control--search" placeholder="合同序号/编号/名称/乙方" clearable @keyup.enter="handleQuery" />
  <AppRangeField
    v-model="dateRange"
    class="filter-control--time"
    start-placeholder="开始日期"
    end-placeholder="结束日期"
  />
  <el-select v-model="queryParams.status" placeholder="合同状态" clearable />
  <DictSelect v-model="queryParams.category" category="management_contract_category" placeholder="合同分类" clearable />
  <template #actions>
    <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
    <el-button icon="Refresh" @click="resetQuery">重置</el-button>
  </template>
</AppFilterBar>

function applyDateRange(queryParams, dateRange) {
  queryParams.start_date = dateRange?.[0] || undefined
  queryParams.end_date = dateRange?.[1] || undefined
}
```

- [ ] **Step 4: Run the representative test plus the existing relevant frontend suite**

Run: `cd frontend && npm test -- src/views/contracts/__tests__/ManagementList.filters.spec.js src/components/__tests__/SmartDateInput.spec.js src/components/ui/__tests__/AppRangeField.spec.js`
Expected: PASS, and manually verify that each migrated page still assembles API params from `dateRange`.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/contracts/ManagementList.vue frontend/src/views/contracts/DownstreamList.vue frontend/src/views/contracts/UpstreamList.vue frontend/src/views/expenses/OrdinaryExpenseList.vue frontend/src/views/expenses/ZeroHourLaborList.vue frontend/src/views/audit/AuditLog.vue
git commit -m "feat: migrate list filters to text date ranges"
```

### Task 6: Migrate the report dashboard export cards and month range safely

**Files:**
- Modify: `frontend/src/views/reports/ReportDashboard.vue`

- [ ] **Step 1: Write failing tests for report export parameter assembly**

```js
import { describe, expect, it } from 'vitest'
import { buildExportParams } from '@/views/reports/reportDashboard.helpers'

describe('buildExportParams', () => {
  it('includes normalized date range and status when valid', () => {
    expect(buildExportParams({ dateRange: ['2026-04-01', '2026-04-06'], status: '执行中' })).toEqual({
      start_date: '2026-04-01',
      end_date: '2026-04-06',
      status: '执行中'
    })
  })

  it('omits empty dates', () => {
    expect(buildExportParams({ dateRange: ['', ''], status: '全部' })).toEqual({})
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/views/reports/__tests__/reportDashboard.helpers.spec.js`
Expected: FAIL because the helper does not exist yet.

- [ ] **Step 3: Extract export-param assembly and update the card layout**

```js
export function buildExportParams(filters) {
  const params = {}

  if (filters.dateRange?.[0] && filters.dateRange?.[1]) {
    params.start_date = filters.dateRange[0]
    params.end_date = filters.dateRange[1]
  }

  if (filters.status && filters.status !== '全部') {
    params.status = filters.status
  }

  return params
}
```

```vue
<AppFilterBar class="report-export-card__filters" :class="`report-export-card__filters--${card.type}`">
  <AppRangeField
    v-if="card.type === 'daterange'"
    v-model="card.model.value"
    class="filter-control--range-wide"
    start-placeholder="开始日期"
    end-placeholder="结束日期"
  />
  <template v-else-if="card.type === 'daterange-with-status'">
    <AppRangeField
      v-model="exportFilters.dateRange"
      class="filter-control--range-wide"
      start-placeholder="开始日期"
      end-placeholder="结束日期"
    />
    <el-select v-model="exportFilters.status" placeholder="合同状态" />
  </template>
</AppFilterBar>
```

- [ ] **Step 4: Run the helper test and the report page component tests**

Run: `cd frontend && npm test -- src/views/reports/__tests__/reportDashboard.helpers.spec.js src/components/ui/__tests__/AppRangeField.spec.js`
Expected: PASS, with export params only including valid normalized values.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/reports/ReportDashboard.vue frontend/src/views/reports/__tests__/reportDashboard.helpers.spec.js
git commit -m "feat: migrate report export filters to text date ranges"
```

### Task 7: Replace the contract query assistant date picker and refresh guidance text

**Files:**
- Modify: `frontend/src/components/ContractQueryBot.vue`

- [ ] **Step 1: Write the failing query assistant test**

```js
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ContractQueryBot from '@/components/ContractQueryBot.vue'

describe('ContractQueryBot', () => {
  it('renders text date range inputs instead of a date picker', async () => {
    const wrapper = mount(ContractQueryBot)
    await wrapper.find('.bot-button').trigger('click')

    expect(wrapper.findComponent({ name: 'AppRangeField' }).exists()).toBe(true)
    expect(wrapper.html()).not.toContain('el-date-picker')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- src/components/__tests__/ContractQueryBot.spec.js`
Expected: FAIL because the component still renders `el-date-picker`.

- [ ] **Step 3: Replace the picker with the shared range field**

```vue
<div class="input-row">
  <AppRangeField
    v-model="signDateRange"
    class="sign-date-input"
    start-placeholder="签约开始日期"
    end-placeholder="签约结束日期"
  />
</div>

<p>签约时间范围支持输入如 2026/04/06、26.4.6、2026-4-6。</p>
```

- [ ] **Step 4: Run the query assistant test**

Run: `cd frontend && npm test -- src/components/__tests__/ContractQueryBot.spec.js`
Expected: PASS with the shared range field rendered and guidance text updated.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ContractQueryBot.vue frontend/src/components/__tests__/ContractQueryBot.spec.js
git commit -m "feat: update query bot date filters"
```

### Task 8: Run full verification and document any gaps

**Files:**
- Modify: `frontend/src/components/SmartDateInput.vue`
- Modify: `frontend/src/components/ui/AppRangeField.vue`
- Modify: `frontend/src/components/ui/AppFilterBar.vue`
- Modify: `frontend/src/components/ContractQueryBot.vue`
- Modify: `frontend/src/views/contracts/ManagementList.vue`
- Modify: `frontend/src/views/contracts/DownstreamList.vue`
- Modify: `frontend/src/views/contracts/UpstreamList.vue`
- Modify: `frontend/src/views/expenses/OrdinaryExpenseList.vue`
- Modify: `frontend/src/views/expenses/ZeroHourLaborList.vue`
- Modify: `frontend/src/views/audit/AuditLog.vue`
- Modify: `frontend/src/views/reports/ReportDashboard.vue`
- Test: `frontend/src/utils/__tests__/dateInput.spec.ts`
- Test: `frontend/src/components/__tests__/SmartDateInput.spec.js`
- Test: `frontend/src/components/ui/__tests__/AppRangeField.spec.js`

- [ ] **Step 1: Run the targeted automated suite**

Run: `cd frontend && npm test -- src/utils/__tests__/dateInput.spec.ts src/components/__tests__/SmartDateInput.spec.js src/components/ui/__tests__/AppRangeField.spec.js src/components/__tests__/ContractQueryBot.spec.js src/views/reports/__tests__/reportDashboard.helpers.spec.js`
Expected: PASS for parser, single input, range field, query assistant, and report export helpers.

- [ ] **Step 2: Run lint on the changed frontend files**

Run: `cd frontend && npm run lint`
Expected: PASS with no new lint errors in the modified files.

- [ ] **Step 3: Run a production build**

Run: `cd frontend && npm run build`
Expected: PASS and generate the Vite production bundle without component compile errors.

- [ ] **Step 4: Perform manual browser verification**

```text
1. Open each affected page.
2. Enter 2026/04/06, 26/4/6, 26.4.6, 2026.04.06, 26。4。6, 2026-4-6, 26-4-6.
3. Confirm the field reformats to YYYY/MM/DD after blur or Enter.
4. Enter 2026/2/31 and confirm raw text remains, error appears, and the invalid side is not applied.
5. Enter a start date later than the end date and confirm the range shows an error and does not filter.
6. Check desktop and narrow widths for all affected filter bars and report cards.
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/dateInput.ts frontend/src/utils/__tests__/dateInput.spec.ts frontend/src/components/SmartDateInput.vue frontend/src/components/__tests__/SmartDateInput.spec.js frontend/src/components/ui/AppRangeField.vue frontend/src/components/ui/__tests__/AppRangeField.spec.js frontend/src/components/ui/AppFilterBar.vue frontend/src/components/ui/__tests__/AppFilterBar.spec.js frontend/src/components/ContractQueryBot.vue frontend/src/components/__tests__/ContractQueryBot.spec.js frontend/src/views/contracts/ManagementList.vue frontend/src/views/contracts/DownstreamList.vue frontend/src/views/contracts/UpstreamList.vue frontend/src/views/expenses/OrdinaryExpenseList.vue frontend/src/views/expenses/ZeroHourLaborList.vue frontend/src/views/audit/AuditLog.vue frontend/src/views/reports/ReportDashboard.vue frontend/src/views/reports/__tests__/reportDashboard.helpers.spec.js
git commit -m "feat: redesign date filter inputs and layouts"
```

## Self-Review

- Spec coverage check:
  - Pure text start/end filters: covered by Tasks 2, 3, 5, 6, 7.
  - Supported fuzzy formats and normalization: covered by Task 1 and verified again in Task 8.
  - Invalid raw input preserved with error: covered by Tasks 2, 3, 8.
  - Range order validation: covered by Task 3 and Task 8.
  - Filter bar layout cleanup across pages: covered by Tasks 4, 5, 6, 7, 8.
- Placeholder scan:
  - No `TODO`, `TBD`, or “similar to” shortcuts remain.
- Type consistency:
  - Committed values are consistently `YYYY-MM-DD` strings.
  - Display values are consistently `YYYY/MM/DD`.
  - Shared range values remain `[start, end]` arrays to minimize page churn.
