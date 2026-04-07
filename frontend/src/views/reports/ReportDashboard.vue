<template>
  <div class="report-dashboard-shell">
    <AppPageHeader class="report-dashboard-header" title="报表统计" />

    <div class="report-dashboard-panels">
    <AppWorkspacePanel panel-class="report-dashboard-panel report-dashboard-panel--cost">
    <AppSectionCard>
      <template #header>月度 / 季度成本报表</template>
      <AppFilterBar>
        <el-date-picker
          v-model="costMonth"
          class="filter-control--time"
          type="month"
          value-format="YYYY-MM"
          format="YYYY年MM月"
          placeholder="选择月份"
          clearable
        />
        <template #actions>
        <el-button type="primary" :loading="costLoading" @click="handleQueryCostReport">查询报表</el-button>
        <el-button type="primary" plain :loading="costExportLoading" @click="handleExportCostReport">导出</el-button>
        </template>
      </AppFilterBar>

      <el-tabs v-model="costActiveTab" class="cost-tabs app-tabs--line">
        <el-tab-pane label="月度成本报表" name="monthly">
          <div class="cost-title">{{ monthlyTitle }}</div>
          <AppDataTable v-if="monthlyRowCount > 0">
            <el-table
              :data="monthlyTableData"
              border
              v-loading="costLoading"
              :row-class-name="costRowClassName"
              :cell-style="costCellStyle"
              class="cost-report-table"
            >
              <el-table-column prop="company_category" label="公司合同分类" fixed min-width="140" />
              <el-table-column label="上游合同">
                <el-table-column prop="upstream_contract_amount" label="签约金额" min-width="120" :formatter="amountFormatter" />
                <el-table-column prop="upstream_receivable" label="应收款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="upstream_invoice" label="挂账" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="upstream_receipt" label="收款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="upstream_settlement" label="结算" min-width="110" :formatter="amountFormatter" />
              </el-table-column>
              <el-table-column label="下游及管理合同">
                <el-table-column prop="down_mgmt_contract_amount" label="签约金额" min-width="120" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_payable" label="应付款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_invoice" label="挂账" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_payment" label="付款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_settlement" label="结算" min-width="110" :formatter="amountFormatter" />
              </el-table-column>
              <el-table-column prop="zero_hour_labor" label="零星用工" min-width="120" :formatter="amountFormatter" />
              <el-table-column prop="non_contract_expense" label="无合同费用" min-width="120" :formatter="amountFormatter" />
            </el-table>
          </AppDataTable>
          <AppEmptyState
            v-else-if="!costLoading"
            title="暂无月度成本数据"
          />
        </el-tab-pane>

        <el-tab-pane label="季度成本报表" name="quarterly">
          <div class="cost-title">{{ quarterlyTitle }}</div>
          <AppDataTable v-if="quarterlyRowCount > 0">
            <el-table
              :data="quarterlyTableData"
              border
              v-loading="costLoading"
              :row-class-name="costRowClassName"
              :cell-style="costCellStyle"
              class="cost-report-table"
            >
              <el-table-column prop="company_category" label="公司合同分类" fixed min-width="140" />
              <el-table-column label="上游合同">
                <el-table-column prop="upstream_contract_amount" label="签约金额" min-width="120" :formatter="amountFormatter" />
                <el-table-column prop="upstream_receivable" label="应收款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="upstream_invoice" label="挂账" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="upstream_receipt" label="收款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="upstream_settlement" label="结算" min-width="110" :formatter="amountFormatter" />
              </el-table-column>
              <el-table-column label="下游及管理合同">
                <el-table-column prop="down_mgmt_contract_amount" label="签约金额" min-width="120" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_payable" label="应付款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_invoice" label="挂账" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_payment" label="付款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_settlement" label="结算" min-width="110" :formatter="amountFormatter" />
              </el-table-column>
              <el-table-column prop="zero_hour_labor" label="零星用工" min-width="120" :formatter="amountFormatter" />
              <el-table-column prop="non_contract_expense" label="无合同费用" min-width="120" :formatter="amountFormatter" />
            </el-table>
          </AppDataTable>
          <AppEmptyState
            v-else-if="!costLoading"
            title="暂无季度成本数据"
          />
        </el-tab-pane>

        <el-tab-pane label="半年度成本报表" name="half_yearly">
          <div class="cost-title">{{ halfYearlyTitle }}</div>
          <AppDataTable v-if="halfYearlyRowCount > 0">
            <el-table
              :data="halfYearlyTableData"
              border
              v-loading="costLoading"
              :row-class-name="costRowClassName"
              :cell-style="costCellStyle"
              class="cost-report-table"
            >
              <el-table-column prop="company_category" label="公司合同分类" fixed min-width="140" />
              <el-table-column label="上游合同">
                <el-table-column prop="upstream_contract_amount" label="签约金额" min-width="120" :formatter="amountFormatter" />
                <el-table-column prop="upstream_receivable" label="应收款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="upstream_invoice" label="挂账" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="upstream_receipt" label="收款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="upstream_settlement" label="结算" min-width="110" :formatter="amountFormatter" />
              </el-table-column>
              <el-table-column label="下游及管理合同">
                <el-table-column prop="down_mgmt_contract_amount" label="签约金额" min-width="120" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_payable" label="应付款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_invoice" label="挂账" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_payment" label="付款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_settlement" label="结算" min-width="110" :formatter="amountFormatter" />
              </el-table-column>
              <el-table-column prop="zero_hour_labor" label="零星用工" min-width="120" :formatter="amountFormatter" />
              <el-table-column prop="non_contract_expense" label="无合同费用" min-width="120" :formatter="amountFormatter" />
            </el-table>
          </AppDataTable>
          <AppEmptyState
            v-else-if="!costLoading"
            title="暂无半年度成本数据"
          />
        </el-tab-pane>

        <el-tab-pane label="年度成本报表" name="yearly">
          <div class="cost-title">{{ yearlyTitle }}</div>
          <AppDataTable v-if="yearlyRowCount > 0">
            <el-table
              :data="yearlyTableData"
              border
              v-loading="costLoading"
              :row-class-name="costRowClassName"
              :cell-style="costCellStyle"
              class="cost-report-table"
            >
              <el-table-column prop="company_category" label="公司合同分类" fixed min-width="140" />
              <el-table-column label="上游合同">
                <el-table-column prop="upstream_contract_amount" label="签约金额" min-width="120" :formatter="amountFormatter" />
                <el-table-column prop="upstream_receivable" label="应收款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="upstream_invoice" label="挂账" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="upstream_receipt" label="收款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="upstream_settlement" label="结算" min-width="110" :formatter="amountFormatter" />
              </el-table-column>
              <el-table-column label="下游及管理合同">
                <el-table-column prop="down_mgmt_contract_amount" label="签约金额" min-width="120" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_payable" label="应付款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_invoice" label="挂账" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_payment" label="付款" min-width="110" :formatter="amountFormatter" />
                <el-table-column prop="down_mgmt_settlement" label="结算" min-width="110" :formatter="amountFormatter" />
              </el-table-column>
              <el-table-column prop="zero_hour_labor" label="零星用工" min-width="120" :formatter="amountFormatter" />
              <el-table-column prop="non_contract_expense" label="无合同费用" min-width="120" :formatter="amountFormatter" />
            </el-table>
          </AppDataTable>
          <AppEmptyState
            v-else-if="!costLoading"
            title="暂无年度成本数据"
          />
        </el-tab-pane>
      </el-tabs>
    </AppSectionCard>
    </AppWorkspacePanel>

    <AppWorkspacePanel panel-class="report-dashboard-panel report-dashboard-panel--exports">
    <AppSectionCard>
      <template #header>数据查询与导出</template>
      <div class="report-export-grid">
        <article v-for="card in exportCards" :key="card.title" class="report-export-card">
          <div class="report-export-card__header">
            <h3>{{ card.title }}</h3>
          </div>

          <AppFilterBar class="report-export-card__filters" :class="`report-export-card__filters--${card.type}`">
            <template v-if="card.type === 'daterange'">
              <AppRangeField
                v-model="card.model.value"
                class="filter-control--range-wide"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
              />
            </template>
            <template v-else-if="card.type === 'daterange-with-status'">
              <AppRangeField
                v-model="exportFilters.dateRange"
                class="filter-control--range-wide"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
              />
              <el-select v-model="exportFilters.status" placeholder="合同状态">
                <el-option label="全部" value="全部" />
                <el-option label="执行中" value="执行中" />
                <el-option label="已完工" value="已完工" />
                <el-option label="已结算" value="已结算" />
                <el-option label="质保期到期" value="质保期到期" />
                <el-option label="合同终止" value="合同终止" />
                <el-option label="合同中止" value="合同中止" />
              </el-select>
            </template>
            <template v-else>
              <el-input
                v-model="card.model.value"
                placeholder="请输入合同序号/编号/名称"
                clearable
              />
            </template>
            <template #actions>
              <el-button type="primary" plain :loading="card.loading.value" @click="card.action">导出</el-button>
            </template>
          </AppFilterBar>
        </article>
      </div>
    </AppSectionCard>
    </AppWorkspacePanel>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppSectionCard from '@/components/ui/AppSectionCard.vue'
