import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick, ref, reactive } from 'vue'
import ZeroHourLaborList from '@/views/expenses/ZeroHourLaborList.vue'

const routeState = reactive({ query: {} })
const setRouteQuery = (nextQuery = {}) => {
  Object.keys(routeState.query).forEach((key) => {
    delete routeState.query[key]
  })
  Object.keys(nextQuery).forEach((key) => {
    routeState.query[key] = nextQuery[key]
  })
}

const apiMocks = vi.hoisted(() => ({
  getZeroHourLaborList: vi.fn(),
  createZeroHourLabor: vi.fn(),
  updateZeroHourLabor: vi.fn(),
  deleteZeroHourLabor: vi.fn(),
  exportZeroHourLabor: vi.fn()
}))

const upstreamMocks = vi.hoisted(() => ({
  getContracts: vi.fn()
}))

vi.mock('vue-router', async () => {
  const actual = await vi.importActual('vue-router')
  return {
    ...actual,
    useRoute: () => routeState
  }
})

vi.mock('@/api/zeroHourLabor', () => ({
  getZeroHourLaborList: apiMocks.getZeroHourLaborList,
  createZeroHourLabor: apiMocks.createZeroHourLabor,
  updateZeroHourLabor: apiMocks.updateZeroHourLabor,
  deleteZeroHourLabor: apiMocks.deleteZeroHourLabor,
  exportZeroHourLabor: apiMocks.exportZeroHourLabor
}))

vi.mock('@/api/contractUpstream', () => ({
  getContracts: upstreamMocks.getContracts
}))

vi.mock('@/api/common', () => ({
  uploadFile: vi.fn()
}))

vi.mock('@/utils/common', () => ({
  formatMoney: vi.fn((value) => String(value))
}))

vi.mock('@/composables/useContractList', () => ({
  useMobileDetection: () => ({
    isMobile: ref(false)
  })
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

const mountPage = () =>
  mount(ZeroHourLaborList, {
    global: {
      directives: {
        loading: {}
      },
      stubs: {
        AppWorkspacePanel: true,
        AppSectionCard: true,
        AppFilterBar: true,
        AppRangeField: true,
        AppDataTable: true,
        AppEmptyState: true,
        ElSelect: true,
        ElOption: true,
        ElInput: true,
        ElDatePicker: true,
        ElDivider: true,
        ElInputNumber: true,
        ElButton: true,
        ElDropdown: true,
        ElDropdownMenu: true,
        ElDropdownItem: true,
        ElPagination: true,
        ElTable: true,
        ElTableColumn: true,
        ElTag: true,
        ElCard: true,
        ElDialog: { template: '<div><slot /></div>' },
        ElForm: { template: '<form><slot /></form>' },
        ElFormItem: {
          props: ['label'],
          template: '<div><span>{{ label }}</span><slot /></div>'
        },
        ElRow: { template: '<div><slot /></div>' },
        ElCol: { template: '<div><slot /></div>' },
        ElUpload: true,
        ElTooltip: true,
        ElIcon: true
      }
    }
  })

describe('ZeroHourLaborList route filters', () => {
  beforeEach(() => {
    setRouteQuery({})
    apiMocks.getZeroHourLaborList.mockResolvedValue({ items: [], total: 0 })
  })

  afterEach(() => {
    setRouteQuery({})
    vi.clearAllMocks()
  })

  it('applies upstream contract filter from route query on mount', async () => {
    setRouteQuery({ upstream_contract_id: '58' })
    const wrapper = mountPage()
    await flushPromises()

    expect(apiMocks.getZeroHourLaborList).toHaveBeenCalledWith(
      expect.objectContaining({
        upstream_contract_id: 58
      })
    )
  })

  it('shows dispatch unit field for company labor entries', async () => {
    const wrapper = mountPage()
    await flushPromises()

    wrapper.vm.form.attribution = 'COMPANY'
    await nextTick()

    expect(wrapper.text()).toContain('派工单位名称')
  })
})
