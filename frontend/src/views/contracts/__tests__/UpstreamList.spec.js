import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { defineComponent, reactive, ref } from 'vue'
import UpstreamList from '@/views/contracts/UpstreamList.vue'

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
      company_category: '',
      category: '',
      management_mode: '',
      start_date: undefined,
      end_date: undefined,
      start_month: undefined,
      end_month: undefined
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
    useRoute: () => ({ query: {} })
  }
})

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    canManageUpstreamContracts: false
  })
}))

vi.mock('@/api/contractUpstream', () => ({
  getContracts: vi.fn(),
  createContract: vi.fn(),
  updateContract: vi.fn(),
  deleteContract: vi.fn(),
  exportContracts: vi.fn(),
  downloadImportTemplate: vi.fn(),
  importContracts: vi.fn(),
  getNextSerialNumber: vi.fn()
}))

vi.mock('@/api/common', () => ({
  uploadFile: vi.fn()
}))

vi.mock('@/utils/common', () => ({
  getFileUrl: vi.fn()
}))

vi.mock('@/utils/download', () => ({
  downloadExcel: vi.fn()
}))

const RangeFieldStub = defineComponent({
  props: ['modelValue', 'type', 'startPlaceholder', 'endPlaceholder'],
  emits: ['update:modelValue'],
  template: `
    <div class="range-field-stub" :data-type="type || 'date'" :data-start="startPlaceholder" :data-end="endPlaceholder">
      <button type="button" class="apply-range" @click="$emit('update:modelValue', ['2026-04-01', '2026-04-06'])">apply</button>
    </div>
  `
})

const mountPage = () =>
  mount(UpstreamList, {
    global: {
      stubs: {
        AppSectionCard: { template: '<section><slot name="header" /><slot /><slot name="actions" /></section>' },
        AppFilterBar: { template: '<div><slot /><slot name="actions" /></div>' },
        AppDataTable: { template: '<div><slot /></div>' },
        AppEmptyState: true,
        AppRangeField: RangeFieldStub,
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
        ElIcon: true,
        ElTabs: { template: '<div><slot /></div>' },
        ElTabPane: { template: '<div><slot /></div>' },
        ElResult: true,
        ElDivider: true
      }
    }
  })

describe('UpstreamList filters', () => {
  beforeEach(() => {
    queryParamsState.value.page = 1
    queryParamsState.value.start_date = undefined
    queryParamsState.value.end_date = undefined
    queryParamsState.value.start_month = undefined
    queryParamsState.value.end_month = undefined
    getListMock.mockClear()
  })

  it('uses date input range instead of month picker for the management filter', async () => {
    const wrapper = mountPage()
    const rangeFields = wrapper.findAll('.range-field-stub')

    expect(rangeFields[0].attributes('data-type')).toBe('date')
    expect(rangeFields[0].attributes('data-start')).toBe('开始日期')
    expect(rangeFields[0].attributes('data-end')).toBe('结束日期')
  })

  it('writes management filter values into start_date and end_date', async () => {
    const wrapper = mountPage()
    const rangeFields = wrapper.findAll('.range-field-stub')

    await rangeFields[0].find('.apply-range').trigger('click')
    await wrapper.vm.handleQuery()

    expect(wrapper.vm.queryParams.start_date).toBe('2026-04-01')
    expect(wrapper.vm.queryParams.end_date).toBe('2026-04-06')
    expect(wrapper.vm.queryParams.start_month).toBeUndefined()
    expect(wrapper.vm.queryParams.end_month).toBeUndefined()
    expect(getListMock).toHaveBeenCalled()
  })
})