import AppFilterBar from '@/components/ui/AppFilterBar.vue'
import AppDataTable from '@/components/ui/AppDataTable.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import AppRangeField from '@/components/ui/AppRangeField.vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'
import { buildExportParams } from '@/views/reports/reportDashboard.helpers'
import {
  getCostMonthlyQuarterlyReport,
  downloadCostMonthlyQuarterlyReport,
  downloadComprehensiveReport,
  downloadReceivablesReport,
  downloadPayablesReport,
  downloadUpstreamInvoicesReport,
  downloadDownstreamInvoicesReport,
  downloadUpstreamReceiptsReport,
  downloadDownstreamPaymentsReport,
  downloadExpensePaymentsReport,
  downloadUpstreamSettlementsReport,
  downloadDownstreamSettlementsReport,
  downloadAssociationReport
} from '@/api/reports'

const COST_FIELDS = [
  'upstream_contract_amount',
  'upstream_receivable',
  'upstream_invoice',
  'upstream_receipt',
  'upstream_settlement',
  'down_mgmt_contract_amount',
  'down_mgmt_payable',
  'down_mgmt_invoice',
  'down_mgmt_payment',
  'down_mgmt_settlement',
  'zero_hour_labor',
  'non_contract_expense'
]

const now = new Date()
const currentMonthValue = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
const costMonth = ref(currentMonthValue)
const costLoading = ref(false)
const costExportLoading = ref(false)
const costActiveTab = ref('monthly')

