import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, reactive, ref } from 'vue'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import DownstreamList from '@/views/contracts/DownstreamList.vue'

const downstreamListSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/contracts/DownstreamList.vue'),
  'utf-8'
)

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
  useUserStore: () => ({ canManageDownstreamContracts: false })
}))

vi.mock('@/api/contractDownstream', () => ({
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
    </div>
  `
})

const ElDialogStub = defineComponent({
  props: ['modelValue'],
  template: '<div v-if="modelValue"><slot /></div>'
})

const mountPage = () =>
  mount(DownstreamList, {
    global: {
      directives: {
        loading: {}
      },
      stubs: {
        AppSectionCard: { template: '<section><slot name="header" /><slot /><slot name="actions" /></section>' },
        AppFilterBar: { template: '<div><slot /><slot name="actions" /></div>' },
        AppDataTable: { template: '<div><slot /><slot name="footer" /></div>' },
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
        ElDialog: ElDialogStub,
        ElForm: true,
        ElFormItem: true,
        ElInputNumber: true,
        ElTag: true,
        ElRow: true,
        ElCol: true,
        ElCard: true,
        ElUpload: true,
        ElTooltip: true,
        ElIcon: true
      }
    }
  })

describe('DownstreamList workspace shell', () => {
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
    getUpstreamContractsMock.mockResolvedValue({ items: [] })
  })

  it('renders downstream-specific workspace shell wrappers without the top title band', () => {
    const wrapper = mountPage()

    expect(wrapper.find('.downstream-page-shell').exists()).toBe(true)
    expect(wrapper.find('.downstream-page-header').exists()).toBe(false)
    expect(wrapper.findAll('.downstream-page-panel')).toHaveLength(2)
    expect(wrapper.find('.downstream-page-panel--filters').exists()).toBe(true)
    expect(wrapper.find('.downstream-page-panel--list').exists()).toBe(true)
  })

  it('keeps the downstream list surfaces elevated instead of flattening them into transparent cards', () => {
    expect(downstreamListSource).toContain('background: var(--surface-panel-elevated);')
    expect(downstreamListSource).toContain('padding-top: 16px;')
    expect(downstreamListSource).toContain('border-top: 1px solid var(--border-subtle);')
    expect(downstreamListSource).not.toContain('background: transparent;')
  })
})
