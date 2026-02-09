<template>
  <div class="app-container">
    <el-card shadow="hover" class="cost-report-card">
      <template #header>
        <div class="header-content">
          <span class="title">月度/季度成本报表</span>
          <span class="subtitle">统计口径：按业务日期（签约/付款/结算等）</span>
        </div>
      </template>

      <div class="filter-container cost-filter-container">
        <span class="filter-label">统计月份:</span>
        <el-date-picker
          v-model="costMonth"
          type="month"
          value-format="YYYY-MM"
          format="YYYY年MM月"
          placeholder="选择月份"
          class="filter-item short"
        />
        <el-button type="primary" :loading="costLoading" @click="handleQueryCostReport">
          <el-icon class="el-icon--right"><Download /></el-icon> 查询报表
        </el-button>
        <el-button type="success" :loading="costExportLoading" @click="handleExportCostReport">
          <el-icon class="el-icon--right"><Download /></el-icon> 导出 Excel
        </el-button>
      </div>

      <el-tabs v-model="costActiveTab" class="cost-tabs">
        <el-tab-pane label="月度成本报表" name="monthly">
          <div class="cost-title">{{ monthlyTitle }}</div>
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
        </el-tab-pane>

        <el-tab-pane label="季度成本报表" name="quarterly">
          <div class="cost-title">{{ quarterlyTitle }}</div>
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
        </el-tab-pane>

        <el-tab-pane label="半年度成本报表" name="half_yearly">
          <div class="cost-title">{{ halfYearlyTitle }}</div>
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
        </el-tab-pane>

        <el-tab-pane label="年度成本报表" name="yearly">
          <div class="cost-title">{{ yearlyTitle }}</div>
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
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card shadow="hover" class="page-header">
       <template #header>
         <div class="header-content">
           <span class="title">数据查询与导出</span>
           <span class="subtitle">请选择相应报表进行导出</span>
         </div>
       </template>
       
       <el-row :gutter="20">
      <el-col :xs="24" :md="6" style="margin-bottom: 20px;">
        <!-- Comprehensive Report Export Section -->
        <el-card shadow="hover" class="chart-card" style="margin-top: 0; min-height: 100%;">
      <template #header>
        <div class="card-header">
          <span>上游合同综合报表导出</span>
        </div>
      </template>
      <div class="filter-container">
        <span class="filter-label">签约时间范围:</span>
        <el-date-picker
          v-model="exportFilters.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          class="filter-item"
        />
        
        <span class="filter-label">合同状态:</span>
        <el-select v-model="exportFilters.status" class="filter-item short">
          <el-option label="全部" value="全部" />
          <el-option label="执行中" value="执行中" />
          <el-option label="已完工" value="已完工" />
          <el-option label="已结算" value="已结算" />
          <el-option label="质保期到期" value="质保期到期" />
          <el-option label="合同终止" value="合同终止" />
          <el-option label="合同中止" value="合同中止" />
        </el-select>
        
        <el-button type="primary" :loading="exportLoading" @click="handleExport">
          <el-icon class="el-icon--right"><Download /></el-icon> 导出 Excel
        </el-button>
      </div>
      <div style="font-size: 12px; color: #909399; margin-top: 10px;">
        * 导出内容包含：上游合同基础信息、财务累计数据（应收/挂账/已收）、以及关联的下游、管理、无合同费用统计。
      </div>
    </el-card>
      </el-col>

      <!-- Upstream-Downstream Association Report Export -->
      <el-col :xs="24" :md="6" style="margin-bottom: 20px;">
        <el-card shadow="hover" class="chart-card" style="margin-top: 0; min-height: 100%;">
          <template #header>
            <div class="card-header">
              <span>上下游合同关联报表导出</span>
            </div>
          </template>
          <div class="filter-container">
            <span class="filter-label">合同查询:</span>
            <el-input
              v-model="assocQuery"
              placeholder="请输入合同序号/编号/名称"
              clearable
              class="filter-item"
            />
            <el-button type="primary" :loading="assocLoading" @click="handleExportAssociation">
              <el-icon class="el-icon--right"><Download /></el-icon> 导出 Excel
            </el-button>
          </div>
          <div style="font-size: 12px; color: #909399; margin-top: 10px;">
            * 导出内容包含：上游合同及其关联的下游/管理合同、无合同费用的详细关联数据。
          </div>
        </el-card>
      </el-col>

      <!-- Upstream Receivable Export -->
      <el-col :xs="24" :md="6" style="margin-bottom: 20px;">
        <el-card shadow="hover" class="chart-card" style="margin-top: 0; min-height: 100%;">
          <template #header>
            <div class="card-header">
              <span>上游合同应收款报表导出</span>
            </div>
          </template>
          <div class="filter-container">
            <span class="filter-label">应收时间范围:</span>
            <el-date-picker
              v-model="recDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="margin-right: 20px; width: 240px;"
            />
            <el-button type="primary" :loading="recLoading" @click="handleExportRec">
              <el-icon class="el-icon--right"><Download /></el-icon> 导出 Excel
            </el-button>
          </div>
          <div style="font-size: 12px; color: #909399; margin-top: 10px;">
            * 导出内容包含：上游合同的所有应收款记录（含金额、日期、备注）。
          </div>
        </el-card>
      </el-col>
      
      <!-- Downstream/Management Payable Export -->
      <el-col :xs="24" :md="6" style="margin-bottom: 20px;">
        <el-card shadow="hover" class="chart-card" style="margin-top: 0; min-height: 100%;">
          <template #header>
            <div class="card-header">
              <span>下游及管理合同应付款报表导出</span>
            </div>
          </template>
          <div class="filter-container">
            <span class="filter-label">应付时间范围:</span>
            <el-date-picker
              v-model="payDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="margin-right: 20px; width: 240px;"
            />
            <el-button type="primary" :loading="payLoading" @click="handleExportPay">
              <el-icon class="el-icon--right"><Download /></el-icon> 导出 Excel
            </el-button>
          </div>
          <div style="font-size: 12px; color: #909399; margin-top: 10px;">
            * 导出内容包含：下游及管理合同的所有应付款记录（含金额、日期、备注）。
          </div>
        </el-card>
      </el-col>

      <!-- Upstream Invoice Export -->
      <el-col :xs="24" :md="6" style="margin-bottom: 20px;">
        <el-card shadow="hover" class="chart-card" style="margin-top: 0; min-height: 100%;">
          <template #header>
            <div class="card-header">
              <span>上游合同挂账报表导出</span>
            </div>
          </template>
          <div class="filter-container">
            <span class="filter-label">挂账时间范围:</span>
            <el-date-picker
              v-model="upInvDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="margin-right: 20px; width: 240px;"
            />
            <el-button type="primary" :loading="upInvLoading" @click="handleExportUpInv">
              <el-icon class="el-icon--right"><Download /></el-icon> 导出 Excel
            </el-button>
          </div>
          <div style="font-size: 12px; color: #909399; margin-top: 10px;">
            * 导出内容包含：上游合同的所有挂账/开票记录（含金额、日期、发票号、备注）。
          </div>
        </el-card>
      </el-col>
      
      <!-- Downstream/Management Invoice Export -->
      <el-col :xs="24" :md="6" style="margin-bottom: 20px;">
        <el-card shadow="hover" class="chart-card" style="margin-top: 0; min-height: 100%;">
          <template #header>
            <div class="card-header">
              <span>下游及管理合同挂账报表导出</span>
            </div>
          </template>
          <div class="filter-container">
            <span class="filter-label">挂账时间范围:</span>
            <el-date-picker
              v-model="downInvDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="margin-right: 20px; width: 240px;"
            />
            <el-button type="primary" :loading="downInvLoading" @click="handleExportDownInv">
              <el-icon class="el-icon--right"><Download /></el-icon> 导出 Excel
            </el-button>
          </div>
          <div style="font-size: 12px; color: #909399; margin-top: 10px;">
            * 导出内容包含：下游及管理合同的所有挂账/收票记录（含金额、日期、发票号、备注）。
          </div>
        </el-card>
      </el-col>

      <!-- Upstream Receipt Export -->
      <el-col :xs="24" :md="6" style="margin-bottom: 20px;">
        <el-card shadow="hover" class="chart-card" style="margin-top: 0; min-height: 100%;">
          <template #header>
            <div class="card-header">
              <span>上游合同收款报表导出</span>
            </div>
          </template>
          <div class="filter-container">
            <span class="filter-label">收款时间范围:</span>
            <el-date-picker
              v-model="upReceiptDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="margin-right: 20px; width: 240px;"
            />
            <el-button type="primary" :loading="upReceiptLoading" @click="handleExportUpReceipt">
              <el-icon class="el-icon--right"><Download /></el-icon> 导出 Excel
            </el-button>
          </div>
          <div style="font-size: 12px; color: #909399; margin-top: 10px;">
            * 导出内容包含：上游合同的所有实际收款记录（含金额、日期、方式、备注）。
          </div>
        </el-card>
      </el-col>

      <!-- Downstream/Management Payment Export -->
      <el-col :xs="24" :md="6" style="margin-bottom: 20px;">
        <el-card shadow="hover" class="chart-card" style="margin-top: 0; min-height: 100%;">
          <template #header>
            <div class="card-header">
              <span>下游及管理合同付款报表导出</span>
            </div>
          </template>
          <div class="filter-container">
            <span class="filter-label">付款时间范围:</span>
            <el-date-picker
              v-model="downPayDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="margin-right: 20px; width: 240px;"
            />
            <el-button type="primary" :loading="downPayLoading" @click="handleExportDownPay">
              <el-icon class="el-icon--right"><Download /></el-icon> 导出 Excel
            </el-button>
          </div>
          <div style="font-size: 12px; color: #909399; margin-top: 10px;">
            * 导出内容包含：下游及管理合同的所有实际付款记录（含金额、日期、方式、备注）。
          </div>
        </el-card>
      </el-col>

      <!-- Non-Contract Expense Payment Export -->
      <el-col :xs="24" :md="6" style="margin-bottom: 20px;">
        <el-card shadow="hover" class="chart-card" style="margin-top: 0; min-height: 100%;">
          <template #header>
            <div class="card-header">
              <span>无合同费用付款报表导出</span>
            </div>
          </template>
          <div class="filter-container">
            <span class="filter-label">费用时间范围:</span>
            <el-date-picker
              v-model="expPayDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="margin-right: 20px; width: 240px;"
            />
            <el-button type="primary" :loading="expPayLoading" @click="handleExportExpPay">
              <el-icon class="el-icon--right"><Download /></el-icon> 导出 Excel
            </el-button>
          </div>
          <div style="font-size: 12px; color: #909399; margin-top: 10px;">
            * 导出内容包含：所有无合同费用报销记录（含金额、日期、类别、经办人、备注）。
          </div>
        </el-card>
      </el-col>

      <!-- Upstream Settlement Export -->
      <el-col :xs="24" :md="6" style="margin-bottom: 20px;">
        <el-card shadow="hover" class="chart-card" style="margin-top: 0; min-height: 100%;">
          <template #header>
            <div class="card-header">
              <span>上游合同结算报表导出</span>
            </div>
          </template>
          <div class="filter-container">
            <span class="filter-label">结算时间范围:</span>
            <el-date-picker
              v-model="upSettlementDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="margin-right: 20px; width: 240px;"
            />
            <el-button type="primary" :loading="upSettlementLoading" @click="handleExportUpSettlement">
              <el-icon class="el-icon--right"><Download /></el-icon> 导出 Excel
            </el-button>
          </div>
          <div style="font-size: 12px; color: #909399; margin-top: 10px;">
            * 导出内容包含：上游合同的所有结算/完工记录（含结算金额、完工日期、备注）。
          </div>
        </el-card>
      </el-col>

      <!-- Downstream/Management Settlement Export -->
      <el-col :xs="24" :md="6" style="margin-bottom: 20px;">
        <el-card shadow="hover" class="chart-card" style="margin-top: 0; min-height: 100%;">
          <template #header>
            <div class="card-header">
              <span>下游及管理合同结算报表导出</span>
            </div>
          </template>
          <div class="filter-container">
            <span class="filter-label">结算时间范围:</span>
            <el-date-picker
              v-model="downSettlementDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="margin-right: 20px; width: 240px;"
            />
            <el-button type="primary" :loading="downSettlementLoading" @click="handleExportDownSettlement">
              <el-icon class="el-icon--right"><Download /></el-icon> 导出 Excel
            </el-button>
          </div>
          <div style="font-size: 12px; color: #909399; margin-top: 10px;">
            * 导出内容包含：下游及管理合同的所有结算记录（含结算金额、备注）。
          </div>
        </el-card>
      </el-col>
    </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
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
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'

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
const costMonth = ref(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`)
const costLoading = ref(false)
const costExportLoading = ref(false)
const costActiveTab = ref('monthly')

const buildEmptyCostRecord = (companyCategory = '合计') => {
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
  const rows = (costReportData.value.monthly?.rows || []).map(row => ({ ...buildEmptyCostRecord(row.company_category), ...row, is_total: false }))
  const total = { ...buildEmptyCostRecord('合计'), ...(costReportData.value.monthly?.total || {}), company_category: '合计', is_total: true }
  return [...rows, total]
})

const quarterlyTableData = computed(() => {
  const rows = (costReportData.value.quarterly?.rows || []).map(row => ({ ...buildEmptyCostRecord(row.company_category), ...row, is_total: false }))
  const total = { ...buildEmptyCostRecord('合计'), ...(costReportData.value.quarterly?.total || {}), company_category: '合计', is_total: true }
  return [...rows, total]
})

const halfYearlyTableData = computed(() => {
  const rows = (costReportData.value.half_yearly?.rows || []).map(row => ({ ...buildEmptyCostRecord(row.company_category), ...row, is_total: false }))
  const total = { ...buildEmptyCostRecord('合计'), ...(costReportData.value.half_yearly?.total || {}), company_category: '合计', is_total: true }
  return [...rows, total]
})

const yearlyTableData = computed(() => {
  const rows = (costReportData.value.yearly?.rows || []).map(row => ({ ...buildEmptyCostRecord(row.company_category), ...row, is_total: false }))
  const total = { ...buildEmptyCostRecord('合计'), ...(costReportData.value.yearly?.total || {}), company_category: '合计', is_total: true }
  return [...rows, total]
})

const parseYearMonth = () => {
  if (!costMonth.value) return { year: now.getFullYear(), month: now.getMonth() + 1 }
  const [yearStr, monthStr] = costMonth.value.split('-')
  const year = Number(yearStr)
  const month = Number(monthStr)
  if (!year || !month || month < 1 || month > 12) {
    return { year: now.getFullYear(), month: now.getMonth() + 1 }
  }
  return { year, month }
}

const handleQueryCostReport = async () => {
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
  } catch (e) {
    console.error(e)
    ElMessage.error('成本报表查询失败')
  } finally {
    costLoading.value = false
  }
}

const handleExportCostReport = async () => {
  costExportLoading.value = true
  try {
    const { year, month } = parseYearMonth()
    const res = await downloadCostMonthlyQuarterlyReport({ year, month })
    downloadFile(res, `月度季度成本报表_${year}年${String(month).padStart(2, '0')}月.xlsx`)
    ElMessage.success('导出成功')
  } catch (e) {
    console.error(e)
    ElMessage.error('导出失败')
  } finally {
    costExportLoading.value = false
  }
}

const amountFormatter = (_row, _column, value) => {
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
const costCellStyle = ({ column }) => {
  if (COST_FIELDS.includes(column.property)) {
    return { textAlign: 'right' }
  }
  return {}
}

onMounted(() => {
  handleQueryCostReport()
})

// Export State
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

const handleExport = async () => {
    exportLoading.value = true
    try {
        const params = {
            status: exportFilters.value.status
        }
        if (exportFilters.value.dateRange && exportFilters.value.dateRange.length === 2) {
            params.start_date = exportFilters.value.dateRange[0]
            params.end_date = exportFilters.value.dateRange[1]
        }
        const res = await downloadComprehensiveReport(params)
        downloadFile(res, `上游合同综合报表_${new Date().toISOString().slice(0,10)}.xlsx`)
        ElMessage.success('导出成功')
    } catch (e) {
        console.error(e)
        ElMessage.error('导出失败')
    } finally {
        exportLoading.value = false
    }
}

const handleExportRec = async () => {
    recLoading.value = true
    try {
        const params = {}
        if (recDateRange.value && recDateRange.value.length === 2) {
            params.start_date = recDateRange.value[0]
            params.end_date = recDateRange.value[1]
        }
        const res = await downloadReceivablesReport(params)
        downloadFile(res, `上游合同应收款明细_${new Date().toISOString().slice(0,10)}.xlsx`)
        ElMessage.success('导出成功')
    } catch (e) {
        console.error(e)
        ElMessage.error('导出失败')
    } finally {
        recLoading.value = false
    }
}

const handleExportPay = async () => {
    payLoading.value = true
    try {
        const params = {}
        if (payDateRange.value && payDateRange.value.length === 2) {
            params.start_date = payDateRange.value[0]
            params.end_date = payDateRange.value[1]
        }
        const res = await downloadPayablesReport(params)
        downloadFile(res, `下游及管理合同应付款明细_${new Date().toISOString().slice(0,10)}.xlsx`)
        ElMessage.success('导出成功')
    } catch (e) {
        console.error(e)
        ElMessage.error('导出失败')
    } finally {
        payLoading.value = false
    }
}

const handleExportUpInv = async () => {
    upInvLoading.value = true
    try {
        const params = {}
        if (upInvDateRange.value && upInvDateRange.value.length === 2) {
            params.start_date = upInvDateRange.value[0]
            params.end_date = upInvDateRange.value[1]
        }
        const res = await downloadUpstreamInvoicesReport(params)
        downloadFile(res, `上游合同挂账报表_${new Date().toISOString().slice(0,10)}.xlsx`)
        ElMessage.success('导出成功')
    } catch (e) {
        console.error(e)
        ElMessage.error('导出失败')
    } finally {
        upInvLoading.value = false
    }
}

const handleExportDownInv = async () => {
    downInvLoading.value = true
    try {
        const params = {}
        if (downInvDateRange.value && downInvDateRange.value.length === 2) {
            params.start_date = downInvDateRange.value[0]
            params.end_date = downInvDateRange.value[1]
        }
        const res = await downloadDownstreamInvoicesReport(params)
        downloadFile(res, `下游及管理合同挂账报表_${new Date().toISOString().slice(0,10)}.xlsx`)
        ElMessage.success('导出成功')
    } catch (e) {
        console.error(e)
        ElMessage.error('导出失败')
    } finally {
        downInvLoading.value = false
    }
}

const handleExportUpReceipt = async () => {
    upReceiptLoading.value = true
    try {
        const params = {}
        if (upReceiptDateRange.value && upReceiptDateRange.value.length === 2) {
            params.start_date = upReceiptDateRange.value[0]
            params.end_date = upReceiptDateRange.value[1]
        }
        const res = await downloadUpstreamReceiptsReport(params)
        downloadFile(res, `上游合同收款报表_${new Date().toISOString().slice(0,10)}.xlsx`)
        ElMessage.success('导出成功')
    } catch (e) {
        console.error(e)
        ElMessage.error('导出失败')
    } finally {
        upReceiptLoading.value = false
    }
}

const handleExportDownPay = async () => {
    downPayLoading.value = true
    try {
        const params = {}
        if (downPayDateRange.value && downPayDateRange.value.length === 2) {
            params.start_date = downPayDateRange.value[0]
            params.end_date = downPayDateRange.value[1]
        }
        const res = await downloadDownstreamPaymentsReport(params)
        downloadFile(res, `下游及管理合同付款报表_${new Date().toISOString().slice(0,10)}.xlsx`)
        ElMessage.success('导出成功')
    } catch (e) {
        console.error(e)
        ElMessage.error('导出失败')
    } finally {
        downPayLoading.value = false
    }
}

const handleExportExpPay = async () => {
    expPayLoading.value = true
    try {
        const params = {}
        if (expPayDateRange.value && expPayDateRange.value.length === 2) {
            params.start_date = expPayDateRange.value[0]
            params.end_date = expPayDateRange.value[1]
        }
        const res = await downloadExpensePaymentsReport(params)
        downloadFile(res, `无合同费用付款报表_${new Date().toISOString().slice(0,10)}.xlsx`)
        ElMessage.success('导出成功')
    } catch (e) {
        console.error(e)
        ElMessage.error('导出失败')
    } finally {
        expPayLoading.value = false
    }
}

const handleExportUpSettlement = async () => {
    upSettlementLoading.value = true
    try {
        const params = {}
        if (upSettlementDateRange.value && upSettlementDateRange.value.length === 2) {
            params.start_date = upSettlementDateRange.value[0]
            params.end_date = upSettlementDateRange.value[1]
        }
        const res = await downloadUpstreamSettlementsReport(params)
        downloadFile(res, `上游合同结算报表_${new Date().toISOString().slice(0,10)}.xlsx`)
        ElMessage.success('导出成功')
    } catch (e) {
        console.error(e)
        ElMessage.error('导出失败')
    } finally {
        upSettlementLoading.value = false
    }
}

const handleExportDownSettlement = async () => {
    downSettlementLoading.value = true
    try {
        const params = {}
        if (downSettlementDateRange.value && downSettlementDateRange.value.length === 2) {
            params.start_date = downSettlementDateRange.value[0]
            params.end_date = downSettlementDateRange.value[1]
        }
        const res = await downloadDownstreamSettlementsReport(params)
        downloadFile(res, `下游及管理合同结算报表_${new Date().toISOString().slice(0,10)}.xlsx`)
        ElMessage.success('导出成功')
    } catch (e) {
        console.error(e)
        ElMessage.error('导出失败')
    } finally {
        downSettlementLoading.value = false
    }
}

const handleExportAssociation = async () => {
    assocLoading.value = true
    try {
        const params = {
            query: assocQuery.value
        }
        const res = await downloadAssociationReport(params)
        downloadFile(res, `上下游合同关联报表_${new Date().toISOString().slice(0,10)}.xlsx`)
        ElMessage.success('导出成功')
    } catch (e) {
        console.error(e)
        ElMessage.error('导出失败')
    } finally {
        assocLoading.value = false
    }
}

const downloadFile = (res, filename) => {
    const url = window.URL.createObjectURL(new Blob([res]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
}
</script>

<style scoped lang="scss">
.app-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 84px);
}

.page-header {
  margin-bottom: 20px;
  
  .header-content {
      display: flex;
      flex-direction: column;
      
      .title {
        font-size: 18px;
        font-weight: bold;
        color: #303133;
        margin-bottom: 5px;
      }
      
      .subtitle {
        font-size: 13px;
        color: #909399;
      }
  }
}

.cost-report-card {
  margin-bottom: 20px;
  border: 1px solid #e4e7ed;
}

.cost-filter-container {
  margin-bottom: 12px;
}

.cost-title {
  margin: 8px 0 10px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.cost-tabs {
  :deep(.el-tabs__nav-wrap) {
    margin-bottom: 6px;
  }
}

.cost-report-table {
  :deep(th) {
    text-align: center;
    font-weight: 700;
  }

  :deep(.el-table__cell) {
    padding: 8px 0;
  }
}

:deep(.cost-total-row td.el-table__cell) {
  background-color: #fff8c4 !important;
  font-weight: 700;
}

.filter-container {
  background-color: #fff;
  padding: 15px;
  margin-bottom: 20px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  
  .filter-label {
    font-weight: bold;
    color: #606266;
    margin-right: 10px;
    font-size: 14px;
    white-space: nowrap; // Prevent label breaking
  }

  // Common styles for inputs in filters
  .filter-item {
    margin-right: 20px; 
    width: 240px;
    
    &.short {
        width: 150px;
    }
  }
}

/* Chart Cards (Generic for Export Box) */
.chart-card {
  border: none;
  border-radius: 12px;
  margin-bottom: 20px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s;
  
  &:hover {
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
  }
  
  :deep(.el-card__header) {
    padding: 15px 20px;
    border-bottom: 1px solid #f0f2f5;
    background: #fff;
  }
}

@media only screen and (max-width: 768px) {
  .page-header :deep(.el-card__header) {
    display: block; // Show header on mobile but maybe simplified
    padding: 10px;
  }
  
  .app-container {
    padding: 10px;
  }

  .filter-container {
      flex-direction: column;
      align-items: stretch; // Full width items
      
      .filter-label {
          margin-bottom: 5px;
          margin-right: 0;
      }
      
      .filter-item {
          width: 100% !important; // Force full width
          margin-right: 0;
          margin-bottom: 10px;
          
          &.short {
              width: 100% !important;
          }
      }
      
      .el-button {
          width: 100%;
          margin-left: 0 !important;
      }
  }

  .cost-title {
    font-size: 14px;
  }
}
</style>
