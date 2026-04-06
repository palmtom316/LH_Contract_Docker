import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { reactive, ref } from 'vue'
import ManagementList from '@/views/contracts/ManagementList.vue'

const { getListMock, queryParamsState } = vi.hoisted(() => ({
  getListMock: vi.fn(),
  queryParamsState: { value: null }
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
      category: undefined
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
  getContracts: vi.fn(),
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

const mountPage = () =>
  mount(ManagementList, {
    global: {
      stubs: {
        AppSectionCard: { template: '<section><slot name="header" /><slot /><slot name="actions" /></section>' },
        AppFilterBar: { template: '<div><slot /><slot name="actions" /></div>' },
        AppDataTable: { template: '<div><slot /><slot name="footer" /></div>' },
        AppEmptyState: true,
        AppRangeField: true,
        DictSelect: true,
        SmartDateInput: true,
        ElInput: true,
        ElSelect: true,
        ElOption: true,
        ElButton: true,
        ElTable: true,
        ElTableColumn: true,
        ElPagination: true,
        ElDialog: true,
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
    queryParamsState.value.keyword = ''
    queryParamsState.value.status = ''
    queryParamsState.value.start_date = undefined
    queryParamsState.value.end_date = undefined
    getListMock.mockClear()
  })

  it('applies both range sides when provided', async () => {
    const wrapper = mountPage()
    wrapper.vm.dateRange = ['2026-04-01', '2026-04-06']

    await wrapper.vm.handleQuery()

    expect(wrapper.vm.queryParams.start_date).toBe('2026-04-01')
    expect(wrapper.vm.queryParams.end_date).toBe('2026-04-06')
    expect(getListMock).toHaveBeenCalled()
  })

  it('supports partial range values', async () => {
    const wrapper = mountPage()
    wrapper.vm.dateRange = ['2026-04-01', '']

    await wrapper.vm.handleQuery()

    expect(wrapper.vm.queryParams.start_date).toBe('2026-04-01')
    expect(wrapper.vm.queryParams.end_date).toBeUndefined()

    wrapper.vm.dateRange = ['', '2026-04-06']
    await wrapper.vm.handleQuery()

    expect(wrapper.vm.queryParams.start_date).toBeUndefined()
    expect(wrapper.vm.queryParams.end_date).toBe('2026-04-06')
  })
})