function buildEmptyCostRecord(companyCategory = '合计') {
  const record = { company_category: companyCategory }
  COST_FIELDS.forEach((key) => {
    record[key] = 0
  })
  return record
}

const costReportData = ref({
  period: {
    year: now.getFullYear(),
    month: now.getMonth() + 1,
    quarter: Math.floor(now.getMonth() / 3) + 1,
    half_year: now.getMonth() + 1 <= 6 ? 1 : 2
  },
  monthly: { rows: [], total: buildEmptyCostRecord('合计') },
  quarterly: { rows: [], total: buildEmptyCostRecord('合计') },
  half_yearly: { rows: [], total: buildEmptyCostRecord('合计') },
  yearly: { rows: [], total: buildEmptyCostRecord('合计') }
})

const monthlyTitle = computed(() => {
  const p = costReportData.value.period || {}
  if (!p.year || !p.month) return '月度成本报表'
  return `${p.year}年${p.month}月 月度成本报表`
})

const quarterlyTitle = computed(() => {
  const p = costReportData.value.period || {}
  if (!p.year || !p.quarter) return '季度成本报表'
  return `${p.year}年第${p.quarter}季度 成本报表`
})

const halfYearlyTitle = computed(() => {
  const p = costReportData.value.period || {}
  if (!p.year || !p.half_year) return '半年度成本报表'
  return `${p.year}年${p.half_year === 1 ? '上半年' : '下半年'} 成本报表`
})

const yearlyTitle = computed(() => {
  const p = costReportData.value.period || {}
  if (!p.year) return '年度成本报表'
  return `${p.year}年 年度成本报表`
})

const monthlyTableData = computed(() => {
  const rows = (costReportData.value.monthly?.rows || []).map((row) => ({ ...buildEmptyCostRecord(row.company_category), ...row, is_total: false }))
  const total = { ...buildEmptyCostRecord('合计'), ...(costReportData.value.monthly?.total || {}), company_category: '合计', is_total: true }
  return [...rows, total]
})
const monthlyRowCount = computed(() => costReportData.value.monthly?.rows?.length || 0)

const quarterlyTableData = computed(() => {
  const rows = (costReportData.value.quarterly?.rows || []).map((row) => ({ ...buildEmptyCostRecord(row.company_category), ...row, is_total: false }))
  const total = { ...buildEmptyCostRecord('合计'), ...(costReportData.value.quarterly?.total || {}), company_category: '合计', is_total: true }
  return [...rows, total]
})
const quarterlyRowCount = computed(() => costReportData.value.quarterly?.rows?.length || 0)

