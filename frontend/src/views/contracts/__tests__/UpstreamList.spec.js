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

const routeMock = reactive({
  query: {},
  meta: { title: '首页' },
  path: '/'
})
const routerMock = { push: vi.fn() }
vi.mock('vue-router', async () => {
  const actual = await vi.importActual('vue-router')
  return {
    ...actual,
    useRouter: () => routerMock,
    useRoute: () => routeMock
  }
})

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    canManageUpstreamContracts: false,
    canViewDashboard: true,
    canViewUpstreamContracts: true,
    canViewDownstreamContracts: true,
    canViewManagementContracts: true,
    canViewExpenses: true,
    canViewReports: true,
    canManageUsers: true,
    isAdmin: false
  })
}))

const fetchConfigMock = vi.fn()
const fetchNotificationsMock = vi.fn()
vi.mock('@/stores/system', () => ({
  useSystemStore: () => ({
    config: {
      system_name: '蓝海合同管理',
      system_name_line_2: 'Platform'
    },
    notifications: [],
    fetchConfig: fetchConfigMock,
    fetchNotifications: fetchNotificationsMock
  })
}))

const closeNotificationDrawerMock = vi.fn()
vi.mock('@/stores/ui', () => ({
  useUiStore: () => ({
    notificationDrawerOpen: false,
    closeNotificationDrawer: closeNotificationDrawerMock
  })
}))

vi.mock('@/composables/useDevice', () => ({
  useDevice: () => ({
    isMobile: ref(false)
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

const ElButtonStub = defineComponent({
  props: ['type', 'icon'],
  emits: ['click'],
  template: `
    <button
      type="button"
      :data-type="type"
      :data-icon="icon"
      v-bind="$attrs"
      @click="$emit('click', $event)"
    >
      <slot />
    </button>
  `
})

const ElTabPaneStub = defineComponent({
  props: ['label', 'name'],
  template: '<div class="el-tab-pane-stub" :data-label="label" :data-name="name"><span class="tab-label">{{ label }}</span><slot /></div>'
})

const layoutElementStubs = {
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
  ElButton: ElButtonStub,
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
  ElTabPane: ElTabPaneStub,
  ElResult: true,
  ElDivider: true
}

const mountPage = () =>
  mount(UpstreamList, {
    global: {
      stubs: layoutElementStubs
    }
  })

describe('UpstreamList filters', () => {
  beforeEach(() => {
    queryParamsState.value.page = 1
    queryParamsState.value.page_size = 10
    queryParamsState.value.keyword = ''
    queryParamsState.value.status = ''
    queryParamsState.value.company_category = ''
    queryParamsState.value.category = ''
    queryParamsState.value.management_mode = ''
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

  it('renders the management and basic info tabs', () => {
    const wrapper = mountPage()
    const paneLabels = wrapper.findAll('.el-tab-pane-stub').map((pane) => pane.attributes('data-label'))

    expect(wrapper.text()).toContain('合同管理')
    expect(wrapper.text()).toContain('上游合同基本信息')
    expect(paneLabels).toEqual(expect.arrayContaining(['合同管理', '上游合同基本信息']))
  })

  it('shows the management filter action buttons', () => {
    const wrapper = mountPage()
    const managementPane = wrapper.get('.el-tab-pane-stub[data-name="management"]')
    const searchButton = managementPane.get('[data-icon="Search"]')
    const resetButton = managementPane.get('[data-icon="Refresh"]')

    expect(wrapper.text()).toContain('搜索')
    expect(wrapper.text()).toContain('重置')
    expect(searchButton.text()).toBe('搜索')
    expect(resetButton.text()).toBe('重置')
  })
})

describe('upstream workspace shell structure', () => {
  it('uses upstream-specific workspace wrappers for the full app redesign', () => {
    const wrapper = mountPage()

    expect(wrapper.find('.upstream-workspace-shell').exists()).toBe(true)
    expect(wrapper.find('.upstream-workspace-shell__body').exists()).toBe(true)
  })

})
