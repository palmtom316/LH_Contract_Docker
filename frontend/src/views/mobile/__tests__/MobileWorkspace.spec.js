import { shallowMount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import MobileLayout from '@/views/mobile/MobileLayout.vue'

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
    logout: vi.fn()
  })
}))

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn() },
  ElMessageBox: { confirm: vi.fn().mockResolvedValue() }
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

describe('Mobile workspace shell', () => {
  it('renders the mobile workspace frame wrappers', () => {
    const wrapper = mountPage()

    expect(wrapper.find('.mobile-shell').exists()).toBe(true)
    expect(wrapper.find('.mobile-shell__content').exists()).toBe(true)
  })
})
