<template>
  <div class="report-dashboard-shell">
    <div class="report-dashboard-panels">
    <AppWorkspacePanel panel-class="report-dashboard-panel report-dashboard-panel--cost">
    <AppSectionCard>
      <template #header>月度 / 季度成本报表</template>
      <AppFilterBar>
        <ReportPeriodFilter :period-type="costActiveTab" :selection="costPeriodSelection" />
        <template #actions>
        <el-button type="primary" :loading="costLoading" @click="handleQueryCostReport">查询报表</el-button>
        <el-button type="primary" plain :loading="costExportLoading" @click="handleExportCostReport">导出</el-button>
        </template>
      </AppFilterBar>

      <el-tabs v-model="costActiveTab" class="cost-tabs app-tabs--line">
        <el-tab-pane
          v-for="period in REPORT_PERIODS"
          :key="period.key"
          :label="`${period.label}成本报表`"
          :name="period.key"
        >
          <div class="cost-title">{{ costTitle(period.key) }}</div>
          <AppDataTable v-if="costRowCount(period.key) > 0">
            <el-table
              :data="costTableData(period.key)"
              border
              v-loading="costLoading"
              :row-class-name="costRowClassName"
              :cell-style="costCellStyle"
              class="cost-report-table"
            >
              <el-table-column prop="company_category" label="公司合同分类" :fixed="isMobile ? false : true" min-width="140" />
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
            :title="`暂无${period.label}成本数据`"
          />
        </el-tab-pane>
      </el-tabs>
    </AppSectionCard>

    <AppSectionCard class="settlement-report-card">
      <template #header>月度 / 季度结算报表</template>
      <AppFilterBar>
        <ReportPeriodFilter :period-type="settlementActiveTab" :selection="settlementPeriodSelection" />
        <template #actions>
          <el-button type="primary" :loading="settlementLoading" @click="handleQuerySettlementReport">查询报表</el-button>
          <el-button type="primary" plain :loading="settlementExportLoading" @click="handleExportSettlementReport">导出</el-button>
        </template>
      </AppFilterBar>

      <el-tabs v-model="settlementActiveTab" class="settlement-tabs app-tabs--line">
        <el-tab-pane
          v-for="period in REPORT_PERIODS"
          :key="period.key"
          :label="`${period.label}结算报表`"
          :name="period.key"
        >
          <div class="cost-title">{{ settlementTitle(period.key) }}</div>
          <AppDataTable v-if="settlementRowCount(period.key) > 0">
            <el-table
              :data="settlementTableData(period.key)"
              border
              v-loading="settlementLoading"
              :cell-style="settlementCellStyle"
              show-summary
              :summary-method="settlementSummaryMethod"
              class="settlement-report-table"
            >
              <el-table-column prop="serial_number" label="合同序号" :fixed="isMobile ? false : true" min-width="100" />
              <el-table-column prop="contract_name" label="合同名称" :fixed="isMobile ? false : true" min-width="230" class-name="settlement-text-column" />
              <el-table-column prop="company_category" label="公司合同分类" min-width="140" />
              <el-table-column prop="party_a_name" label="甲方单位" min-width="210" class-name="settlement-text-column" />
              <el-table-column prop="contract_amount" label="签约金额" min-width="130" :formatter="amountFormatter" />
              <el-table-column prop="settlement_date" label="结算时间" min-width="120" />
              <el-table-column prop="settlement_amount" label="结算金额" min-width="130" :formatter="amountFormatter" />
              <el-table-column prop="received_amount" label="合同已收款金额" min-width="150" :formatter="amountFormatter" />
              <el-table-column prop="down_mgmt_settlement_amount" label="下游合同结算" min-width="150" :formatter="amountFormatter" />
              <el-table-column prop="down_mgmt_paid_amount" label="下游合同已付款" min-width="165" :formatter="amountFormatter" />
              <el-table-column prop="non_contract_expense_amount" label="无合同费用" min-width="135" :formatter="amountFormatter" />
              <el-table-column prop="zero_hour_labor_amount" label="零星用工" min-width="125" :formatter="amountFormatter" />
            </el-table>
          </AppDataTable>
          <AppEmptyState
            v-else-if="!settlementLoading"
            :title="`暂无${period.label}结算数据`"
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
            <template v-for="field in card.fields" :key="field.key">
              <AppRangeField
                v-if="field.type === 'dateRange'"
                v-model="field.model.value"
                class="filter-control--range-wide"
                :start-placeholder="field.startPlaceholder || '开始日期'"
                :end-placeholder="field.endPlaceholder || '结束日期'"
              />
              <DictSelect
                v-else-if="field.type === 'companyCategory'"
                v-model="field.model.value"
                category="project_category"
                :placeholder="field.placeholder || '公司合同分类'"
                clearable
              />
              <el-input
                v-else
                v-model="field.model.value"
                :placeholder="field.placeholder"
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
import AppSectionCard from '@/components/ui/AppSectionCard.vue'
import AppFilterBar from '@/components/ui/AppFilterBar.vue'
import AppDataTable from '@/components/ui/AppDataTable.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import AppRangeField from '@/components/ui/AppRangeField.vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'
import DictSelect from '@/components/DictSelect.vue'
import { useDevice } from '@/composables/useDevice'
import ReportPeriodFilter from '@/views/reports/ReportPeriodFilter.vue'
import { buildExportParams, buildSettlementSummaries } from '@/views/reports/reportDashboard.helpers'
import {
  REPORT_PERIODS,
  createPeriodSelection,
  formatPeriodLabel,
  resolvePeriodAnchor,
  syncPeriodSelection
} from '@/views/reports/reportPeriod.helpers'
import {
  getCostMonthlyQuarterlyReport,
  downloadCostMonthlyQuarterlyReport,
  getSettlementMonthlyQuarterlyReport,
  downloadSettlementMonthlyQuarterlyReport,
  downloadComprehensiveReport,
  downloadReceivablesReport,
  downloadPayablesReport,
  downloadUpstreamInvoicesReport,
  downloadDownstreamInvoicesReport,
  downloadUpstreamReceiptsReport,
  downloadUpstreamInvoiceReceiptComprehensiveReport,
  downloadDownstreamPaymentsReport,
  downloadExpensePaymentsReport,
  downloadUpstreamSettlementsReport,
  downloadDownstreamSettlementsReport,
  downloadAssociationReport,
  downloadZeroHourLaborReport
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

const SETTLEMENT_AMOUNT_FIELDS = [
  'contract_amount',
  'settlement_amount',
  'received_amount',
  'down_mgmt_settlement_amount',
  'down_mgmt_paid_amount',
  'non_contract_expense_amount',
  'zero_hour_labor_amount'
]

const now = new Date()
const { isMobile } = useDevice()
const costPeriodSelection = ref(createPeriodSelection(now))
const costLoading = ref(false)
const costExportLoading = ref(false)
const costActiveTab = ref('monthly')
const settlementPeriodSelection = ref(createPeriodSelection(now))
const settlementLoading = ref(false)
const settlementExportLoading = ref(false)
const settlementActiveTab = ref('monthly')

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

const settlementReportData = ref({
  period: {
    year: now.getFullYear(),
    month: now.getMonth() + 1,
    quarter: Math.floor(now.getMonth() / 3) + 1,
    half_year: now.getMonth() + 1 <= 6 ? 1 : 2
  },
  monthly: { rows: [] },
  quarterly: { rows: [] },
  half_yearly: { rows: [] },
  yearly: { rows: [] }
})

function periodMonth(periodType, period) {
  if (periodType === 'monthly') return period.month
  if (periodType === 'quarterly') return ((period.quarter || 1) - 1) * 3 + 1
  if (periodType === 'half_yearly') return period.half_year === 2 ? 7 : 1
  return 1
}

function reportTitle(reportData, periodType, suffix) {
  const period = reportData.period || {}
  if (!period.year) return `${suffix}报表`
  return `${formatPeriodLabel(periodType, period.year, periodMonth(periodType, period))} ${suffix}报表`
}

const costTitle = (periodType) => reportTitle(costReportData.value, periodType, '成本')
const settlementTitle = (periodType) => reportTitle(settlementReportData.value, periodType, '结算')

function costTableData(periodType) {
  const periodData = costReportData.value[periodType] || {}
  const rows = (periodData.rows || []).map((row) => ({
    ...buildEmptyCostRecord(row.company_category),
    ...row,
    is_total: false
  }))
  const total = {
    ...buildEmptyCostRecord('合计'),
    ...(periodData.total || {}),
    company_category: '合计',
    is_total: true
  }
  return [...rows, total]
}

const costRowCount = (periodType) => costReportData.value[periodType]?.rows?.length || 0
const settlementTableData = (periodType) => settlementReportData.value[periodType]?.rows || []
const settlementRowCount = (periodType) => settlementReportData.value[periodType]?.rows?.length || 0

async function handleQueryCostReport() {
  costLoading.value = true
  try {
    const { year, month } = resolvePeriodAnchor(costActiveTab.value, costPeriodSelection.value, now)
    syncPeriodSelection(costPeriodSelection.value, year, month)
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
    const { year, month } = resolvePeriodAnchor(costActiveTab.value, costPeriodSelection.value, now)
    syncPeriodSelection(costPeriodSelection.value, year, month)
    const res = await downloadCostMonthlyQuarterlyReport({ year, month, period_type: costActiveTab.value })
    downloadFile(res, `${formatPeriodLabel(costActiveTab.value, year, month)}成本报表.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    costExportLoading.value = false
  }
}

async function handleQuerySettlementReport() {
  settlementLoading.value = true
  try {
    const { year, month } = resolvePeriodAnchor(settlementActiveTab.value, settlementPeriodSelection.value, now)
    syncPeriodSelection(settlementPeriodSelection.value, year, month)
    const res = await getSettlementMonthlyQuarterlyReport(year, month)
    settlementReportData.value = {
      period: res.period || {
        year,
        month,
        quarter: Math.floor((month - 1) / 3) + 1,
        half_year: month <= 6 ? 1 : 2
      },
      monthly: { rows: res.monthly?.rows || [] },
      quarterly: { rows: res.quarterly?.rows || [] },
      half_yearly: { rows: res.half_yearly?.rows || [] },
      yearly: { rows: res.yearly?.rows || [] }
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('结算报表查询失败')
  } finally {
    settlementLoading.value = false
  }
}

async function handleExportSettlementReport() {
  settlementExportLoading.value = true
  try {
    const { year, month } = resolvePeriodAnchor(settlementActiveTab.value, settlementPeriodSelection.value, now)
    syncPeriodSelection(settlementPeriodSelection.value, year, month)
    const res = await downloadSettlementMonthlyQuarterlyReport({
      year,
      month,
      period_type: settlementActiveTab.value
    })
    downloadFile(res, `${formatPeriodLabel(settlementActiveTab.value, year, month)}结算报表.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    settlementExportLoading.value = false
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

function settlementCellStyle({ column }) {
  if (SETTLEMENT_AMOUNT_FIELDS.includes(column.property)) {
    return { textAlign: 'right' }
  }
  return {}
}

function settlementSummaryMethod({ columns, data }) {
  return buildSettlementSummaries(columns, data, SETTLEMENT_AMOUNT_FIELDS)
}

const exportFilters = ref({
  dateRange: [],
  companyCategory: ''
})
const exportLoading = ref(false)
const recDateRange = ref([])
const recCompanyCategory = ref('')
const payDateRange = ref([])
const upInvDateRange = ref([])
const upInvCompanyCategory = ref('')
const downInvDateRange = ref([])
const upReceiptDateRange = ref([])
const upReceiptCompanyCategory = ref('')
const upInvoiceReceiptComprehensiveDateRange = ref([])
const upInvoiceReceiptComprehensiveCompanyCategory = ref('')
const downPayDateRange = ref([])
const downPayCompanyCategory = ref('')
const expPayDateRange = ref([])
const expPayUpstreamContractName = ref('')
const expPayCompanyCategory = ref('')
const upSettlementDateRange = ref([])
const downSettlementDateRange = ref([])
const assocQuery = ref('')
const assocDateRange = ref([])
const zeroHourLaborDateRange = ref([])
const zeroHourLaborUpstreamContractName = ref('')
const zeroHourLaborCompanyCategory = ref('')

const recLoading = ref(false)
const payLoading = ref(false)
const upInvLoading = ref(false)
const downInvLoading = ref(false)
const upReceiptLoading = ref(false)
const upInvoiceReceiptComprehensiveLoading = ref(false)
const downPayLoading = ref(false)
const expPayLoading = ref(false)
const upSettlementLoading = ref(false)
const downSettlementLoading = ref(false)
const assocLoading = ref(false)
const zeroHourLaborLoading = ref(false)

const dateRangeField = (key, model, startPlaceholder = '开始日期', endPlaceholder = '结束日期') => ({
  key,
  type: 'dateRange',
  model,
  startPlaceholder,
  endPlaceholder
})

const companyCategoryField = (key, model, placeholder = '公司合同分类') => ({
  key,
  type: 'companyCategory',
  model,
  placeholder
})

const inputField = (key, model, placeholder) => ({
  key,
  type: 'input',
  model,
  placeholder
})

async function handleExport() {
  exportLoading.value = true
  try {
    const params = buildExportParams({
      dateRange: exportFilters.value.dateRange,
      companyCategory: exportFilters.value.companyCategory
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
    const params = buildExportParams({
      dateRange: recDateRange.value,
      companyCategory: recCompanyCategory.value
    })
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
    const params = buildExportParams({
      dateRange: upInvDateRange.value,
      companyCategory: upInvCompanyCategory.value
    })
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
    const params = buildExportParams({
      dateRange: upReceiptDateRange.value,
      companyCategory: upReceiptCompanyCategory.value
    })
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

async function handleExportUpInvoiceReceiptComprehensive() {
  upInvoiceReceiptComprehensiveLoading.value = true
  try {
    const params = buildExportParams({
      dateRange: upInvoiceReceiptComprehensiveDateRange.value,
      companyCategory: upInvoiceReceiptComprehensiveCompanyCategory.value
    })
    const res = await downloadUpstreamInvoiceReceiptComprehensiveReport(params)
    downloadFile(res, `上游合同挂账付款综合报表_${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    upInvoiceReceiptComprehensiveLoading.value = false
  }
}

async function handleExportDownPay() {
  downPayLoading.value = true
  try {
    const params = buildExportParams({
      dateRange: downPayDateRange.value,
      companyCategory: downPayCompanyCategory.value
    })
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
    const params = buildExportParams({
      dateRange: expPayDateRange.value,
      upstreamContractName: expPayUpstreamContractName.value,
      companyCategory: expPayCompanyCategory.value
    })
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
    const params = buildExportParams({ dateRange: assocDateRange.value })
    if (assocQuery.value) params.query = assocQuery.value
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

async function handleExportZeroHourLabor() {
  zeroHourLaborLoading.value = true
  try {
    const params = buildExportParams({
      dateRange: zeroHourLaborDateRange.value,
      upstreamContractName: zeroHourLaborUpstreamContractName.value,
      companyCategory: zeroHourLaborCompanyCategory.value
    })
    const res = await downloadZeroHourLaborReport(params)
    downloadFile(res, `零星用工报表_${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
  } finally {
    zeroHourLaborLoading.value = false
  }
}

const exportCards = computed(() => [
  {
    title: '上游合同综合报表导出',
    description: '按时间范围与公司合同分类导出综合统计结果。',
    footnote: '导出内容包含：上游合同基础信息、财务累计数据，以及关联的下游、管理、无合同费用统计。',
    type: 'daterange-with-category',
    fields: [
      dateRangeField('comprehensive-date', computed({
        get: () => exportFilters.value.dateRange,
        set: (value) => { exportFilters.value.dateRange = value }
      })),
      companyCategoryField('comprehensive-company-category', computed({
        get: () => exportFilters.value.companyCategory,
        set: (value) => { exportFilters.value.companyCategory = value }
      }))
    ],
    loading: exportLoading,
    action: handleExport
  },
  {
    title: '上下游合同关联报表导出',
    description: '通过合同编号、名称或序号快速定位关联关系。',
    footnote: '导出内容包含：上游合同及其关联的下游、管理合同与无合同费用明细。',
    type: 'query-with-daterange',
    fields: [
      inputField('association-query', assocQuery, '请输入合同序号/编号/名称'),
      dateRangeField('association-date', assocDateRange, '签约开始日期', '签约结束日期')
    ],
    loading: assocLoading,
    action: handleExportAssociation
  },
  {
    title: '上游合同应收款报表导出',
    description: '筛选应收时间范围，导出应收款记录。',
    footnote: '导出内容包含：金额、日期、备注等应收款明细。',
    type: 'daterange-with-category',
    fields: [
      dateRangeField('receivable-date', recDateRange),
      companyCategoryField('receivable-company-category', recCompanyCategory)
    ],
    loading: recLoading,
    action: handleExportRec
  },
  {
    title: '下游及管理合同应付款报表导出',
    description: '按应付时间导出付款记录。',
    footnote: '导出内容包含：金额、日期、备注等应付款明细。',
    type: 'daterange',
    fields: [dateRangeField('payable-date', payDateRange)],
    loading: payLoading,
    action: handleExportPay
  },
  {
    title: '上游合同挂账报表导出',
    description: '导出上游挂账与开票记录。',
    footnote: '导出内容包含：金额、日期、发票号、备注等字段。',
    type: 'daterange-with-category',
    fields: [
      dateRangeField('upstream-invoice-date', upInvDateRange),
      companyCategoryField('upstream-invoice-company-category', upInvCompanyCategory)
    ],
    loading: upInvLoading,
    action: handleExportUpInv
  },
  {
    title: '下游及管理合同挂账报表导出',
    description: '导出下游及管理合同挂账与收票记录。',
    footnote: '导出内容包含：金额、日期、发票号、备注等字段。',
    type: 'daterange',
    fields: [dateRangeField('downstream-invoice-date', downInvDateRange)],
    loading: downInvLoading,
    action: handleExportDownInv
  },
  {
    title: '上游合同收款报表导出',
    description: '按收款时间范围导出到账记录。',
    footnote: '导出内容包含：金额、日期、方式、备注等收款明细。',
    type: 'daterange-with-category',
    fields: [
      dateRangeField('upstream-receipt-date', upReceiptDateRange),
      companyCategoryField('upstream-receipt-company-category', upReceiptCompanyCategory)
    ],
    loading: upReceiptLoading,
    action: handleExportUpReceipt
  },
  {
    title: '上游合同挂账付款综合报表导出',
    description: '按挂账或收款日期筛选合同，导出合同级综合明细。',
    footnote: '导出内容包含：合同基础信息、签约结算信息、筛选期内挂账与收款汇总。',
    type: 'daterange-with-category',
    fields: [
      dateRangeField(
        'upstream-invoice-receipt-comprehensive-date',
        upInvoiceReceiptComprehensiveDateRange,
        '挂账/收款开始日期',
        '挂账/收款结束日期'
      ),
      companyCategoryField(
        'upstream-invoice-receipt-comprehensive-company-category',
        upInvoiceReceiptComprehensiveCompanyCategory
      )
    ],
    loading: upInvoiceReceiptComprehensiveLoading,
    action: handleExportUpInvoiceReceiptComprehensive
  },
  {
    title: '下游及管理合同付款报表导出',
    description: '按付款时间范围导出实际付款记录。',
    footnote: '导出内容包含：金额、日期、方式、备注等付款明细。',
    type: 'daterange-with-category',
    fields: [
      dateRangeField('downstream-payment-date', downPayDateRange),
      companyCategoryField('downstream-payment-company-category', downPayCompanyCategory)
    ],
    loading: downPayLoading,
    action: handleExportDownPay
  },
  {
    title: '无合同费用付款报表导出',
    description: '导出无合同费用支出记录。',
    footnote: '导出内容包含：金额、日期、类别、经办人、备注等字段。',
    type: 'expense-payment',
    fields: [
      dateRangeField('expense-payment-date', expPayDateRange),
      inputField('expense-payment-upstream-name', expPayUpstreamContractName, '上游合同名称'),
      companyCategoryField('expense-payment-company-category', expPayCompanyCategory, '上游公司合同分类')
    ],
    loading: expPayLoading,
    action: handleExportExpPay
  },
  {
    title: '零星用工报表导出',
    description: '按用工时间与上游合同信息导出零星用工记录。',
    footnote: '导出内容包含：用工时间、归宿、上游合同、各项费用与总计。',
    type: 'zero-hour-labor',
    fields: [
      dateRangeField('zero-hour-labor-date', zeroHourLaborDateRange),
      inputField('zero-hour-labor-upstream-name', zeroHourLaborUpstreamContractName, '上游合同名称'),
      companyCategoryField('zero-hour-labor-company-category', zeroHourLaborCompanyCategory, '上游公司合同分类')
    ],
    loading: zeroHourLaborLoading,
    action: handleExportZeroHourLabor
  },
  {
    title: '上游合同结算报表导出',
    description: '导出上游合同结算与完工记录。',
    footnote: '导出内容包含：结算金额、完工日期、备注等字段。',
    type: 'daterange',
    fields: [dateRangeField('upstream-settlement-date', upSettlementDateRange)],
    loading: upSettlementLoading,
    action: handleExportUpSettlement
  },
  {
    title: '下游及管理合同结算报表导出',
    description: '导出下游及管理合同结算记录。',
    footnote: '导出内容包含：结算金额、备注等字段。',
    type: 'daterange',
    fields: [dateRangeField('downstream-settlement-date', downSettlementDateRange)],
    loading: downSettlementLoading,
    action: handleExportDownSettlement
  }
])

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
  handleQuerySettlementReport()
})
</script>

<style scoped lang="scss">
.report-dashboard-shell {
  display: grid;
  gap: var(--space-5);
  width: 100%;
  min-width: 0;
}

.report-dashboard-panels {
  display: grid;
  gap: var(--space-5);
  min-width: 0;
}

.report-dashboard-panel {
  gap: var(--space-4);
  min-width: 0;
}

.cost-tabs,
.settlement-tabs {
  width: 100%;
  min-width: 0;
  max-width: 100%;
}

.report-dashboard-panel :deep(.app-section-card) {
  border-radius: calc(var(--radius) + 2px);
}

.cost-title {
  margin: 0 0 var(--space-4);
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.cost-report-table :deep(th),
.settlement-report-table :deep(th) {
  text-align: center;
  font-weight: 700;
}

.cost-report-table :deep(.el-table__cell),
.settlement-report-table :deep(.el-table__cell) {
  padding: 10px 0;
}

.settlement-report-table :deep(td.settlement-text-column .cell) {
  overflow: visible;
  white-space: normal;
  text-overflow: clip;
  word-break: break-word;
  overflow-wrap: anywhere;
  line-height: 1.55;
}

.settlement-report-table :deep(.el-table__footer-wrapper td.el-table__cell) {
  background: color-mix(in srgb, var(--status-warning) 12%, var(--surface-panel));
  font-weight: 700;
}

.settlement-report-table :deep(.el-table__footer-wrapper .cell) {
  white-space: nowrap;
}

.settlement-report-card {
  margin-top: var(--space-5);
}

:deep(.cost-total-row td.el-table__cell) {
  background: color-mix(in srgb, var(--status-warning) 12%, var(--surface-panel));
  font-weight: 700;
  white-space: nowrap;
}

:deep(.cost-total-row td.el-table__cell .cell) {
  white-space: nowrap;
}

.report-export-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-5);
}

.report-export-card {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: var(--space-4);
  padding: var(--space-5);
  border: 1px solid var(--border-subtle);
  border-radius: calc(var(--radius) + 2px);
  background: color-mix(in srgb, var(--surface-panel) 90%, var(--surface-panel-muted) 10%);
  box-shadow: var(--shadow-card);
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
  height: 100%;
}

:deep(.app-filter-bar.report-export-card__filters) {
  height: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
}

:deep(.app-filter-bar.report-export-card__filters .app-filter-bar__content) {
  height: 100%;
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
  margin-top: auto;
  align-self: end;
}

:deep(.app-filter-bar.report-export-card__filters .el-date-editor),
:deep(.app-filter-bar.report-export-card__filters .el-input),
:deep(.app-filter-bar.report-export-card__filters .el-select) {
  width: 100%;
  max-width: 100%;
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
