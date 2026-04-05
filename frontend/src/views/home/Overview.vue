<template>
  <div class="overview-page">
    <section class="dashboard-metric-grid">
      <AppMetricCard
        v-for="item in metricCards"
        :key="item.title"
        :eyebrow="item.eyebrow"
        :title="item.title"
        :value="item.value"
        :description="item.description"
      >
        <template #badge>
          <span class="metric-badge" :class="`metric-badge--${item.tone}`">{{ item.badge }}</span>
        </template>
      </AppMetricCard>
    </section>

    <section class="overview-summary-grid">
      <AppSectionCard>
        <template #header>年度收支趋势</template>
        <div ref="barChartRef" class="chart-surface chart-surface--annual" />
      </AppSectionCard>

      <AppSectionCard>
        <template #header>结构摘要</template>
        <div class="summary-grid">
          <article v-for="item in overviewSummaryCards" :key="item.title" class="summary-card">
            <span class="summary-card__title">{{ item.title }}</span>
            <strong class="summary-card__value">{{ item.value }}</strong>
            <span class="summary-card__meta">{{ item.meta }}</span>
          </article>
        </div>
      </AppSectionCard>
    </section>

    <section v-if="!isMobile" class="period-grid">
      <AppSectionCard>
        <template #header>近30天经营表现</template>
        <div class="period-panel">
          <div class="period-stats-grid">
            <div class="period-stat-group">
              <div class="period-stat-group__title">上游合同</div>
              <div class="period-stat-list">
                <div class="period-stat-item">
                  <span>签约数量</span>
                  <strong>{{ periodStats.monthly.upstream_count }} 单</strong>
                </div>
                <div class="period-stat-item">
                  <span>签约金额</span>
                  <strong>{{ formatAmount(periodStats.monthly.upstream_amount) }}</strong>
                </div>
                <div class="period-stat-item">
                  <span>回款金额</span>
                  <strong>{{ formatAmount(periodStats.monthly.upstream_receipts) }}</strong>
                </div>
              </div>
            </div>
            <div class="period-stat-group">
              <div class="period-stat-group__title">下游与管理</div>
              <div class="period-stat-list">
                <div class="period-stat-item">
                  <span>签约数量</span>
                  <strong>{{ periodStats.monthly.downstream_mgmt_count }} 单</strong>
                </div>
                <div class="period-stat-item">
                  <span>签约金额</span>
                  <strong>{{ formatAmount(periodStats.monthly.downstream_mgmt_amount) }}</strong>
                </div>
                <div class="period-stat-item">
                  <span>付款金额</span>
                  <strong>{{ formatAmount(periodStats.monthly.downstream_mgmt_payment) }}</strong>
                </div>
                <div class="period-stat-item">
                  <span>无合同费用</span>
                  <strong>{{ formatAmount(periodStats.monthly.non_contract_expense) }}</strong>
                </div>
                <div class="period-stat-item">
                  <span>零星用工</span>
                  <strong>{{ formatAmount(periodStats.monthly.zero_hour_labor) }}</strong>
                </div>
              </div>
            </div>
          </div>
          <div ref="monthChartRef" class="chart-surface chart-surface--period" />
        </div>
      </AppSectionCard>

      <AppSectionCard>
        <template #header>近90天经营表现</template>
        <div class="period-panel">
          <div class="period-stats-grid">
            <div class="period-stat-group">
              <div class="period-stat-group__title">上游合同</div>
              <div class="period-stat-list">
                <div class="period-stat-item">
                  <span>签约数量</span>
                  <strong>{{ periodStats.quarterly.upstream_count }} 单</strong>
                </div>
                <div class="period-stat-item">
                  <span>签约金额</span>
                  <strong>{{ formatAmount(periodStats.quarterly.upstream_amount) }}</strong>
                </div>
                <div class="period-stat-item">
                  <span>回款金额</span>
                  <strong>{{ formatAmount(periodStats.quarterly.upstream_receipts) }}</strong>
                </div>
              </div>
            </div>
            <div class="period-stat-group">
              <div class="period-stat-group__title">下游与管理</div>
              <div class="period-stat-list">
                <div class="period-stat-item">
                  <span>签约数量</span>
                  <strong>{{ periodStats.quarterly.downstream_mgmt_count }} 单</strong>
                </div>
                <div class="period-stat-item">
                  <span>签约金额</span>
                  <strong>{{ formatAmount(periodStats.quarterly.downstream_mgmt_amount) }}</strong>
                </div>
                <div class="period-stat-item">
                  <span>付款金额</span>
                  <strong>{{ formatAmount(periodStats.quarterly.downstream_mgmt_payment) }}</strong>
                </div>
                <div class="period-stat-item">
                  <span>无合同费用</span>
                  <strong>{{ formatAmount(periodStats.quarterly.non_contract_expense) }}</strong>
                </div>
                <div class="period-stat-item">
                  <span>零星用工</span>
                  <strong>{{ formatAmount(periodStats.quarterly.zero_hour_labor) }}</strong>
                </div>
              </div>
            </div>
          </div>
          <div ref="quarterChartRef" class="chart-surface chart-surface--period" />
        </div>
      </AppSectionCard>
    </section>

    <AppSectionCard v-else>
      <template #header>阶段经营表现</template>
      <el-tabs v-model="mobileActiveTab" class="overview-mobile-tabs app-tabs--line">
        <el-tab-pane label="近30天" name="monthly">
          <div class="period-panel period-panel--mobile">
            <div class="period-stats-grid period-stats-grid--single">
              <div class="period-stat-group">
                <div class="period-stat-group__title">上游合同</div>
                <div class="period-stat-list">
                  <div class="period-stat-item">
                    <span>签约数量</span>
                    <strong>{{ periodStats.monthly.upstream_count }} 单</strong>
                  </div>
                  <div class="period-stat-item">
                    <span>签约金额</span>
                    <strong>{{ formatAmount(periodStats.monthly.upstream_amount) }}</strong>
                  </div>
                  <div class="period-stat-item">
                    <span>回款金额</span>
                    <strong>{{ formatAmount(periodStats.monthly.upstream_receipts) }}</strong>
                  </div>
                </div>
              </div>
              <div class="period-stat-group">
                <div class="period-stat-group__title">下游与管理</div>
                <div class="period-stat-list">
                  <div class="period-stat-item">
                    <span>签约数量</span>
                    <strong>{{ periodStats.monthly.downstream_mgmt_count }} 单</strong>
                  </div>
                  <div class="period-stat-item">
                    <span>签约金额</span>
                    <strong>{{ formatAmount(periodStats.monthly.downstream_mgmt_amount) }}</strong>
                  </div>
                  <div class="period-stat-item">
                    <span>付款金额</span>
                    <strong>{{ formatAmount(periodStats.monthly.downstream_mgmt_payment) }}</strong>
                  </div>
                </div>
              </div>
            </div>
            <div ref="mobileMonthChartRef" class="chart-surface chart-surface--mobile" />
          </div>
        </el-tab-pane>
        <el-tab-pane label="近90天" name="quarterly">
          <div class="period-panel period-panel--mobile">
            <div class="period-stats-grid period-stats-grid--single">
              <div class="period-stat-group">
                <div class="period-stat-group__title">上游合同</div>
                <div class="period-stat-list">
                  <div class="period-stat-item">
                    <span>签约数量</span>
                    <strong>{{ periodStats.quarterly.upstream_count }} 单</strong>
                  </div>
                  <div class="period-stat-item">
                    <span>签约金额</span>
                    <strong>{{ formatAmount(periodStats.quarterly.upstream_amount) }}</strong>
                  </div>
                  <div class="period-stat-item">
                    <span>回款金额</span>
                    <strong>{{ formatAmount(periodStats.quarterly.upstream_receipts) }}</strong>
                  </div>
                </div>
              </div>
              <div class="period-stat-group">
                <div class="period-stat-group__title">下游与管理</div>
                <div class="period-stat-list">
                  <div class="period-stat-item">
                    <span>签约数量</span>
                    <strong>{{ periodStats.quarterly.downstream_mgmt_count }} 单</strong>
                  </div>
                  <div class="period-stat-item">
                    <span>签约金额</span>
                    <strong>{{ formatAmount(periodStats.quarterly.downstream_mgmt_amount) }}</strong>
                  </div>
                  <div class="period-stat-item">
                    <span>付款金额</span>
                    <strong>{{ formatAmount(periodStats.quarterly.downstream_mgmt_payment) }}</strong>
                  </div>
                </div>
              </div>
            </div>
            <div ref="mobileQuarterChartRef" class="chart-surface chart-surface--mobile" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </AppSectionCard>

    <section class="overview-chart-grid">
      <AppSectionCard>
        <template #header>合同分类</template>
        <div class="pie-grid">
          <div class="pie-panel">
            <div class="pie-panel__title">合同类别</div>
            <div ref="pieCategoryChartRef" class="chart-surface chart-surface--pie" />
          </div>
          <div class="pie-panel">
            <div class="pie-panel__title">自定类别</div>
            <div ref="pieCompanyChartRef" class="chart-surface chart-surface--pie" />
          </div>
        </div>
      </AppSectionCard>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import echarts from '@/utils/echarts'
