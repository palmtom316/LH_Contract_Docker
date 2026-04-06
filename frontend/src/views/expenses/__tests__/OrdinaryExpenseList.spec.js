import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { defineComponent } from 'vue'
import ExpenseList from '@/views/expenses/ExpenseList.vue'
import OrdinaryExpenseList from '@/views/expenses/OrdinaryExpenseList.vue'

const apiMocks = vi.hoisted(() => ({
  getExpenses: vi.fn(),
  getContracts: vi.fn(),
  getContract: vi.fn()
}))

vi.mock('@/api/expense', () => ({
  getExpenses: apiMocks.getExpenses,
  createExpense: vi.fn(),
  updateExpense: vi.fn(),
  deleteExpense: vi.fn(),
  exportExpenses: vi.fn()
}))

vi.mock('@/api/contractUpstream', () => ({
  getContracts: apiMocks.getContracts,
  getContract: apiMocks.getContract
}))

vi.mock('@/api/common', () => ({
  uploadFile: vi.fn()
}))

vi.mock('@/utils/common', () => ({
  getFileUrl: vi.fn(() => ''),
  formatMoney: vi.fn((value) => String(value))
}))

const ElDialogStub = defineComponent({
  props: ['modelValue'],
  template: '<div v-if="modelValue"><slot /></div>'
})

const ElInputStub = defineComponent({
  props: ['modelValue', 'placeholder'],
  emits: ['update:modelValue', 'keyup.enter'],
  template: '<input :value="modelValue" :placeholder="placeholder" @input="$emit(\'update:modelValue\', $event.target.value)" />'
})

const ElSelectStub = defineComponent({
  props: ['modelValue', 'placeholder', 'remote', 'remoteMethod'],
  emits: ['update:modelValue', 'change'],
  template: `
    <div class="el-select-stub" :data-placeholder="placeholder">
      <button
        v-if="remote && remoteMethod"
        class="remote-search"
        type="button"
        @click="remoteMethod('甲方单位')"
      >
        搜索
      </button>
      <button
        v-if="remote"
        class="remote-select"
        type="button"
        @click="$emit('update:modelValue', 9); $emit('change', 9)"
      >
        选择
      </button>
      <slot />
    </div>
  `
})

const ElButtonStub = defineComponent({
  emits: ['click'],
  template: '<button type="button" @click="$emit(\'click\')"><slot /></button>'
})

const ElTabsStub = defineComponent({
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: '<div class="el-tabs-stub"><slot /></div>'
})

const ElTabPaneStub = defineComponent({
  props: ['label', 'name'],
  template: '<div class="el-tab-pane-stub" :data-label="label" :data-name="name"><slot /></div>'
})

const mountPage = () =>
  mount(OrdinaryExpenseList, {
    global: {
      stubs: {
        AppSectionCard: { template: '<section><slot name="header" /><slot /><slot name="actions" /></section>' },
        AppFilterBar: { template: '<div><slot /><slot name="actions" /></div>' },
        AppDataTable: { template: '<div><slot /><slot name="footer" /></div>' },
        AppEmptyState: true,
        AppRangeField: true,
        DictSelect: true,
        SmartDateInput: true,
        FormulaInput: true,
        ElInput: ElInputStub,
        ElSelect: ElSelectStub,
        ElOption: true,
        ElButton: ElButtonStub,
        ElTable: true,
        ElTableColumn: true,
        ElPagination: true,
        ElDialog: ElDialogStub,
        ElForm: true,
        ElFormItem: true,
        ElInputNumber: true,
        ElTag: true,
        ElRow: true,
        ElCol: true,
        ElCard: true,
        ElDropdown: true,
        ElDropdownMenu: true,
        ElDropdownItem: true,
        ElUpload: true,
        ElTooltip: true,
        ElIcon: true
      }
    }
  })

const mountExpensePage = () =>
  mount(ExpenseList, {
    global: {
      stubs: {
        OrdinaryExpenseList: { template: '<div class="ordinary-expense-list-stub">ordinary</div>' },
        ZeroHourLaborList: { template: '<div class="zero-hour-labor-list-stub">labor</div>' },
        ElTabs: ElTabsStub,
        ElTabPane: ElTabPaneStub
      }
    }
  })

describe('ExpenseList workspace shell', () => {
  it('renders the expense page shell, header, and tab panel with page-specific naming', () => {
    const wrapper = mountExpensePage()

    expect(wrapper.find('.expense-page-shell').exists()).toBe(true)
    expect(wrapper.find('.expense-page-header').exists()).toBe(true)
    expect(wrapper.find('.expense-page-panel').exists()).toBe(true)
    expect(wrapper.find('.expense-overview').exists()).toBe(false)
    expect(wrapper.find('.expense-page-tabs').exists()).toBe(true)
    expect(wrapper.find('.el-tab-pane-stub[data-name="valuable"]').exists()).toBe(true)
    expect(wrapper.find('.el-tab-pane-stub[data-name="zeroHourLabor"]').exists()).toBe(true)
  })
})

describe('OrdinaryExpenseList upstream filter', () => {
  beforeEach(() => {
    apiMocks.getExpenses.mockReset()
    apiMocks.getContracts.mockReset()
    apiMocks.getContract.mockReset()
    apiMocks.getExpenses.mockResolvedValue({ items: [], total: 0 })
    apiMocks.getContracts.mockResolvedValue({
      items: [
        {
          id: 9,
          serial_number: 88,
          contract_code: 'UP-009',
          contract_name: '上游合同九',
          party_a_name: '甲方单位九'
        }
      ]
    })
  })

  it('renders ordinary expense page-specific workspace panels', () => {
    const wrapper = mountPage()

    expect(wrapper.find('.expense-list-page').exists()).toBe(true)
    expect(wrapper.findAll('.expense-list-panel')).toHaveLength(2)
    expect(wrapper.find('.expense-list-panel--filters').exists()).toBe(true)
    expect(wrapper.find('.expense-list-panel--results').exists()).toBe(true)
    expect(wrapper.text()).toContain('费用列表')
  })

  it('uses remote upstream search in the filter bar', async () => {
    const wrapper = mountPage()
    const selects = wrapper.findAllComponents(ElSelectStub)
    const filterSelect = selects.find((node) => node.props('placeholder')?.includes('上游合同'))

    expect(filterSelect).toBeTruthy()
    expect(filterSelect.props('placeholder')).toContain('上游合同')
    expect(typeof filterSelect.props('remoteMethod')).toBe('function')

    await filterSelect.props('remoteMethod')('甲方单位')

    expect(apiMocks.getContracts).toHaveBeenCalledWith({
      keyword: '甲方单位',
      page: 1,
      page_size: 20
    })
  })

  it('passes selected upstream contract id when querying the list', async () => {
    const wrapper = mountPage()
    apiMocks.getExpenses.mockClear()

    const selects = wrapper.findAllComponents(ElSelectStub)
    const filterSelect = selects.find((node) => node.props('placeholder')?.includes('上游合同'))

    filterSelect.vm.$emit('update:modelValue', 9)
    filterSelect.vm.$emit('change', 9)
    await wrapper.vm.handleQuery()

    expect(apiMocks.getExpenses).toHaveBeenCalledWith(
      expect.objectContaining({
        upstream_contract_id: 9
      })
    )
  })
})
