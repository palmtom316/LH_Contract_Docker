import { describe, expect, it, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import Business from '@/views/home/Business.vue'

const { chartInstances, initChart } = vi.hoisted(() => {
  const chartInstances = []
  const initChart = vi.fn(() => {
    const instance = {
      setOption: vi.fn(),
      dispose: vi.fn(),
      resize: vi.fn()
    }
    chartInstances.push(instance)
    return instance
  })

  return { chartInstances, initChart }
})

vi.mock('@/utils/echarts', () => ({
  default: {
    init: initChart
  }
}))

vi.mock('@/api/reports', () => ({
  getContractSummary: vi.fn(),
  getFinanceTrend: vi.fn(),
  getExpenseBreakdown: vi.fn(),
  getArApStats: vi.fn()
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

const businessSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/home/Business.vue'),
  'utf-8'
)

describe('Business metric cards', () => {
  it('reuses the shared metric card component for the top summary cards without the eyebrow copy', () => {
    expect(businessSource).toContain("import AppMetricCard from '@/components/ui/AppMetricCard.vue'")
    expect(businessSource).toContain('<AppMetricCard')
    expect(businessSource).toContain(":eyebrow=\"''\"")
    expect(businessSource).not.toContain('<article class="metric-card')
  })
})

describe('Business chart composition', () => {
  it('drops pie and rose chart rendering in favor of ranking and stacked bars', () => {
    expect(businessSource).toContain("from '@/utils/dashboardRanking'")
    expect(businessSource).toContain('createHorizontalRankOption')
    expect(businessSource).toContain('createStackedCategoryOption')
    expect(businessSource).not.toContain("type: \"pie\"")
    expect(businessSource).not.toContain('roseType')
  })
})

describe('Business expense structure chart mapping', () => {
  const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

  const mountPage = () =>
    mount(Business, {
      global: {
        directives: {
          loading: {}
        },
        stubs: {
          AppFilterBar: { template: '<div class="app-filter-bar-stub"><slot /><slot name="actions" /></div>' },
          AppMetricCard: { template: '<div class="app-metric-card-stub"><slot /><slot name="badge" /><slot name="footer" /></div>' },
          AppSectionCard: { template: '<section class="app-section-card-stub"><slot name="header" /><slot /></section>' },
          ElDatePicker: { template: '<div class="el-date-picker-stub" />' },
          ElSelect: { template: '<div class="el-select-stub"><slot /></div>' },
          ElOption: { template: '<div class="el-option-stub" />' },
          ElButton: { template: '<button class="el-button-stub"><slot /></button>' },
          ElProgress: { template: '<div class="el-progress-stub" />' }
        }
      }
    })

  beforeEach(async () => {
    chartInstances.length = 0
    initChart.mockClear()
    vi.clearAllMocks()
    const { getContractSummary, getFinanceTrend, getExpenseBreakdown, getArApStats } = await import('@/api/reports')

    getContractSummary.mockResolvedValue({
      upstream_by_category: [{ name: '安装', amount: 100000, count: 1 }],
      upstream_by_company_category: [{ name: 'A公司', amount: 80000, count: 1 }],
      downstream_by_category: [],
      management_by_category: []
    })
    getFinanceTrend.mockResolvedValue({
      months: ['1月'],
      income: [100000],
      expense_breakdown: {
        downstream: [20000],
        management: [30000],
        non_contract: [4000]
      }
    })
    getExpenseBreakdown.mockResolvedValue({
      overall_breakdown: [
        { name: '下游合同支出', value: 120000 },
        { name: '管理合同支出', value: 340000 },
        { name: '无合同费用', value: 56000 },
        { name: '零星用工', value: 78000 }
      ],
      non_contract_breakdown: [{ name: '差旅', value: 12000, count: 2 }],
      zero_hour_labor: { count: 1, total: 78000 }
    })
    getArApStats.mockResolvedValue({
      ar: { total_receivable: 100000, total_received: 80000, outstanding: 20000 },
      ap: { total_payable: 60000, total_paid: 40000, outstanding: 20000 }
    })
  })

  it('maps backend expense labels into the stacked category chart series', async () => {
    mountPage()
    await flushPromises()
    await flushPromises()

    const expenseChartInstance = chartInstances.find((instance) =>
      instance.setOption.mock.calls.some(([option]) => option?.title?.text === '支出构成')
    )

    expect(expenseChartInstance).toBeTruthy()

    const expenseOption = expenseChartInstance.setOption.mock.calls.find(
      ([option]) => option?.title?.text === '支出构成'
    )[0]
    const downstreamSeries = expenseOption.series.find((item) => item.name === '下游合同')
    const managementSeries = expenseOption.series.find((item) => item.name === '管理合同')

    expect(downstreamSeries.data[0]).toBe(120000)
    expect(managementSeries.data[0]).toBe(340000)
  })
})