import AppMetricCard from '@/components/ui/AppMetricCard.vue'
import AppSectionCard from '@/components/ui/AppSectionCard.vue'
import { useDevice } from '@/composables/useDevice'
import { getStats, getPeriodStats, getPeriodTrend } from '@/api/dashboard'
import { getFinanceTrend } from '@/api/reports'
import { createBarChartOption, createPieChartOption, readChartTheme } from '@/utils/echarts'

const { isMobile } = useDevice()
const mobileActiveTab = ref('monthly')
const currentYear = new Date().getFullYear().toString()

const barChartRef = ref(null)
const pieCategoryChartRef = ref(null)
const pieCompanyChartRef = ref(null)
const monthChartRef = ref(null)
const quarterChartRef = ref(null)
const mobileMonthChartRef = ref(null)
const mobileQuarterChartRef = ref(null)

let barChart = null
let pieCategoryChart = null
let pieCompanyChart = null
let monthChart = null
let quarterChart = null
let mobileMonthChart = null
let mobileQuarterChart = null

let monthTrendData = null
let quarterTrendData = null

const cardData = ref([
  { eyebrow: '年度经营', badge: '签约', tone: 'primary', title: '年度上游签约', value: 0, count: 0, description: '累计签约总额' },
  { eyebrow: '年度经营', badge: '成本', tone: 'warning', title: '年度下游签约', value: 0, count: 0, description: '累计支出预算' },
  { eyebrow: '年度经营', badge: '收入', tone: 'success', title: '年度回款总额', value: 0, description: '实际到账金额' },
  { eyebrow: '年度经营', badge: '支出', tone: 'danger', title: '年度付款总额', value: 0, description: '实际支出金额' }
])

