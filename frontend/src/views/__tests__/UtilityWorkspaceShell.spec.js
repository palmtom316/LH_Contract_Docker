import { shallowMount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import NotificationCenter from '@/views/notifications/NotificationCenter.vue'
import SystemManagement from '@/views/system/SystemManagement.vue'
import AuditLog from '@/views/audit/AuditLog.vue'

const systemManagementSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/system/SystemManagement.vue'),
  'utf-8'
)

const notificationCenterSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/notifications/NotificationCenter.vue'),
  'utf-8'
)

const auditLogSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/audit/AuditLog.vue'),
  'utf-8'
)

const userManagementSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/users/UserManagement.vue'),
  'utf-8'
)

const { notificationsState, markNotificationReadMock, removeNotificationMock } = vi.hoisted(() => ({
  notificationsState: [
    {
      id: 'local-blocked-delete',
      title: '上游合同无法删除',
      subtitle: '存在关联数据',
      content: '请先删除关联记录。',
      createdAt: '2026-04-07T10:00:00.000Z',
      unread: true,
      relatedGroups: [
        {
          label: '下游合同',
          items: ['DOWN-001 关联下游合同']
        }
      ]
    }
  ],
  markNotificationReadMock: vi.fn(),
  removeNotificationMock: vi.fn()
}))

vi.mock('@/stores/system', () => ({
  useSystemStore: () => ({
    notifications: notificationsState,
    notificationsError: '',
    fetchNotifications: vi.fn().mockResolvedValue([]),
    markNotificationRead: markNotificationReadMock,
    removeNotification: removeNotificationMock
  })
}))

vi.mock('@/composables/useDevice', () => ({
  useDevice: () => ({
    isMobile: false
  })
}))

vi.mock('@/utils/request', () => ({
  default: vi.fn().mockResolvedValue({
    items: [],
    total: 0
  })
}))

vi.mock('@/api/audit', () => ({
  deleteAuditLogsBefore: vi.fn()
}))

vi.mock('@/api/system', () => ({
  backupSystem: vi.fn(),
  backupDatabase: vi.fn(),
  resetSystem: vi.fn()
}))

vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn()
    },
    ElMessageBox: {
      confirm: vi.fn()
    }
  }
})

const globalMountOptions = {
  directives: {
    loading: {}
  },
  stubs: {
    AppWorkspacePanel: {
      props: ['panelClass'],
      template: '<section class="app-workspace-panel-stub" :class="panelClass"><slot /></section>'
    },
    AppSectionCard: { template: '<section class="app-section-card-stub"><slot name="header" /><slot /><slot name="actions" /></section>' },
    AppFilterBar: { template: '<div class="app-filter-bar-stub"><slot /><slot name="actions" /></div>' },
    AppDataTable: { template: '<div class="app-data-table-stub"><slot /><slot name="footer" /></div>' },
    AppEmptyState: { template: '<div class="app-empty-state-stub" />' },
    AppRangeField: { template: '<div class="app-range-field-stub" />' },
    UserManagement: { template: '<div class="user-management-stub" />' },
    SystemSettings: { template: '<div class="system-settings-stub" />' },
    ElSegmented: { template: '<div class="el-segmented-stub" />' },
    ElSkeleton: { template: '<div class="el-skeleton-stub" />' },
    ElEmpty: { template: '<div class="el-empty-stub"><slot /></div>' },
    ElButton: { template: '<button type="button"><slot /></button>' },
    ElTabs: { template: '<div class="el-tabs-stub"><slot /></div>' },
    ElTabPane: { template: '<div class="el-tab-pane-stub"><slot /></div>' },
    ElIcon: { template: '<i class="el-icon-stub"><slot /></i>' },
    ElUpload: { template: '<div class="el-upload-stub"><slot /></div>' },
    ElAlert: { template: '<div class="el-alert-stub" />' },
    ElDatePicker: { template: '<div class="el-date-picker-stub" />' },
    ElSelect: { template: '<div class="el-select-stub"><slot /></div>' },
    ElOption: { template: '<div class="el-option-stub" />' },
    ElDialog: { template: '<div class="el-dialog-stub"><slot /></div>' },
    ElDescriptions: { template: '<div class="el-descriptions-stub"><slot /></div>' },
    ElDescriptionsItem: { template: '<div class="el-descriptions-item-stub"><slot /></div>' },
    ElInput: { template: '<div class="el-input-stub" />' },
    ElTable: { template: '<div class="el-table-stub"><slot /></div>' },
    ElTableColumn: { template: '<div class="el-table-column-stub" />' },
    ElTag: { template: '<div class="el-tag-stub"><slot /></div>' },
    ElPagination: { template: '<div class="el-pagination-stub" />' }
  }
}

describe('Utility workspace shells', () => {
  it('renders the notification workspace wrappers', () => {
    const wrapper = shallowMount(NotificationCenter, { global: globalMountOptions })

    expect(wrapper.find('.notification-center-shell').exists()).toBe(true)
    expect(wrapper.find('.notification-center-header').exists()).toBe(false)
    expect(wrapper.find('.notification-center-panel').exists()).toBe(true)
  })

  it('renders notification actions and related record details', () => {
    const wrapper = shallowMount(NotificationCenter, { global: globalMountOptions })

    expect(wrapper.text()).toContain('已读')
    expect(wrapper.text()).toContain('删除')
    expect(wrapper.text()).toContain('下游合同')
    expect(wrapper.text()).toContain('DOWN-001 关联下游合同')
  })

  it('keeps the notification feed on elevated list surfaces with restrained unread emphasis', () => {
    expect(notificationCenterSource).toContain('box-shadow: var(--shadow-soft);')
    expect(notificationCenterSource).toContain('background: var(--surface-panel-elevated);')
    expect(notificationCenterSource).toContain('notification-item--unread')
  })

  it('renders the system workspace wrappers', () => {
    const wrapper = shallowMount(SystemManagement, { global: globalMountOptions })

    expect(wrapper.find('.system-management-shell').exists()).toBe(true)
    expect(wrapper.find('.system-management-panel').exists()).toBe(true)
  })

  it('keeps operations panels aligned to the shared workspace spacing scale', () => {
    expect(systemManagementSource).toContain('gap: var(--space-5);')
    expect(systemManagementSource).toContain('min-height: 100%;')
    expect(systemManagementSource).toContain('background: color-mix(in srgb, var(--surface-panel) 84%, var(--status-warning) 16%);')
    expect(systemManagementSource).not.toContain('.operation-panel {\n  height: 100%;')
  })

  it('renders the audit workspace wrappers', () => {
    const wrapper = shallowMount(AuditLog, { global: globalMountOptions })

    expect(wrapper.find('.audit-log-shell').exists()).toBe(true)
    expect(wrapper.find('.audit-log-header').exists()).toBe(false)
    expect(wrapper.find('.audit-log-panel--filters').exists()).toBe(true)
    expect(wrapper.find('.audit-log-panel--records').exists()).toBe(true)
  })

  it('brings audit records and user management onto the shared workspace shell rhythm', () => {
    expect(auditLogSource).toContain('box-shadow: var(--shadow-soft);')
    expect(auditLogSource).toContain('background: var(--surface-panel-elevated);')
    expect(userManagementSource).toContain('user-management-shell')
    expect(userManagementSource).toContain("import AppFilterBar from '@/components/ui/AppFilterBar.vue'")
    expect(userManagementSource).toContain("import AppDataTable from '@/components/ui/AppDataTable.vue'")
    expect(userManagementSource).toContain('gap: var(--space-5);')
  })
})
