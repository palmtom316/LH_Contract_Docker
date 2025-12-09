<template>
  <div class="app-container" v-loading="loading">
    
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <el-button link icon="ArrowLeft" @click="$router.back()">返回</el-button>
        <h2 class="title">{{ contract.contract_name || '合同详情' }}</h2>
        <el-tag :type="getStatusType(contract.status)">{{ contract.status }}</el-tag>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleEdit">编辑合同</el-button>
      </div>
    </div>

    <!-- Summary Cards -->
    <!-- Summary Cards -->
    <el-row :gutter="20" class="summary-cards">
      <el-col :span="6" :xs="12">
        <el-card shadow="hover">
          <template #header><span>合同总额</span></template>
          <div class="amount-text">¥ {{ formatMoney(contract.contract_amount) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6" :xs="12">
        <el-card shadow="hover">
          <template #header><span>累计应收款</span></template>
          <div class="amount-text info-text">¥ {{ formatMoney(totalReceivables) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6" :xs="12">
        <el-card shadow="hover">
          <template #header><span>累计回款</span></template>
          <div class="amount-text success-text">¥ {{ formatMoney(totalReceipts) }}</div>
          <el-progress :percentage="Number(receiptPercentage)" :status="Number(receiptPercentage) >= 100 ? 'success' : ''" />
        </el-card>
      </el-col>
      <el-col :span="6" :xs="12">
        <el-card shadow="hover">
          <template #header><span>累计开票</span></template>
          <div class="amount-text warning-text">¥ {{ formatMoney(totalInvoices) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Main Content Tabs -->
    <el-tabs v-model="activeTab" class="main-tabs" type="border-card">
      
      <!-- 1. Basic Info -->
      <el-tab-pane label="基本信息" name="info">
        <el-descriptions :column="isMobile ? 1 : 2" border>
          <el-descriptions-item label="合同序号">{{ contract.id }}</el-descriptions-item>
          <el-descriptions-item label="合同编号">{{ contract.contract_code }}</el-descriptions-item>
          <el-descriptions-item label="合同名称">{{ contract.contract_name }}</el-descriptions-item>
          <el-descriptions-item label="合同甲方单位">{{ contract.party_a_name }}</el-descriptions-item>
          <el-descriptions-item label="合同乙方单位">{{ contract.party_b_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="签约日期">{{ contract.sign_date }}</el-descriptions-item>
          <el-descriptions-item label="签约金额">¥ {{ formatMoney(contract.contract_amount) }}</el-descriptions-item>
          <el-descriptions-item label="合同类别">{{ contract.category }}</el-descriptions-item>
          <el-descriptions-item label="公司合同分类">{{ contract.company_category || '-' }}</el-descriptions-item>
          <el-descriptions-item label="计价模式">{{ contract.pricing_mode || '-' }}</el-descriptions-item>
          <el-descriptions-item label="管理模式">{{ contract.management_mode || '-' }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ contract.responsible_person || '-' }}</el-descriptions-item>
          <el-descriptions-item label="合同文件" :span="2">
            <el-link 
              v-if="contract.contract_file_path" 
              type="primary" 
              :href="getFileUrl(contract.contract_file_path)" 
              target="_blank" 
              :underline="false"
            >
              <el-icon class="el-icon--left"><Document /></el-icon> 查看合同文件
            </el-link>
            <span v-else style="color: #909399">未上传</span>
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ contract.notes }}</el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>

      <!-- 2. Receivables -->
      <el-tab-pane label="应收款" name="receivables">
        <div class="tab-actions">
          <el-button type="primary" size="small" icon="Plus" @click="openFinanceDialog('receivable')">新增应收款</el-button>
        </div>
        <el-table :data="receivables" border style="width: 100%">
          <el-table-column prop="category" label="应收款类别" width="120" />
          <el-table-column prop="amount" label="金额" align="right">
            <template #default="{ row }">¥ {{ formatMoney(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="expected_date" label="发生时间" width="120" />
          <el-table-column prop="description" label="备注" show-overflow-tooltip />
          <el-table-column label="应收款审批文件" width="150" align="center">
            <template #default="{ row }">
              <el-link 
                v-if="row.file_path" 
                type="primary" 
                :href="getFileUrl(row.file_path)" 
                target="_blank"
                :underline="false"
              >
                <el-icon><Document /></el-icon> 查看文件
              </el-link>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 3. Invoices (Guazhang) -->
      <el-tab-pane label="挂账" name="invoices">
          <div class="tab-actions">
          <el-button type="primary" size="small" icon="Plus" @click="openFinanceDialog('invoice')">新增挂账</el-button>
        </div>
        <el-table :data="invoices" border style="width: 100%">
          <el-table-column prop="invoice_number" label="发票号" width="150" />
          <el-table-column prop="amount" label="金额" align="right">
            <template #default="{ row }">¥ {{ formatMoney(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="invoice_date" label="开票日期" width="120" />
          <el-table-column prop="invoice_type" label="类型" width="100" />
          <el-table-column prop="description" label="说明" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>

      <!-- 4. Receipts (Payment) -->
      <el-tab-pane label="回款" name="receipts">
          <div class="tab-actions">
          <el-button type="success" size="small" icon="Plus" @click="openFinanceDialog('receipt')">新增回款</el-button>
        </div>
        <el-table :data="receipts" border style="width: 100%">
          <el-table-column prop="receipt_date" label="到账日期" width="120" />
          <el-table-column prop="amount" label="金额" align="right">
            <template #default="{ row }">¥ {{ formatMoney(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="payment_method" label="方式" width="100" />
          <el-table-column prop="payer_name" label="付款单位" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>
      
      <!-- 5. Settlements -->
      <el-tab-pane label="结算" name="settlements">
          <div class="tab-actions">
          <el-button type="warning" size="small" icon="Plus" @click="openFinanceDialog('settlement')">新增结算</el-button>
        </div>
        <el-table :data="settlements" border style="width: 100%">
          <el-table-column prop="settlement_code" label="结算单号" width="150" />
          <el-table-column prop="settlement_amount" label="结算金额" align="right">
            <template #default="{ row }">¥ {{ formatMoney(row.settlement_amount) }}</template>
          </el-table-column>
          <el-table-column prop="settlement_date" label="结算日期" width="120" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="description" label="说明" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- Finance Create Dialog -->
    <el-dialog v-model="financeDialog.visible" :title="financeDialog.title" width="500px" append-to-body>
      <el-form :model="financeForm" label-width="100px">
        
        <!-- Receivable Fields -->
        <template v-if="financeDialog.type === 'receivable'">
          <el-form-item label="应收款类别">
             <el-select v-model="financeForm.category" style="width: 100%">
              <el-option label="预付款" value="预付款" />
              <el-option label="进度款" value="进度款" />
              <el-option label="结算款" value="结算款" />
              <el-option label="质保金" value="质保金" />
            </el-select>
          </el-form-item>
          <el-form-item label="应收款金额">
            <el-input-number v-model="financeForm.amount" :precision="2" :min="0" :controls="false" class="amount-input-right" style="width: 100%" />
          </el-form-item>
          <el-form-item label="发生时间">
            <el-date-picker v-model="financeForm.expected_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="financeForm.description" />
          </el-form-item>
          <el-form-item label="应收款审批文件">
            <el-upload
              class="upload-demo"
              action="#"
              :http-request="handleUploadRequest"
              :limit="1"
              :file-list="fileList"
              accept=".pdf"
            >
              <template #trigger>
                <el-button type="primary">选择文件 (PDF)</el-button>
              </template>
            </el-upload>
          </el-form-item>
        </template>

        <!-- Invoice Fields -->
        <template v-if="financeDialog.type === 'invoice'">
           <el-form-item label="发票号码">
            <el-input v-model="financeForm.invoice_number" />
          </el-form-item>
          <el-form-item label="开票金额">
            <el-input-number v-model="financeForm.amount" :precision="2" :min="0" style="width: 100%" />
          </el-form-item>
          <el-form-item label="开票日期">
            <el-date-picker v-model="financeForm.invoice_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item label="发票类型">
             <el-select v-model="financeForm.invoice_type" style="width: 100%">
              <el-option label="专票" value="专票" />
              <el-option label="普票" value="普票" />
            </el-select>
          </el-form-item>
        </template>

        <!-- Receipt Fields -->
        <template v-if="financeDialog.type === 'receipt'">
          <el-form-item label="回款金额">
            <el-input-number v-model="financeForm.amount" :precision="2" :min="0" style="width: 100%" />
          </el-form-item>
          <el-form-item label="到账日期">
            <el-date-picker v-model="financeForm.receipt_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item label="付款方">
            <el-input v-model="financeForm.payer_name" />
          </el-form-item>
          <el-form-item label="支付方式">
             <el-select v-model="financeForm.payment_method" style="width: 100%">
              <el-option label="银行转账" value="银行转账" />
              <el-option label="支票" value="支票" />
              <el-option label="现金" value="现金" />
            </el-select>
          </el-form-item>
          <el-form-item label="回款附件">
            <el-upload
              class="upload-demo"
              action="#"
              :http-request="handleUploadRequest"
              :limit="1"
              :file-list="fileList"
              accept=".pdf"
            >
              <template #trigger>
                <el-button type="primary">选择文件 (PDF)</el-button>
              </template>
            </el-upload>
          </el-form-item>
        </template>

        <!-- Settlement Fields -->
        <template v-if="financeDialog.type === 'settlement'">
          <el-form-item label="结算单号">
            <el-input v-model="financeForm.settlement_code" placeholder="单号" />
          </el-form-item>
          <el-form-item label="结算日期">
             <el-date-picker v-model="financeForm.settlement_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item label="结算金额">
            <el-input-number v-model="financeForm.settlement_amount" :precision="2" :min="0" style="width: 100%" />
          </el-form-item>
          <el-form-item label="说明">
            <el-input v-model="financeForm.description" type="textarea" />
          </el-form-item>
        </template>

      </el-form>
      <template #footer>
        <el-button @click="financeDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitFinance">提交</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Document } from '@element-plus/icons-vue'
import { 
  getContract, 
  getReceivables, createReceivable,
  getInvoices, createInvoice,
  getReceipts, createReceipt,
  getSettlements, createSettlement
} from '@/api/contractUpstream'
import { uploadFile } from '@/api/common'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const contractId = route.params.id

const loading = ref(false)
const isMobile = ref(window.innerWidth < 768)

const contract = ref({})
const activeTab = ref('info')
// const activeFinanceTab = ref('receivables') // Removed

// Financial Data Lists
const receivables = ref([])
const invoices = ref([])
const receipts = ref([])
const settlements = ref([])
const fileList = ref([]) // For dialog uploads

// Dialog State
const financeDialog = reactive({
  visible: false,
  title: '',
  type: '' // 'receivable', 'invoice', 'receipt'
})

const financeForm = reactive({})

// Computed
const totalReceivables = computed(() => {
  return receivables.value.reduce((sum, item) => sum + Number(item.amount), 0)
})

const totalReceipts = computed(() => {
  return receipts.value.reduce((sum, item) => sum + Number(item.amount), 0)
})

const totalInvoices = computed(() => {
  return invoices.value.reduce((sum, item) => sum + Number(item.amount), 0)
})

const receiptPercentage = computed(() => {
  if (!contract.value.contract_amount) return 0
  const p = (totalReceipts.value / contract.value.contract_amount) * 100
  return Math.min(p, 100).toFixed(1)
})

// Initial Load
const loadData = async () => {
  loading.value = true
  try {
    contract.value = await getContract(contractId)
    await Promise.all([
      loadReceivables(),
      loadInvoices(),
      loadReceipts(),
      loadSettlements()
    ])
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const loadReceivables = async () => receivables.value = await getReceivables(contractId)
const loadInvoices = async () => invoices.value = await getInvoices(contractId)
const loadReceipts = async () => receipts.value = await getReceipts(contractId)
const loadSettlements = async () => settlements.value = await getSettlements(contractId)

// Helpers
const formatMoney = (val) => {
  if (!val) return '0.00'
  return Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const getFileUrl = (path) => {
  if (!path) return ''
  const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  const baseUrl = apiUrl.replace(/\/api\/v1\/?$/, '')
  return `${baseUrl}${path}`
}

const getStatusType = (status) => {
  const map = { '进行中': 'primary', '已完成': 'success', '已终止': 'info' }
  return map[status] || ''
}

const handleUploadRequest = async (option) => {
  try {
    const res = await uploadFile(option.file)
    financeForm.file_path = res.path
    fileList.value = [{ name: option.file.name, url: res.path }]
    ElMessage.success('上传成功')
  } catch (e) {
    ElMessage.error('上传失败')
    option.onError(e)
  }
}

// Actions
const handleEdit = () => {
  // Navigate back to list or open edit dialog (not implemented in this view directly)
  ElMessage.info('请在列表页点击编辑')
}

const openFinanceDialog = (type) => {
  financeDialog.type = type
  financeDialog.visible = true
  // Reset form
  Object.keys(financeForm).forEach(key => delete financeForm[key])
  fileList.value = [] // Reset file list
  
  financeForm.contract_id = Number(contractId)
  
  if (type === 'receivable') {
    financeDialog.title = '新增应收款'
    Object.assign(financeForm, {
      category: '进度款', amount: 0, expected_date: '', description: '',
      file_path: ''
    })
  } else if (type === 'invoice') {
    financeDialog.title = '新增开票记录'
    Object.assign(financeForm, {
      invoice_number: '', amount: 0, invoice_date: new Date().toISOString().split('T')[0], invoice_type: '专票'
    })
  } else if (type === 'receipt') {
    financeDialog.title = '新增回款记录'
    Object.assign(financeForm, {
      amount: 0, receipt_date: new Date().toISOString().split('T')[0], payment_method: '银行转账', payer_name: contract.value.party_a_name,
      file_path: ''
    })
  } else if (type === 'settlement') {
    financeDialog.title = '新增结算记录'
    Object.assign(financeForm, {
      settlement_code: '',
      settlement_amount: 0,
      settlement_date: new Date().toISOString().split('T')[0],
      status: '待审核',
      description: ''
    })
  }
}

const submitFinance = async () => {
  try {
    if (financeDialog.type === 'receivable') {
      await createReceivable(contractId, financeForm)
      await loadReceivables()
    } else if (financeDialog.type === 'invoice') {
      await createInvoice(contractId, financeForm)
      await loadInvoices()
    } else if (financeDialog.type === 'receipt') {
      await createReceipt(contractId, financeForm)
      await loadReceipts()
    } else if (financeDialog.type === 'settlement') {
      await createSettlement(contractId, financeForm)
      await loadSettlements()
    }
    ElMessage.success('保存成功')
    financeDialog.visible = false
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', () => isMobile.value = window.innerWidth < 768)
})
</script>

<style scoped lang="scss">
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 15px;
    
    .title { margin: 0; font-size: 20px; }
  }
}

.summary-cards {
  margin-bottom: 20px;
  .amount-text {
    font-size: 24px;
    font-weight: bold;
    color: #303133;
    
    &.success-text { color: #67c23a; }
    &.info-text { color: #409eff; }
  }
}

.tab-actions {
  margin-bottom: 15px;
}
.tab-actions {
  margin-bottom: 15px;
}

:deep(.amount-input-right .el-input__inner) {
  text-align: right;
}
</style>
