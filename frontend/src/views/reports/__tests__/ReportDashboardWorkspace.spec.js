import { shallowMount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ReportDashboard from '@/views/reports/ReportDashboard.vue'

vi.mock('@/api/reports', () => ({
  getCostMonthlyQuarterlyReport: vi.fn().mockResolvedValue({
    period: { year: 2026, month: 4, quarter: 2, half_year: 1 },
    monthly: { rows: [], total: {} },
    quarterly: { rows: [], total: {} },
    half_yearly: { rows: [], total: {} },
    yearly: { rows: [], total: {} }
  }),
  downloadCostMonthlyQuarterlyReport: vi.fn(),
  downloadComprehensiveReport: vi.fn(),
  downloadReceivablesReport: vi.fn(),
  downloadPayablesReport: vi.fn(),
  downloadUpstreamInvoicesReport: vi.fn(),
  downloadDownstreamInvoicesReport: vi.fn(),
  downloadUpstreamReceiptsReport: vi.fn(),
  downloadDownstreamPaymentsReport: vi.fn(),
  downloadExpensePaymentsReport: vi.fn(),
  downloadUpstreamSettlementsReport: vi.fn(),
  downloadDownstreamSettlementsReport: vi.fn(),
  downloadAssociationReport: vi.fn()
}))

vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    ElMessage: {
      error: vi.fn(),
      success: vi.fn()
    }
  }
})

const mountPage = () =>
  shallowMount(ReportDashboard, {
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
        AppFilterBar: { template: '<div class="app-filter-bar-stub"><slot /><slot name="actions" /></div>' },
        AppDataTable: { template: '<div class="app-data-table-stub"><slot /><slot name="footer" /></div>' },
        AppEmptyState: { template: '<div class="app-empty-state-stub" />' },
        AppRangeField: { template: '<div class="app-range-field-stub" />' },
        ElInput: { template: '<div class="el-input-stub" />' },
        ElDatePicker: { template: '<div class="el-date-picker-stub" />' },
        ElTabs: { template: '<div class="el-tabs-stub"><slot /></div>' },
        ElTabPane: { template: '<div class="el-tab-pane-stub"><slot /></div>' },
        ElTable: { template: '<div class="el-table-stub"><slot /></div>' },
        ElTableColumn: { template: '<div class="el-table-column-stub"><slot /></div>' },
        ElButton: { template: '<button class="el-button-stub"><slot /></button>' },
        ElSelect: { template: '<div class="el-select-stub"><slot /></div>' },
        ElOption: { template: '<div class="el-option-stub" />' }
      }
    }
  })

describe('Report dashboard workspace shell', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the shared report workspace shell wrappers', () => {
    const wrapper = mountPage()

    expect(wrapper.find('.report-dashboard-shell').exists()).toBe(true)
    expect(wrapper.find('.report-dashboard-header').exists()).toBe(false)
    expect(wrapper.find('.report-dashboard-panels').exists()).toBe(true)
    expect(wrapper.find('.report-dashboard-panel').exists()).toBe(true)
    expect(wrapper.find('.report-export-card__filters').exists()).toBe(true)
  })
})