const halfYearlyTableData = computed(() => {
  const rows = (costReportData.value.half_yearly?.rows || []).map((row) => ({ ...buildEmptyCostRecord(row.company_category), ...row, is_total: false }))
  const total = { ...buildEmptyCostRecord('合计'), ...(costReportData.value.half_yearly?.total || {}), company_category: '合计', is_total: true }
  return [...rows, total]
})
const halfYearlyRowCount = computed(() => costReportData.value.half_yearly?.rows?.length || 0)

const yearlyTableData = computed(() => {
  const rows = (costReportData.value.yearly?.rows || []).map((row) => ({ ...buildEmptyCostRecord(row.company_category), ...row, is_total: false }))
  const total = { ...buildEmptyCostRecord('合计'), ...(costReportData.value.yearly?.total || {}), company_category: '合计', is_total: true }
  return [...rows, total]
})
const yearlyRowCount = computed(() => costReportData.value.yearly?.rows?.length || 0)

function parseYearMonth() {
  const selected = costMonth.value || currentMonthValue
  if (!selected) return { year: now.getFullYear(), month: now.getMonth() + 1 }
  const [yearStr, monthStr] = selected.split('-')
  const year = Number(yearStr)
  const month = Number(monthStr)
  if (!year || !month || month < 1 || month > 12) {
    return { year: now.getFullYear(), month: now.getMonth() + 1 }
  }
  return { year, month }
}