const periodStats = ref({
  monthly: {
    upstream_count: 0,
    upstream_amount: 0,
    upstream_receipts: 0,
    downstream_mgmt_count: 0,
    downstream_mgmt_amount: 0,
    downstream_mgmt_payment: 0,
    non_contract_expense: 0,
    zero_hour_labor: 0
  },
  quarterly: {
    upstream_count: 0,
    upstream_amount: 0,
    upstream_receipts: 0,
    downstream_mgmt_count: 0,
    downstream_mgmt_amount: 0,
    downstream_mgmt_payment: 0,
    non_contract_expense: 0,
    zero_hour_labor: 0
  }
})

const metricCards = computed(() => cardData.value.map((item) => ({
  ...item,
  value: item.count !== undefined
    ? `${item.count} 单`
    : formatAmount(item.value)
})))

const overviewSummaryCards = computed(() => [
  {
    title: '近30天上游签约',
    value: `${periodStats.value.monthly.upstream_count} 单`,
    meta: formatAmount(periodStats.value.monthly.upstream_amount)
  },
  {
    title: '近30天回款',
    value: formatAmount(periodStats.value.monthly.upstream_receipts),
    meta: '上游到账金额'
  },
  {
    title: '近90天下游及管理',
    value: `${periodStats.value.quarterly.downstream_mgmt_count} 单`,
    meta: formatAmount(periodStats.value.quarterly.downstream_mgmt_amount)
  },
  {
    title: '近90天支出',
    value: formatAmount(
      periodStats.value.quarterly.downstream_mgmt_payment +
      periodStats.value.quarterly.non_contract_expense +
      periodStats.value.quarterly.zero_hour_labor
    ),
    meta: '管理、费用与零星用工'
  }
])

watch(mobileActiveTab, (value) => {
  nextTick(() => {
    if (value === 'monthly') {
      if (mobileMonthChart) mobileMonthChart.resize()
      else if (monthTrendData) initMonthChart(monthTrendData)
      return
    }

    if (mobileQuarterChart) mobileQuarterChart.resize()
    else if (quarterTrendData) initQuarterChart(quarterTrendData)
  })
})

