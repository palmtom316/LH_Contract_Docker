import { flushPromises, shallowMount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import SystemSettings from '@/views/system/SystemSettings.vue'

const systemSettingsSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/system/SystemSettings.vue'),
  'utf-8'
)

const fetchConfigMock = vi.fn().mockResolvedValue(undefined)
const fetchOptionsMock = vi.fn().mockResolvedValue([])

vi.mock('@/stores/system', () => ({
  useSystemStore: () => ({
    config: {
      system_name: '合同管理系统',
      system_name_line_2: 'Platform',
      system_logo: ''
    },
    fetchConfig: fetchConfigMock,
    fetchOptions: fetchOptionsMock,
    updateConfig: vi.fn(),
    deleteOption: vi.fn(),
    addOption: vi.fn(),
    updateOption: vi.fn()
  })
}))

vi.mock('@/utils/request', () => ({
  default: vi.fn()
}))

vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn()
    },
    ElMessageBox: {
      confirm: vi.fn()
    }
  }
})

const mountPage = () =>
  shallowMount(SystemSettings, {
    global: {
      directives: {
        loading: {}
      },
      stubs: {
        AppWorkspacePanel: {
          props: ['panelClass'],
          template: '<section class="app-workspace-panel-stub" :class="panelClass"><slot /></section>'
        },
        AppSectionCard: { template: '<section class="app-section-card-stub"><slot name="header" /><slot /><slot name="actions" /></section>' },
        ElTabs: { template: '<div class="el-tabs-stub"><slot /></div>' },
        ElTabPane: { template: '<div class="el-tab-pane-stub"><slot /></div>' },
        ElForm: { template: '<form class="el-form-stub"><slot /></form>' },
        ElFormItem: { template: '<div class="el-form-item-stub"><slot /></div>' },
        ElInput: { template: '<div class="el-input-stub" />' },
        ElUpload: { template: '<div class="el-upload-stub"><slot /></div>' },
        ElIcon: { template: '<i class="el-icon-stub"><slot /></i>' },
        ElButton: { template: '<button class="el-button-stub"><slot /></button>' },
        ElMenu: { template: '<div class="el-menu-stub"><slot /></div>' },
        ElMenuItem: { template: '<div class="el-menu-item-stub"><slot /></div>' },
        ElTable: { template: '<div class="el-table-stub"><slot /></div>' },
        ElTableColumn: { template: '<div class="el-table-column-stub"><slot /></div>' },
        ElDialog: { template: '<div class="el-dialog-stub"><slot /><slot name="footer" /></div>' },
        ElInputNumber: { template: '<div class="el-input-number-stub" />' }
      }
    }
  })

describe('SystemSettings workspace shell', () => {
  it('renders the system settings shell without a top page header band', async () => {
    const wrapper = mountPage()
    await flushPromises()

    expect(fetchConfigMock).toHaveBeenCalled()
    expect(fetchOptionsMock).toHaveBeenCalledWith('contract_category')
    expect(wrapper.find('.system-settings-page').exists()).toBe(true)
    expect(wrapper.find('.app-page-header-stub').exists()).toBe(false)
    expect(wrapper.find('.system-settings-panel').exists()).toBe(true)
    expect(wrapper.find('.system-settings-tabs').exists()).toBe(true)
  })

  it('keeps dictionary management inside the same workspace surface rhythm', () => {
    expect(systemSettingsSource).toContain('border-radius: calc(var(--radius-lg) + 2px);')
    expect(systemSettingsSource).toContain('padding: 18px;')
    expect(systemSettingsSource).toContain('justify-content: space-between;')
    expect(systemSettingsSource).not.toContain('border-radius: 14px;')
  })
})
