import { shallowMount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import MobileLayout from '@/views/mobile/MobileLayout.vue'
import ContractListMobile from '@/views/mobile/ContractListMobile.vue'
import ExpenseListMobile from '@/views/mobile/ExpenseListMobile.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({
    meta: { title: '移动端' },
    path: '/m/contracts'
  }),
  useRouter: () => ({ push: vi.fn() })
}))

vi.mock('@/utils/request', () => ({
  default: vi.fn()
}))

vi.mock('@/stores/system', () => ({
  useSystemStore: () => ({
    notifications: [],
    fetchNotifications: vi.fn()
  })
}))

vi.mock('@/stores/ui', () => ({
  useUiStore: () => ({
    notificationDrawerOpen: false
  })
}))

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    canManageUsers: true,
    canViewUpstreamContracts: true,
    canViewExpenses: true,
    canViewReports: true,
    canManageUpstreamContracts: true,
    canManageDownstreamContracts: true,
    canManageManagementContracts: true,
    logout: vi.fn()
  })
}))

vi.mock('vant', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    showToast: vi.fn(),
    showImagePreview: vi.fn()
  }
})

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn() },
  ElMessageBox: { confirm: vi.fn().mockResolvedValue() }
}))

vi.mock('@/api/contractUpstream', () => ({
  getContracts: vi.fn().mockResolvedValue({ items: [], total: 0 })
}))

vi.mock('@/api/contractDownstream', () => ({
  getContracts: vi.fn().mockResolvedValue({ items: [], total: 0 })
}))

vi.mock('@/api/contractManagement', () => ({
  getContracts: vi.fn().mockResolvedValue({ items: [], total: 0 })
}))

vi.mock('@/api/expense', () => ({
  getExpenses: vi.fn().mockResolvedValue({ items: [], total: 0 })
}))

vi.mock('@/api/zeroHourLabor', () => ({
  getZeroHourLaborList: vi.fn().mockResolvedValue({ items: [], total: 0 })
}))

const mountPage = () =>
  shallowMount(MobileLayout, {
    global: {
      stubs: {
        RouterView: { template: '<div class="router-view-stub" />' },
        RouterLink: { template: '<a><slot /></a>' },
        AppTopbarActions: true,
        NotificationCenter: true,
        SidebarUserCard: true,
        VanIcon: true,
        VanPopup: { template: '<div><slot /></div>' },
        VanTabbar: { template: '<div><slot /></div>' },
        VanTabbarItem: { template: '<div><slot /></div>' },
        ElDialog: { template: '<div><slot /></div>' },
        ElForm: { template: '<form><slot /></form>' },
        ElFormItem: { template: '<div><slot /></div>' },
        ElInput: { template: '<input />' },
        ElButton: { template: '<button type="button"><slot /></button>' }
      }
    }
  })

const mountContractList = () =>
  shallowMount(ContractListMobile, {
    global: {
      stubs: {
        VanDropdownMenu: { template: '<div class="van-dropdown-menu-stub"><slot /></div>' },
        VanDropdownItem: { template: '<div class="van-dropdown-item-stub" />' },
        VanIcon: true,
        VanSearch: { template: '<div class="van-search-stub" />' },
        VanTabs: { template: '<div class="van-tabs-stub"><slot /></div>' },
        VanTab: { template: '<div class="van-tab-stub" />' },
        VanPullRefresh: { template: '<div class="van-pull-refresh-stub"><slot /></div>' },
        VanList: { template: '<div class="van-list-stub"><slot /></div>' },
        VanCell: { template: '<div class="van-cell-stub"><slot name="title" /><slot name="value" /></div>' },
        VanCellGroup: { template: '<div class="van-cell-group-stub"><slot /></div>' },
        VanTag: { template: '<div class="van-tag-stub"><slot /></div>' },
        VanEmpty: { template: '<div class="van-empty-stub" />' },
        VanActionSheet: { template: '<div class="van-action-sheet-stub" />' }
      }
    }
  })

const mountExpenseList = () =>
  shallowMount(ExpenseListMobile, {
    global: {
      stubs: {
        VanTabs: { template: '<div class="van-tabs-stub"><slot /></div>' },
        VanTab: { template: '<div class="van-tab-stub" />' },
        VanSearch: { template: '<div class="van-search-stub" />' },
        VanPullRefresh: { template: '<div class="van-pull-refresh-stub"><slot /></div>' },
        VanList: { template: '<div class="van-list-stub"><slot /></div>' },
        VanCell: { template: '<div class="van-cell-stub"><slot name="title" /><slot name="value" /></div>' },
        VanCellGroup: { template: '<div class="van-cell-group-stub"><slot /></div>' },
        VanTag: { template: '<div class="van-tag-stub"><slot /></div>' },
        VanEmpty: { template: '<div class="van-empty-stub" />' }
      }
    }
  })

describe('Mobile workspace shell', () => {
  it('renders the mobile workspace frame wrappers', () => {
    const wrapper = mountPage()

    expect(wrapper.find('.mobile-shell').exists()).toBe(true)
    expect(wrapper.find('.mobile-shell__frame').exists()).toBe(true)
  })

  it('renders the mobile contract toolbar shell', () => {
    const wrapper = mountContractList()

    expect(wrapper.find('.mobile-contract-list').exists()).toBe(true)
    expect(wrapper.find('.mobile-contract-list__toolbar').exists()).toBe(true)
    expect(wrapper.find('.mobile-contract-list__filters').exists()).toBe(true)
  })

  it('renders the mobile expense toolbar shell', () => {
    const wrapper = mountExpenseList()

    expect(wrapper.find('.mobile-expense-list').exists()).toBe(true)
    expect(wrapper.find('.mobile-expense-list__toolbar').exists()).toBe(true)
    expect(wrapper.find('.mobile-expense-list__filters').exists()).toBe(true)
  })
})
