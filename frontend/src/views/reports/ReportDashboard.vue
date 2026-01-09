<template>
  <div class="app-container">
    <el-card shadow="hover" class="page-header">
       <template #header>
         <div class="header-content">
           <span class="title">数据查询与导出</span>
           <span class="subtitle">请选择相应报表进行导出</span>
         </div>
       </template>
       
       <el-row :gutter="20">
      <el-col :xs="24" :md="12" style="margin-bottom: 20px;">
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
          style="margin-right: 20px; width: 240px;"
        />
        
        <span class="filter-label">合同状态:</span>
        <el-select v-model="exportFilters.status" style="width: 150px; margin-right: 20px;">
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
              style="margin-right: 20px; width: 240px;"
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
import { ref, reactive } from 'vue'
import { downloadComprehensiveReport, downloadReceivablesReport, downloadPayablesReport, downloadUpstreamInvoicesReport, downloadDownstreamInvoicesReport, downloadUpstreamReceiptsReport, downloadDownstreamPaymentsReport, downloadExpensePaymentsReport, downloadUpstreamSettlementsReport, downloadDownstreamSettlementsReport, downloadAssociationReport } from '@/api/reports'
import { ElMessage } from 'element-plus'
import { Download, Document, Money, Wallet, Coin } from '@element-plus/icons-vue'

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
</style>
