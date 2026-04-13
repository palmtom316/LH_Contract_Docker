import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import ContractQueryBot from '@/components/ContractQueryBot.vue'
import { exportUpstreamContractQuery, queryUpstreamContracts } from '@/api/contractSearch'

const push = vi.fn()

vi.mock('@/api/contractSearch', () => ({
  queryUpstreamContracts: vi.fn(() =>
    Promise.resolve({
      total: 1,
      page: 1,
      page_size: 20,
      items: [
        {
          id: 11,
          contract_name: '华东总包上游合同',
          party_a_name: '华东甲方',
          party_b_name: '我方公司',
          category: '施工合同',
          company_category: '市政工程',
          sign_date: '2026-04-03',
          contract_amount: 300000,
          receivable_amount: 180000,
          invoiced_amount: 120000,
          received_amount: 90000,
          settlement_amount: 150000,
          downstream_contract_count: 2,
          downstream_contract_amount: 80000,
          downstream_settlement_amount: 50000,
          downstream_paid_amount: 42000,
          management_contract_count: 1,
          management_contract_amount: 30000,
          management_settlement_amount: 18000,
          management_paid_amount: 16000,
          non_contract_expense_total: 12000,
          zero_hour_labor_total: 6000
        }
      ]
    })
  ),
  exportUpstreamContractQuery: vi.fn(() => Promise.resolve(new Blob(['xlsx'])))
}))

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    useRouter: () => ({ push })
  }
})

const ElInputStub = {
  name: 'ElInput',
  props: ['modelValue', 'placeholder'],
  emits: ['update:modelValue'],
  template: `
    <input
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  `
}

const ElPaginationStub = {
  name: 'ElPagination',
  template: '<div class="pagination-stub"></div>'
}

const DictSelectStub = {
  name: 'DictSelect',
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: `
    <select :value="modelValue" @change="$emit('update:modelValue', $event.target.value)">
      <option value="">全部</option>
      <option value="施工合同">施工合同</option>
      <option value="市政工程">市政工程</option>
    </select>
  `
}

const AppRangeFieldStub = {
  name: 'AppRangeField',
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: `
    <div>
      <button
        type="button"
        data-testid="range-trigger"
        @click="$emit('update:modelValue', ['2026-04-01', '2026-04-09'])"
      >
        range
      </button>
    </div>
  `
}

const slotStub = name => ({
  name,
  template: `
    <div class="${name}">
      <div class="${name}__header"><slot name="header" /></div>
      <div class="${name}__actions"><slot name="actions" /></div>
      <slot />
      <slot name="footer" />
    </div>
  `
})

const originalCreateElement = document.createElement.bind(document)

const createWrapper = () =>
  mount(ContractQueryBot, {
    global: {
      stubs: {
        'el-input': ElInputStub,
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

describe('ContractQueryBot', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
    if (!window.URL) {
      window.URL = {}
    }
    window.URL.createObjectURL = vi.fn(() => 'blob:contract-query-export')
    window.URL.revokeObjectURL = vi.fn()
    vi.spyOn(document, 'createElement').mockImplementation(tagName => {
      const element = originalCreateElement(tagName)
      if (tagName === 'a') {
        element.click = vi.fn()
      }
      return element
    })
  })

  afterEach(() => {
    vi.runOnlyPendingTimers()
    vi.useRealTimers()
    vi.restoreAllMocks()
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

  it('debounces filter changes and requeries with upstream-only filters', async () => {
    const wrapper = createWrapper()
    await flushPromises()
    queryUpstreamContracts.mockClear()

    const inputs = wrapper.findAll('input')
    await inputs[0].setValue('华东')
    await inputs[1].setValue('华东甲方')
    await wrapper.find('[data-testid="range-trigger"]').trigger('click')

    vi.advanceTimersByTime(260)
    await flushPromises()

    expect(queryUpstreamContracts).toHaveBeenCalledWith({
      keyword: '华东',
      partyAName: '华东甲方',
      contractCategory: '',
      companyCategory: '',
      signDateStart: '2026-04-01',
      signDateEnd: '2026-04-09',
      page: 1,
      pageSize: 20
    })
  })

  it('drills into downstream details from related metric cells', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    await wrapper.find('[data-testid="drilldown-downstream-count-11"]').trigger('click')

    expect(push).toHaveBeenCalledWith({
      path: '/contracts/downstream',
      query: {
        upstream_contract_id: '11'
      }
    })
  })

  it('exports the current upstream query result set', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    await wrapper.find('[data-testid="contract-query-export"]').trigger('click')

    expect(exportUpstreamContractQuery).toHaveBeenCalledWith({
      keyword: '',
      partyAName: '',
      contractCategory: '',
      companyCategory: '',
      signDateStart: '',
      signDateEnd: ''
    })
  })
})