async function handleQueryCostReport() {
  costLoading.value = true
  try {
    const { year, month } = parseYearMonth()
    const res = await getCostMonthlyQuarterlyReport(year, month)
    costReportData.value = {
      period: res.period || {
        year,
        month,
        quarter: Math.floor((month - 1) / 3) + 1,
        half_year: month <= 6 ? 1 : 2
      },
      monthly: {
        rows: res.monthly?.rows || [],
        total: { ...buildEmptyCostRecord('合计'), ...(res.monthly?.total || {}) }
      },
      quarterly: {
        rows: res.quarterly?.rows || [],
        total: { ...buildEmptyCostRecord('合计'), ...(res.quarterly?.total || {}) }
      },
      half_yearly: {
        rows: res.half_yearly?.rows || [],
        total: { ...buildEmptyCostRecord('合计'), ...(res.half_yearly?.total || {}) }
      },
      yearly: {
        rows: res.yearly?.rows || [],
        total: { ...buildEmptyCostRecord('合计'), ...(res.yearly?.total || {}) }
      }
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('成本报表查询失败')
  } finally {
    costLoading.value = false
  }
}

async function handleExportCostReport() {
  costExportLoading.value = true
  try {
    const { year, month } = parseYearMonth()
    const res = await downloadCostMonthlyQuarterlyReport({ year, month })
    downloadFile(res, `月度季度成本报表_${year}年${String(month).padStart(2, '0')}月.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    costExportLoading.value = false
  }
}

function amountFormatter(_row, _column, value) {
  const amount = Number(value)
  if (!Number.isFinite(amount)) {
    return '0.00'
  }
  return amount.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const costRowClassName = ({ row }) => (row.is_total ? 'cost-total-row' : '')

function costCellStyle({ column }) {
  if (COST_FIELDS.includes(column.property)) {
    return { textAlign: 'right' }
  }
  return {}
}

const exportFilters = ref({
  dateRange: [],
  status: '全部'
})
const exportLoading = ref(false)
const recDateRange = ref([])
const payDateRange = ref([])
const upInvDateRange = ref([])
const downInvDateRange = ref([])
const upReceiptDateRange = ref([])
const downPayDateRange = ref([])
const expPayDateRange = ref([])
const upSettlementDateRange = ref([])
const downSettlementDateRange = ref([])
const assocQuery = ref('')

const recLoading = ref(false)
const payLoading = ref(false)
const upInvLoading = ref(false)
const downInvLoading = ref(false)
const upReceiptLoading = ref(false)
const downPayLoading = ref(false)
const expPayLoading = ref(false)
const upSettlementLoading = ref(false)
const downSettlementLoading = ref(false)
const assocLoading = ref(false)

async function handleExport() {
  exportLoading.value = true
  try {
    const params = buildExportParams({
      dateRange: exportFilters.value.dateRange,
      status: exportFilters.value.status
    })
    const res = await downloadComprehensiveReport(params)
    downloadFile(res, `上游合同综合报表_${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    exportLoading.value = false
  }
}

async function handleExportRec() {
  recLoading.value = true
  try {
    const params = buildExportParams({ dateRange: recDateRange.value })
    const res = await downloadReceivablesReport(params)
    downloadFile(res, `上游合同应收款明细_${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    recLoading.value = false
  }
}

async function handleExportPay() {
  payLoading.value = true
  try {
    const params = buildExportParams({ dateRange: payDateRange.value })
    const res = await downloadPayablesReport(params)
    downloadFile(res, `下游及管理合同应付款明细_${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    payLoading.value = false
  }
}

async function handleExportUpInv() {
  upInvLoading.value = true
  try {
    const params = buildExportParams({ dateRange: upInvDateRange.value })
    const res = await downloadUpstreamInvoicesReport(params)
    downloadFile(res, `上游合同挂账报表_${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    upInvLoading.value = false
  }
}

async function handleExportDownInv() {
  downInvLoading.value = true
  try {
    const params = buildExportParams({ dateRange: downInvDateRange.value })
    const res = await downloadDownstreamInvoicesReport(params)
    downloadFile(res, `下游及管理合同挂账报表_${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    downInvLoading.value = false
  }
}

async function handleExportUpReceipt() {
  upReceiptLoading.value = true
  try {
    const params = buildExportParams({ dateRange: upReceiptDateRange.value })
    const res = await downloadUpstreamReceiptsReport(params)
    downloadFile(res, `上游合同收款报表_${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    upReceiptLoading.value = false
  }
}

async function handleExportDownPay() {
  downPayLoading.value = true
  try {
    const params = buildExportParams({ dateRange: downPayDateRange.value })
    const res = await downloadDownstreamPaymentsReport(params)
    downloadFile(res, `下游及管理合同付款报表_${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    downPayLoading.value = false
  }
}

async function handleExportExpPay() {
  expPayLoading.value = true
  try {
    const params = buildExportParams({ dateRange: expPayDateRange.value })
    const res = await downloadExpensePaymentsReport(params)
    downloadFile(res, `无合同费用付款报表_${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    expPayLoading.value = false
  }
}

async function handleExportUpSettlement() {
  upSettlementLoading.value = true
  try {
    const params = buildExportParams({ dateRange: upSettlementDateRange.value })
    const res = await downloadUpstreamSettlementsReport(params)
    downloadFile(res, `上游合同结算报表_${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    upSettlementLoading.value = false
  }
}

async function handleExportDownSettlement() {
  downSettlementLoading.value = true
  try {
    const params = buildExportParams({ dateRange: downSettlementDateRange.value })
    const res = await downloadDownstreamSettlementsReport(params)
    downloadFile(res, `下游及管理合同结算报表_${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    downSettlementLoading.value = false
  }
}

async function handleExportAssociation() {
  assocLoading.value = true
  try {
    const params = {
      query: assocQuery.value
    }
    const res = await downloadAssociationReport(params)
    downloadFile(res, `上下游合同关联报表_${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    assocLoading.value = false
  }
}

const exportCards = computed(() => [
  {
    title: '上游合同综合报表导出',
    description: '按时间范围与合同状态导出综合统计结果。',
    footnote: '导出内容包含：上游合同基础信息、财务累计数据，以及关联的下游、管理、无合同费用统计。',
    type: 'daterange-with-status',
    loading: exportLoading,
    action: handleExport
  },
  {
    title: '上下游合同关联报表导出',
    description: '通过合同编号、名称或序号快速定位关联关系。',
    footnote: '导出内容包含：上游合同及其关联的下游、管理合同与无合同费用明细。',
    type: 'query',
    model: assocQuery,
    loading: assocLoading,
    action: handleExportAssociation
  },
  {
    title: '上游合同应收款报表导出',
    description: '筛选应收时间范围，导出应收款记录。',
    footnote: '导出内容包含：金额、日期、备注等应收款明细。',
    type: 'daterange',
    model: recDateRange,
    loading: recLoading,
    action: handleExportRec
  },
  {
    title: '下游及管理合同应付款报表导出',
    description: '按应付时间导出付款记录。',
    footnote: '导出内容包含：金额、日期、备注等应付款明细。',
    type: 'daterange',
    model: payDateRange,
    loading: payLoading,
    action: handleExportPay
  },
  {
    title: '上游合同挂账报表导出',
    description: '导出上游挂账与开票记录。',
    footnote: '导出内容包含：金额、日期、发票号、备注等字段。',
    type: 'daterange',
    model: upInvDateRange,
    loading: upInvLoading,
    action: handleExportUpInv
  },
  {
    title: '下游及管理合同挂账报表导出',
    description: '导出下游及管理合同挂账与收票记录。',
    footnote: '导出内容包含：金额、日期、发票号、备注等字段。',
    type: 'daterange',
    model: downInvDateRange,
    loading: downInvLoading,
    action: handleExportDownInv
  },
  {
    title: '上游合同收款报表导出',
    description: '按收款时间范围导出到账记录。',
    footnote: '导出内容包含：金额、日期、方式、备注等收款明细。',
    type: 'daterange',
    model: upReceiptDateRange,
    loading: upReceiptLoading,
    action: handleExportUpReceipt
  },
  {
    title: '下游及管理合同付款报表导出',
    description: '按付款时间范围导出实际付款记录。',
    footnote: '导出内容包含：金额、日期、方式、备注等付款明细。',
    type: 'daterange',
    model: downPayDateRange,
    loading: downPayLoading,
    action: handleExportDownPay
  },
  {
    title: '无合同费用付款报表导出',
    description: '导出无合同费用支出记录。',
    footnote: '导出内容包含：金额、日期、类别、经办人、备注等字段。',
    type: 'daterange',
    model: expPayDateRange,
    loading: expPayLoading,
    action: handleExportExpPay
  },
  {
    title: '上游合同结算报表导出',
    description: '导出上游合同结算与完工记录。',
    footnote: '导出内容包含：结算金额、完工日期、备注等字段。',
    type: 'daterange',
    model: upSettlementDateRange,
    loading: upSettlementLoading,
    action: handleExportUpSettlement
  },
  {
    title: '下游及管理合同结算报表导出',
    description: '导出下游及管理合同结算记录。',
    footnote: '导出内容包含：结算金额、备注等字段。',
    type: 'daterange',
    model: downSettlementDateRange,
    loading: downSettlementLoading,
    action: handleExportDownSettlement
  }
])

const reportHeaderMeta = computed(() => `${costMonth.value || currentMonthValue} · ${exportCards.value.length} 类导出`)

function downloadFile(response, filename) {
  const url = window.URL.createObjectURL(new Blob([response]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

onMounted(() => {
  handleQueryCostReport()
})
</script>

<style scoped lang="scss">
.report-dashboard-shell {
  display: grid;
  gap: var(--space-6);
}

.report-dashboard-header {
  margin-bottom: 0;
}

.report-dashboard-panels {
  display: grid;
  gap: var(--space-5);
}

.report-dashboard-panel {
  gap: var(--space-4);
}

.report-dashboard-panel :deep(.app-section-card) {
  border-radius: 22px;
}

.cost-title {
  margin: 0 0 var(--space-4);
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.cost-report-table :deep(th) {
  text-align: center;
  font-weight: 700;
}

.cost-report-table :deep(.el-table__cell) {
  padding: 10px 0;
}

:deep(.cost-total-row td.el-table__cell) {
  background: color-mix(in srgb, var(--status-warning) 12%, var(--surface-panel));
  font-weight: 700;
}

.report-export-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

.report-export-card {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-5);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: linear-gradient(180deg, var(--surface-panel), var(--surface-panel-muted));
  box-shadow: var(--shadow-soft);
}

.report-export-card__header h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: var(--text-primary);
}

.report-export-card__header p {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.report-export-card__filters {
  margin: 0;
}

:deep(.app-filter-bar.report-export-card__filters) {
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
}

:deep(.app-filter-bar.report-export-card__filters .app-filter-bar__main) {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

:deep(.app-filter-bar.report-export-card__filters .app-filter-bar__actions) {
  width: 100%;
  padding-top: 0;
  margin-left: 0;
}

:deep(.app-filter-bar.report-export-card__filters .el-date-editor),
:deep(.app-filter-bar.report-export-card__filters .el-input),
:deep(.app-filter-bar.report-export-card__filters .el-select) {
  width: 100%;
  max-width: 100%;
}

:deep(.app-filter-bar.report-export-card__filters--daterange-with-status .app-filter-bar__main) {
  display: flex;
  flex-direction: column;
}

:deep(.app-filter-bar.report-export-card__filters--daterange-with-status .el-date-editor) {
  width: 100%;
}

.report-export-card__footnote {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-muted);
}

@media (max-width: 1279px) {
  .report-export-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 767px) {
  .report-dashboard-shell {
    gap: var(--space-4);
  }

  .report-dashboard-panels {
    gap: var(--space-4);
  }

  .report-export-grid {
    grid-template-columns: 1fr;
  }

  .report-export-card {
    padding: var(--space-4);
  }

  .cost-title {
    font-size: 14px;
  }
}
</style>
