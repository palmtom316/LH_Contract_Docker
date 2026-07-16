import { shallowMount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import ReportDashboard from '@/views/reports/ReportDashboard.vue'

const reportDashboardSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/reports/ReportDashboard.vue'),
  'utf-8'
)

vi.mock('@/api/reports', () => ({
  getCostMonthlyQuarterlyReport: vi.fn().mockResolvedValue({
    period: { year: 2026, month: 4, quarter: 2, half_year: 1 },
    monthly: { rows: [], total: {} },
    quarterly: { rows: [], total: {} },
    half_yearly: { rows: [], total: {} },
    yearly: { rows: [], total: {} }
  }),
  downloadCostMonthlyQuarterlyReport: vi.fn(),
  getSettlementMonthlyQuarterlyReport: vi.fn().mockResolvedValue({
    period: { year: 2026, month: 4, quarter: 2, half_year: 1 },
    monthly: { rows: [] },
    quarterly: { rows: [] },
    half_yearly: { rows: [] },
    yearly: { rows: [] }
  }),
  downloadSettlementMonthlyQuarterlyReport: vi.fn(),
  downloadComprehensiveReport: vi.fn(),
  downloadReceivablesReport: vi.fn(),
  downloadPayablesReport: vi.fn(),
  downloadUpstreamInvoicesReport: vi.fn(),
  downloadDownstreamInvoicesReport: vi.fn(),
  downloadUpstreamReceiptsReport: vi.fn(),
  downloadUpstreamInvoiceReceiptComprehensiveReport: vi.fn(),
  downloadDownstreamPaymentsReport: vi.fn(),
  downloadExpensePaymentsReport: vi.fn(),
  downloadUpstreamSettlementsReport: vi.fn(),
  downloadDownstreamSettlementsReport: vi.fn(),
  downloadAssociationReport: vi.fn(),
  downloadZeroHourLaborReport: vi.fn()
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

  it('uses restrained export cards instead of oversized radii and gradients', () => {
    expect(reportDashboardSource).toContain('border-radius: calc(var(--radius) + 2px);')
    expect(reportDashboardSource).toContain('background: color-mix(in srgb, var(--surface-panel) 90%, var(--surface-panel-muted) 10%);')
    expect(reportDashboardSource).toContain('gap: var(--space-5);')
    expect(reportDashboardSource).not.toContain('border-radius: 22px;')
    expect(reportDashboardSource).not.toContain('background: linear-gradient(180deg, var(--surface-panel), var(--surface-panel-muted));')
  })

  it('pins each export button to a consistent bottom edge even when report card headings wrap differently', () => {
    expect(reportDashboardSource).toContain('grid-template-rows: auto 1fr;')
    expect(reportDashboardSource).toContain('height: 100%;')
    expect(reportDashboardSource).toContain('margin-top: auto;')
    expect(reportDashboardSource).toContain('align-self: end;')
  })

  it('adds company category filtering to downstream payment export', () => {
    expect(reportDashboardSource).toContain('companyCategory: downPayCompanyCategory.value')
    expect(reportDashboardSource).toContain("companyCategoryField('downstream-payment-company-category', downPayCompanyCategory)")
  })

  it('shows complete wrapped settlement text and a calculated total row', () => {
    expect(reportDashboardSource).toContain('class-name="settlement-text-column"')
    expect(reportDashboardSource).not.toContain('label="合同名称" :fixed="isMobile ? false : true" min-width="210" show-overflow-tooltip')
    expect(reportDashboardSource).toContain('show-summary')
    expect(reportDashboardSource).toContain(':summary-method="settlementSummaryMethod"')
    expect(reportDashboardSource).toContain('white-space: normal;')
    expect(reportDashboardSource).toContain('overflow-wrap: anywhere;')
  })

  it('uses the requested concise settlement column labels', () => {
    for (const label of [
      '甲方单位',
      '签约金额',
      '结算时间',
      '结算金额',
      '下游合同结算',
      '下游合同已付款',
      '无合同费用',
      '零星用工'
    ]) {
      expect(reportDashboardSource).toContain(`label="${label}"`)
    }
  })
})