watch(isMobile, async () => {
  disposePeriodCharts()
  await nextTick()

  if (monthTrendData) {
    initMonthChart(monthTrendData)
  }

  if (quarterTrendData) {
    initQuarterChart(quarterTrendData)
  }

  handleResize()
})

function formatWan(value) {
  if (!value) return '0.00'
  return (Number(value) / 10000).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

function formatAmount(value) {
  return `¥ ${formatWan(value)} 万`
}

function formatTrendLabel(value, sliceStart = 5) {
  if (!value || typeof value !== 'string') return value
  return value.length > sliceStart ? value.substring(sliceStart) : value
}

function buildExpenseSeries(data, useLaborKey = 'labor', incomeName = '收入') {
  const theme = readChartTheme()
  const expenseBreakdown = data?.expense_breakdown || {}

  return [
    {
      name: incomeName,
      data: (data?.income || []).map((value) => Number((value / 10000).toFixed(2))),
      color: theme.success
    },
    {
      name: '下游合同',
      stack: 'expense',
      data: (expenseBreakdown.downstream || []).map((value) => Number((value / 10000).toFixed(2))),
      color: theme.danger
    },
    {
      name: '管理合同',
      stack: 'expense',
      data: (expenseBreakdown.management || []).map((value) => Number((value / 10000).toFixed(2))),
      color: theme.warning
    },
    {
      name: '无合同费用',
      stack: 'expense',
      data: (expenseBreakdown.non_contract || []).map((value) => Number((value / 10000).toFixed(2))),
      color: theme.info
    },
    {
      name: '零星用工',
      stack: 'expense',
      data: (expenseBreakdown[useLaborKey] || []).map((value) => Number((value / 10000).toFixed(2))),
      color: theme.primary
    }
  ]
}

function createTrendBarOption({ categories, series, labelSliceStart = 5, mobile = false, legendNames = [] }) {
  const theme = readChartTheme()
  const option = createBarChartOption({ categories, series })

  option.tooltip.formatter = (params) => {
    if (!Array.isArray(params) || !params.length) return ''
    const lines = [`${params[0].axisValueLabel || params[0].name}`]
    params.forEach((item) => {
      const value = Number(item.value)
      if (!Number.isNaN(value) && value > 0) {
        lines.push(`${item.marker}${item.seriesName}: ${value.toFixed(2)} 万元`)
      }
    })
    return lines.length > 1 ? lines.join('<br/>') : ''
  }
  option.legend.data = legendNames.length ? legendNames : series.map((item) => item.name)
  option.legend.type = mobile ? 'scroll' : 'plain'
  option.legend.textStyle = { color: theme.text, fontSize: mobile ? 10 : 12 }
  option.grid.top = mobile ? '14%' : '12%'
  option.grid.bottom = mobile ? '88px' : '72px'
  option.grid.left = mobile ? '11%' : '8%'
  option.grid.right = '4%'
  option.xAxis.axisLabel.interval = 'auto'
  option.xAxis.axisLabel.rotate = mobile ? 36 : 0
  option.xAxis.axisLabel.formatter = (value) => formatTrendLabel(value, labelSliceStart)
  option.yAxis.name = '金额 (万元)'
  option.yAxis.nameTextStyle = { color: theme.text, padding: [0, 0, 6, 0] }

  return option
}

function createContractPieOption(title, data) {
  const theme = readChartTheme()
  const option = createPieChartOption({ title, data })

  option.tooltip = {
    trigger: 'item',
    confine: true,
    formatter: (params) => `${params.name}: ${formatWan(params.value)} 万元 (${params.percent}%)`
  }
  option.legend.left = 'center'
  option.legend.width = '92%'
  option.legend.itemWidth = 10
  option.legend.itemHeight = 10
  option.legend.itemGap = 12
  option.legend.textStyle = { color: theme.text, fontSize: 11, lineHeight: 14 }
  option.title.textStyle.fontSize = 13
  option.series[0].name = title
  option.series[0].radius = ['36%', '62%']
  option.series[0].center = ['50%', '40%']
  option.series[0].itemStyle = {
    borderRadius: 6,
    borderColor: theme.panel,
    borderWidth: 2
  }

  return option
}

async function fetchData() {
  try {
    const [statsRes, trendRes, periodRes, monthTrendRes, quarterTrendRes] = await Promise.all([
      getStats(),
      getFinanceTrend(currentYear),
      getPeriodStats(),
      getPeriodTrend('monthly'),
      getPeriodTrend('quarterly')
    ])

    const { cards, charts } = statsRes

    cardData.value[0].count = cards.annual_upstream_count
    cardData.value[0].value = cards.annual_upstream_amount
    cardData.value[1].count = cards.annual_down_mgmt_count
    cardData.value[1].value = cards.annual_down_mgmt_amount
    cardData.value[2].value = cards.annual_receipts_amount
    cardData.value[3].value = cards.annual_payments_amount
    periodStats.value = periodRes

    monthTrendData = monthTrendRes
    quarterTrendData = quarterTrendRes

    initAnnualChart(trendRes)
    if (charts.pie_category) initCategoryPie(charts.pie_category)
    if (charts.pie_company) initCompanyPie(charts.pie_company)
    initMonthChart(monthTrendData)
    initQuarterChart(quarterTrendData)
  } catch (error) {
    console.error(error)
    ElMessage.error('获取仪表盘数据失败')
  }
}

function initAnnualChart(data) {
  if (!barChartRef.value) return
  if (barChart) barChart.dispose()

    barChart = echarts.init(barChartRef.value)
  barChart.setOption(createTrendBarOption({
    categories: data?.months || [],
    series: buildExpenseSeries(data, 'zero_hour_labor', '月度收入'),
    labelSliceStart: 5,
    mobile: isMobile.value,
    legendNames: ['月度收入', '下游合同', '管理合同', '无合同费用', '零星用工']
  }))
}

function initMonthChart(data) {
  if (monthChartRef.value) {
    if (monthChart) monthChart.dispose()
    monthChart = echarts.init(monthChartRef.value)
    monthChart.setOption(createTrendBarOption({
      categories: data?.dates || [],
      series: buildExpenseSeries(data, 'labor'),
      labelSliceStart: 5,
      legendNames: ['收入', '下游合同', '管理合同', '无合同费用', '零星用工']
    }))
  }

  if (mobileMonthChartRef.value) {
    if (mobileMonthChart) mobileMonthChart.dispose()
    mobileMonthChart = echarts.init(mobileMonthChartRef.value)
    mobileMonthChart.setOption(createTrendBarOption({
      categories: data?.dates || [],
      series: buildExpenseSeries(data, 'labor'),
      labelSliceStart: 5,
      mobile: true,
      legendNames: ['收入', '下游合同', '管理合同', '无合同费用', '零星用工']
    }))
  }
}

function initQuarterChart(data) {
  if (quarterChartRef.value) {
    if (quarterChart) quarterChart.dispose()
    quarterChart = echarts.init(quarterChartRef.value)
    quarterChart.setOption(createTrendBarOption({
      categories: data?.dates || [],
      series: buildExpenseSeries(data, 'labor'),
      labelSliceStart: 5,
      legendNames: ['收入', '下游合同', '管理合同', '无合同费用', '零星用工']
    }))
  }

  if (mobileQuarterChartRef.value) {
    if (mobileQuarterChart) mobileQuarterChart.dispose()
    mobileQuarterChart = echarts.init(mobileQuarterChartRef.value)
    mobileQuarterChart.setOption(createTrendBarOption({
      categories: data?.dates || [],
      series: buildExpenseSeries(data, 'labor'),
      labelSliceStart: 5,
      mobile: true,
      legendNames: ['收入', '下游合同', '管理合同', '无合同费用', '零星用工']
    }))
  }
}

function initCategoryPie(data) {
  if (!pieCategoryChartRef.value) return
  if (pieCategoryChart) pieCategoryChart.dispose()

  pieCategoryChart = echarts.init(pieCategoryChartRef.value)
  pieCategoryChart.setOption(createContractPieOption('合同类别', data))
}

function initCompanyPie(data) {
  if (!pieCompanyChartRef.value) return
  if (pieCompanyChart) pieCompanyChart.dispose()

  pieCompanyChart = echarts.init(pieCompanyChartRef.value)
  pieCompanyChart.setOption(createContractPieOption('自定类别', data))
}

function disposeChartInstance(instance) {
  if (instance) {
    instance.dispose()
  }
  return null
}

function disposePeriodCharts() {
  monthChart = disposeChartInstance(monthChart)
  quarterChart = disposeChartInstance(quarterChart)
  mobileMonthChart = disposeChartInstance(mobileMonthChart)
  mobileQuarterChart = disposeChartInstance(mobileQuarterChart)
}

function handleResize() {
  barChart && barChart.resize()
  pieCategoryChart && pieCategoryChart.resize()
  pieCompanyChart && pieCompanyChart.resize()
  monthChart && monthChart.resize()
  quarterChart && quarterChart.resize()
  mobileMonthChart && mobileMonthChart.resize()
  mobileQuarterChart && mobileQuarterChart.resize()
}

onMounted(() => {
  nextTick(() => {
    fetchData()
    window.addEventListener('resize', handleResize)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  barChart = disposeChartInstance(barChart)
  pieCategoryChart = disposeChartInstance(pieCategoryChart)
  pieCompanyChart = disposeChartInstance(pieCompanyChart)
  disposePeriodCharts()
})
</script>

<style scoped lang="scss">
.overview-page {
  display: grid;
  gap: var(--space-6);
}

.dashboard-metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
  align-items: stretch;
}

.dashboard-metric-grid :deep(.app-metric-card) {
  min-height: 208px;
  border-radius: 22px;
}

.metric-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.metric-badge--primary {
  background: var(--brand-primary-soft);
  color: var(--brand-primary-strong);
}

.metric-badge--warning {
  background: color-mix(in srgb, var(--status-warning) 14%, transparent);
  color: var(--status-warning);
}

.metric-badge--success {
  background: color-mix(in srgb, var(--status-success) 14%, transparent);
  color: var(--status-success);
}

.metric-badge--danger {
  background: color-mix(in srgb, var(--status-danger) 14%, transparent);
  color: var(--status-danger);
}

.period-grid,
.overview-summary-grid,
.overview-chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.overview-summary-grid :deep(.app-section-card),
.period-grid :deep(.app-section-card),
.overview-chart-grid :deep(.app-section-card) {
  border-radius: 24px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.summary-card {
  display: grid;
  gap: 10px;
  padding: var(--space-5);
  border: 1px solid var(--border-subtle);
  border-radius: 20px;
  background: color-mix(in srgb, var(--surface-panel) 80%, var(--surface-panel-muted) 20%);
}

.summary-card__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.summary-card__value {
  font-size: clamp(22px, 3vw, 30px);
  line-height: 1.08;
  color: var(--text-primary);
}

.summary-card__meta {
  font-size: 12px;
  color: var(--text-muted);
}

.period-panel {
  display: grid;
  gap: var(--space-5);
}

.period-panel--mobile {
  gap: var(--space-4);
}

.period-stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.period-stats-grid--single {
  grid-template-columns: 1fr;
}

.period-stat-group {
  padding: var(--space-5);
  border: 1px solid var(--border-subtle);
  border-radius: 20px;
  background: color-mix(in srgb, var(--surface-panel) 78%, var(--surface-panel-muted) 22%);
}

.period-stat-group__title {
  margin-bottom: 14px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}

.period-stat-list {
  display: grid;
  gap: 10px;
}

.period-stat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  font-size: 14px;
  color: var(--text-secondary);
}

.period-stat-item strong {
  color: var(--text-primary);
  text-align: right;
}

.chart-surface {
  width: 100%;
  min-width: 0;
}

.chart-surface--annual {
  height: 340px;
}

.chart-surface--period {
  height: 300px;
}

.chart-surface--mobile {
  height: 280px;
}

.chart-surface--pie {
  height: 320px;
}

.pie-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.pie-panel {
  min-width: 0;
  overflow: hidden;
}

.pie-panel__title {
  margin-bottom: 10px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

@media (max-width: 1279px) {
  .dashboard-metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .period-grid,
  .overview-summary-grid,
  .overview-chart-grid,
  .pie-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .overview-page {
    gap: var(--space-4);
  }

  .dashboard-metric-grid {
    grid-template-columns: 1fr;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .metric-badge {
    min-height: 24px;
    padding-inline: 8px;
    font-size: 11px;
  }

  .period-stat-group {
    padding: var(--space-4);
  }

  .period-stat-item {
    align-items: flex-start;
    flex-direction: column;
    gap: 4px;
  }

  .chart-surface--annual,
  .chart-surface--period,
  .chart-surface--pie,
  .chart-surface--mobile {
    height: 280px;
  }
}
</style>
