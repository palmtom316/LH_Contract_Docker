import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { defineComponent, reactive, ref } from 'vue'
import ManagementList from '@/views/contracts/ManagementList.vue'

const { getListMock, queryParamsState, getUpstreamContractsMock } = vi.hoisted(() => ({
  getListMock: vi.fn(),
  queryParamsState: { value: null },
  getUpstreamContractsMock: vi.fn()
}))

vi.mock('@/composables/useContractList', () => {
  if (!queryParamsState.value) {
    queryParamsState.value = reactive({
      page: 1,
      page_size: 10,
      keyword: '',
      status: '',
      start_date: undefined,
      end_date: undefined,
      category: undefined,
      upstream_contract_id: undefined
    })
  }
  return {
    useContractList: () => ({
      loading: ref(false),
      list: ref([]),
      total: ref(0),
      queryParams: queryParamsState.value,
      getList: getListMock,
      handleQuery: vi.fn(),
      resetQuery: vi.fn(),
      handleDelete: vi.fn(),
      handleExport: vi.fn(),
      formatMoney: (value) => String(value),
      getStatusType: () => 'success',
      getFileUrl: () => ''
    }),
    useTableSummary: () => ({
      getSummaries: vi.fn(),
      footerCellStyle: vi.fn()
    }),
    useMobileDetection: () => ({
      isMobile: ref(false),
      checkIsMobile: vi.fn()
    })
  }
})

vi.mock('vue-router', async () => {
  const actual = await vi.importActual('vue-router')
  return {
    ...actual,
    useRouter: () => ({ push: vi.fn() }),
    useRoute: () => ({ query: {} }),
    createRouter: () => ({
      push: vi.fn(),
      beforeEach: vi.fn(),
      afterEach: vi.fn()
    }),
    createWebHistory: () => ({})
  }
})

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({ canManageManagementContracts: false })
}))

vi.mock('@/api/contractManagement', () => ({
  getContracts: vi.fn(),
  createContract: vi.fn(),
  updateContract: vi.fn(),
  deleteContract: vi.fn(),
  exportContracts: vi.fn()
}))

vi.mock('@/api/contractUpstream', () => ({
  getContracts: getUpstreamContractsMock,
  getContractSummary: vi.fn()
}))

vi.mock('@/api/common', () => ({
  uploadFile: vi.fn()
}))

vi.mock('@/utils/common', () => ({
  getFileUrl: vi.fn(),
  formatMoney: vi.fn()
}))

vi.mock('@/utils/download', () => ({
  downloadExcel: vi.fn(),
  generateFilename: vi.fn()
}))

vi.mock('@/utils/request', () => ({
  default: vi.fn()
}))

const RangeFieldStub = defineComponent({
  emits: ['update:modelValue'],
  template: `
    <div>
      <button data-testid="range-full" @click="$emit('update:modelValue', ['2026-04-01', '2026-04-06'])"></button>
      <button data-testid="range-start" @click="$emit('update:modelValue', ['2026-04-01', ''])"></button>
      <button data-testid="range-end" @click="$emit('update:modelValue', ['', '2026-04-06'])"></button>
    </div>
  `
})

const ElDialogStub = defineComponent({
  props: ['modelValue'],
  template: '<div v-if="modelValue"><slot /></div>'
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
        @click="$emit('update:modelValue', 7); $emit('change', 7)"
      >
        选择
      </button>
      <slot />
    </div>
  `
})

const mountPage = () =>
  mount(ManagementList, {
    global: {
      stubs: {
        AppSectionCard: { template: '<section><slot name="header" /><slot /><slot name="actions" /></section>' },
        AppFilterBar: { template: '<div><slot /><slot name="actions" /></div>' },
        AppDataTable: { template: '<div><slot /><slot name="footer" /></div>' },
        AppEmptyState: true,
        AppRangeField: RangeFieldStub,
        DictSelect: true,
        SmartDateInput: true,
        ElInput: true,
        ElSelect: ElSelectStub,
        ElOption: true,
        ElButton: true,
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

describe('ManagementList date range query', () => {
  beforeEach(() => {
    queryParamsState.value.page = 1
    queryParamsState.value.page_size = 10
    queryParamsState.value.keyword = ''
    queryParamsState.value.status = ''
    queryParamsState.value.start_date = undefined
    queryParamsState.value.end_date = undefined
    queryParamsState.value.category = undefined
    queryParamsState.value.upstream_contract_id = undefined
    getListMock.mockClear()
    getUpstreamContractsMock.mockReset()
    getUpstreamContractsMock.mockResolvedValue({
      items: [
        {
          id: 7,
          serial_number: 12,
          contract_code: 'UP-007',
          contract_name: '上游合同七',
          party_a_name: '甲方单位七'
        }
      ]
    })
  })

  it('renders management-specific workspace shell wrappers', () => {
    const wrapper = mountPage()

    expect(wrapper.find('.management-page-shell').exists()).toBe(true)
    expect(wrapper.find('.management-page-header').exists()).toBe(true)
    expect(wrapper.find('.contract-page-shell').exists()).toBe(false)
    expect(wrapper.text()).toContain('管理合同')
    expect(wrapper.findAll('.management-page-panel')).toHaveLength(2)
    expect(wrapper.find('.management-page-panel--filters').exists()).toBe(true)
    expect(wrapper.find('.management-page-panel--list').exists()).toBe(true)
  })

  it('applies both range sides when provided', async () => {
    const wrapper = mountPage()
    await wrapper.find('[data-testid="range-full"]').trigger('click')

    await wrapper.vm.handleQuery()

    expect(wrapper.vm.queryParams.start_date).toBe('2026-04-01')
    expect(wrapper.vm.queryParams.end_date).toBe('2026-04-06')
    expect(getListMock).toHaveBeenCalled()
  })

  it('supports partial range values', async () => {
    const wrapper = mountPage()
    await wrapper.find('[data-testid="range-start"]').trigger('click')

    await wrapper.vm.handleQuery()

    expect(wrapper.vm.queryParams.start_date).toBe('2026-04-01')
    expect(wrapper.vm.queryParams.end_date).toBeUndefined()

    await wrapper.find('[data-testid="range-end"]').trigger('click')
    await wrapper.vm.handleQuery()

    expect(wrapper.vm.queryParams.start_date).toBeUndefined()
    expect(wrapper.vm.queryParams.end_date).toBe('2026-04-06')
  })

  it('supports remote upstream search in the filter bar', async () => {
    const wrapper = mountPage()
    const selects = wrapper.findAllComponents(ElSelectStub)
    const filterSelect = selects.find((node) => node.props('placeholder')?.includes('上游合同'))

    expect(filterSelect).toBeTruthy()
    expect(filterSelect.props('placeholder')).toContain('上游合同')
    expect(typeof filterSelect.props('remoteMethod')).toBe('function')

    await filterSelect.props('remoteMethod')('甲方单位')

    expect(getUpstreamContractsMock).toHaveBeenCalledWith({
      keyword: '甲方单位',
      page_size: 100
    })

    filterSelect.vm.$emit('update:modelValue', 7)
    filterSelect.vm.$emit('change', 7)
    await wrapper.vm.handleQuery()

    expect(wrapper.vm.queryParams.upstream_contract_id).toBe(7)
    expect(getListMock).toHaveBeenCalled()
  })
})
