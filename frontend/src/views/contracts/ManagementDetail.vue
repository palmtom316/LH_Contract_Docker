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
        <!-- Edit is usually done in the list view, but could be added here if needed -->
      </div>
    </div>

    <!-- Summary Cards -->
    <el-row :gutter="10" class="summary-cards">
      <el-col :xs="24" :sm="12" :md="4">
        <el-card shadow="hover">
          <template #header><span>合同总额</span></template>
          <div class="amount-text">¥ {{ formatMoney(contract.contract_amount) }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="5">
        <el-card shadow="hover">
          <template #header><span>累计应付</span></template>
          <div class="amount-text warning-text">¥ {{ formatMoney(totalPayables) }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="5">
        <el-card shadow="hover">
          <template #header><span>累计已付</span></template>
          <div class="amount-text success-text">¥ {{ formatMoney(totalPayments) }}</div>
          <el-progress :percentage="Number(paymentPercentage)" :status="Number(paymentPercentage) >= 100 ? 'success' : ''" />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="5">
        <el-card shadow="hover">
          <template #header><span>累计挂账</span></template>
          <div class="amount-text info-text">¥ {{ formatMoney(totalInvoices) }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="5">
        <el-card shadow="hover">
          <template #header><span>合同结算</span></template>
          <div class="amount-text primary-text">¥ {{ formatMoney(totalSettlements) }}</div>
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
          <el-descriptions-item label="甲方(我们)">{{ contract.party_a_name }}</el-descriptions-item>
          <el-descriptions-item label="乙方(供应商)">{{ contract.party_b_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="签约日期">{{ contract.sign_date }}</el-descriptions-item>
          <el-descriptions-item label="签约金额">¥ {{ formatMoney(contract.contract_amount) }}</el-descriptions-item>
          <el-descriptions-item label="费用分类">{{ contract.category }}</el-descriptions-item>

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

      <!-- 2. Payables -->
      <el-tab-pane label="应付款" name="payables">
        <div class="tab-actions">
          <el-button type="warning" size="small" icon="Plus" @click="openFinanceDialog('payable')">新增应付款</el-button>
        </div>
        <el-table :data="payables" border style="width: 100%">
          <el-table-column prop="category" label="款项类别" width="120" />
          <el-table-column prop="amount" label="应付金额" align="right">
            <template #default="{ row }">¥ {{ formatMoney(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="expected_date" label="产生日期" width="120" />
          <el-table-column label="审批文件" width="100" align="center">
            <template #default="{ row }">
               <el-link v-if="row.file_path" :href="getFileUrl(row.file_path)" target="_blank"><el-icon><Document /></el-icon></el-link>
               <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="备注" show-overflow-tooltip />
          <el-table-column label="操作" width="120" align="center" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openEditDialog('payable', row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleDelete('payable', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 3. Invoices (Received) -->
      <el-tab-pane label="挂账明细" name="invoices">
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
          <el-table-column prop="tax_rate" label="税率" width="80" align="center">
            <template #default="{ row }">{{ row.tax_rate ? row.tax_rate + '%' : '-' }}</template>
          </el-table-column>
          <el-table-column prop="supplier_name" label="开票方" show-overflow-tooltip />
          <el-table-column prop="description" label="说明" show-overflow-tooltip />
          <el-table-column label="发票文件" width="120" align="center">
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
              <span v-else style="color: #909399">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openEditDialog('invoice', row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleDelete('invoice', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 4. Payments -->
      <el-tab-pane label="付款明细" name="payments">
          <div class="tab-actions">
          <el-button type="success" size="small" icon="Plus" @click="openFinanceDialog('payment')">新增付款</el-button>
        </div>
        <el-table :data="payments" border style="width: 100%">
          <el-table-column prop="payment_date" label="付款日期" width="120" />
          <el-table-column prop="amount" label="金额" align="right">
            <template #default="{ row }">¥ {{ formatMoney(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="payment_method" label="方式" width="100" />
          <el-table-column prop="payee_name" label="收款单位" show-overflow-tooltip />
          <el-table-column label="支付凭证" width="100" align="center">
            <template #default="{ row }">
               <el-link v-if="row.file_path" :href="getFileUrl(row.file_path)" target="_blank"><el-icon><Document /></el-icon></el-link>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openEditDialog('payment', row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleDelete('payment', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <!-- 5. Settlements -->
      <el-tab-pane label="结算" name="settlements">
          <div class="tab-actions">
          <el-button type="danger" size="small" icon="Plus" @click="openFinanceDialog('settlement')">新增结算</el-button>
        </div>
        <el-table :data="settlements" border style="width: 100%">
          <el-table-column prop="settlement_code" label="结算单号" width="150" />
          <el-table-column prop="settlement_amount" label="结算金额" align="right">
            <template #default="{ row }">¥ {{ formatMoney(row.settlement_amount) }}</template>
          </el-table-column>
          <el-table-column prop="settlement_date" label="结算办结日期" width="120" />
          <el-table-column prop="completion_date" label="完工日期" width="120" />
          <el-table-column prop="warranty_date" label="质保到期日期" width="120" />
          <el-table-column prop="description" label="说明" show-overflow-tooltip />
          <el-table-column label="审批文件" width="100" align="center">
            <template #default="{ row }">
               <el-link v-if="row.file_path" :href="getFileUrl(row.file_path)" target="_blank"><el-icon><Document /></el-icon></el-link>
               <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openEditDialog('settlement', row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleDelete('settlement', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- Finance Create Dialog -->
    <el-dialog v-model="financeDialog.visible" :title="financeDialog.title" width="500px" append-to-body>
      <el-form :model="financeForm" label-width="100px">
        
        <!-- Payable Fields -->
        <template v-if="financeDialog.type === 'payable'">
          <el-form-item label="款项类别">
             <el-select v-model="financeForm.category" style="width: 100%">
              <el-option label="预付款" value="预付款" />
              <el-option label="进度款" value="进度款" />
              <el-option label="完工款" value="完工款" />
              <el-option label="结算款" value="结算款" />
              <el-option label="质保金" value="质保金" />
            </el-select>
          </el-form-item>
          <el-form-item label="应付金额">
            <el-input-number v-model="financeForm.amount" :precision="2" :min="0" :controls="false" style="width: 100%" />
          </el-form-item>
          <el-form-item label="产生日期">
            <el-date-picker v-model="financeForm.expected_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item label="审批文件">
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
          <el-form-item label="备注">
            <el-input v-model="financeForm.description" />
          </el-form-item>
        </template>

        <!-- Invoice Fields -->
        <template v-if="financeDialog.type === 'invoice'">
           <el-form-item label="发票号码">
            <el-input v-model="financeForm.invoice_number" />
          </el-form-item>
          <el-form-item label="发票金额">
            <el-input-number v-model="financeForm.amount" :precision="2" :min="0" :controls="false" style="width: 100%" />
          </el-form-item>
          <el-form-item label="开票日期">
            <el-date-picker v-model="financeForm.invoice_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item label="开票方">
             <el-input v-model="financeForm.supplier_name" />
          </el-form-item>
          <el-form-item label="发票类型">
             <el-select v-model="financeForm.invoice_type" style="width: 100%">
              <el-option label="专票" value="专票" />
              <el-option label="普票" value="普票" />
            </el-select>
          </el-form-item>
          <el-form-item label="发票文件">
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

        <!-- Payment Fields -->
        <template v-if="financeDialog.type === 'payment'">
          <el-form-item label="付款金额">
            <el-input-number v-model="financeForm.amount" :precision="2" :min="0" :controls="false" style="width: 100%" />
          </el-form-item>
          <el-form-item label="付款日期">
            <el-date-picker v-model="financeForm.payment_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item label="收款方">
            <el-input v-model="financeForm.payee_name" />
          </el-form-item>
          <el-form-item label="支付方式">
             <el-select v-model="financeForm.payment_method" style="width: 100%">
              <el-option label="银行转账" value="银行转账" />
              <el-option label="支票" value="支票" />
              <el-option label="现金" value="现金" />
            </el-select>
          </el-form-item>
          <el-form-item label="支付凭证">
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
          <el-form-item label="结算办结日期">
             <el-date-picker v-model="financeForm.settlement_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item label="完工日期">
             <el-date-picker v-model="financeForm.completion_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item label="质保到期日期">
             <el-date-picker v-model="financeForm.warranty_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item label="结算金额">
            <el-input-number v-model="financeForm.settlement_amount" :precision="2" :min="0" :controls="false" style="width: 100%" />
          </el-form-item>
          <el-form-item label="结算审批文件">
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
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Document } from '@element-plus/icons-vue'
import { 
  getContract, 
  getPayables, createPayable, updatePayable, deletePayable,
  getInvoices, createInvoice, updateInvoice, deleteInvoice,
  getPayments, createPayment, updatePayment, deletePayment,
  getSettlements, createSettlement, updateSettlement, deleteSettlement
} from '@/api/contractManagement'
import { uploadFile } from '@/api/common'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const contractId = route.params.id

const loading = ref(false)
const isMobile = ref(window.innerWidth < 768)

const contract = ref({})
const activeTab = ref('info')

// Financial Data Lists
const payables = ref([])
const invoices = ref([])
const payments = ref([])
const settlements = ref([])
const fileList = ref([]) // For dialog uploads

// Dialog State
const financeDialog = reactive({
  visible: false,
  title: '',
  type: '', // 'payable', 'invoice', 'payment', 'settlement'
  isEdit: false,
  editingId: null
})

const financeForm = reactive({})

// Computed
const totalPayables = computed(() => {
  return payables.value.reduce((sum, item) => sum + Number(item.amount), 0)
})

const totalPayments = computed(() => {
  return payments.value.reduce((sum, item) => sum + Number(item.amount), 0)
})

const totalInvoices = computed(() => {
  return invoices.value.reduce((sum, item) => sum + Number(item.amount), 0)
})

const paymentPercentage = computed(() => {
  if (!contract.value.contract_amount) return 0
  const p = (totalPayments.value / contract.value.contract_amount) * 100
  return Math.min(p, 100).toFixed(1)
  return Math.min(p, 100).toFixed(1)
})

const totalSettlements = computed(() => {
  return settlements.value.reduce((sum, item) => sum + Number(item.settlement_amount), 0)
})

// Initial Load
const loadData = async () => {
  loading.value = true
  try {
    contract.value = await getContract(contractId)
    await Promise.all([
      loadPayables(),
      loadInvoices(),
      loadPayments(),
      loadSettlements()
    ])
  } catch (e) {
    console.error(e)
    ElMessage.error('加载合同详情失败')
  } finally {
    loading.value = false
  }
}

const loadPayables = async () => {
  payables.value = await getPayables(contractId)
  console.log('Loaded payables:', payables.value.length)
  if (payables.value.length > 0) console.log('First payable file_path:', payables.value[0].file_path)
}
const loadInvoices = async () => {
  invoices.value = await getInvoices(contractId)
  console.log('Loaded invoices:', invoices.value.length)
  if (invoices.value.length > 0) console.log('First invoice file_path:', invoices.value[0].file_path)
}
const loadPayments = async () => {
  payments.value = await getPayments(contractId)
  console.log('Loaded payments:', payments.value.length)
  if (payments.value.length > 0) console.log('First payment file_path:', payments.value[0].file_path)
}
const loadSettlements = async () => {
  settlements.value = await getSettlements(contractId)
  console.log('Loaded settlements:', settlements.value.length)
  if (settlements.value.length > 0) console.log('First settlement file_path:', settlements.value[0].file_path)
}

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
  if (status === '已完成' || status === '已完工' || status === '已结算') return 'success'
  if (status === '已终止' || status === '已归档' || status === '合同终止') return 'info'
  if (status === '已中止' || status === '合同中止') return 'danger'
  if (status === '待审核' || status === '质保到期') return 'warning'
  if (status === '进行中' || status === '执行中') return 'primary'
  return ''
}

const handleUploadRequest = async (option) => {
  try {
    const res = await uploadFile(option.file)
    console.log('Upload result:', res)
    financeForm.file_path = res.path
    console.log('File path set to:', financeForm.file_path)
    fileList.value = [{ name: option.file.name, url: res.path }]
    ElMessage.success('上传成功')
  } catch (e) {
    ElMessage.error('上传失败')
    option.onError(e)
  }
}

const openFinanceDialog = (type) => {
  financeDialog.type = type
  financeDialog.visible = true
  financeDialog.isEdit = false
  financeDialog.editingId = null
  // Reset form
  Object.keys(financeForm).forEach(key => delete financeForm[key])
  fileList.value = [] // Reset file list
  
  financeForm.contract_id = Number(contractId)
  
  if (type === 'payable') {
    financeDialog.title = '新增应付款'
    Object.assign(financeForm, {
      category: '进度款', amount: 0, expected_date: null, description: '', file_path: ''
    })
  } else if (type === 'invoice') {
    financeDialog.title = '新增收票记录'
    Object.assign(financeForm, {
      invoice_number: '', amount: 0, invoice_date: new Date().toISOString().split('T')[0], 
      invoice_type: '专票', supplier_name: contract.value.party_b_name,
      file_path: '', tax_rate: '0'
    })
  } else if (type === 'payment') {
    financeDialog.title = '新增付款记录'
    Object.assign(financeForm, {
      amount: 0, payment_date: new Date().toISOString().split('T')[0], payment_method: '银行转账', payee_name: contract.value.party_b_name,
      file_path: ''
    })
  } else if (type === 'settlement') {
    financeDialog.title = '新增结算记录'
    Object.assign(financeForm, {
      settlement_code: '',
      settlement_amount: 0,
      settlement_date: new Date().toISOString().split('T')[0],
      completion_date: null,
      warranty_date: null,
      status: '待审核',
      description: '',
      file_path: ''
    })
  }
}

const openEditDialog = (type, row) => {
  financeDialog.type = type
  financeDialog.visible = true
  financeDialog.isEdit = true
  financeDialog.editingId = row.id
  Object.keys(financeForm).forEach(key => delete financeForm[key])
  financeForm.contract_id = Number(contractId)
  
  if (type === 'payable') {
    financeDialog.title = '编辑应付款'
    Object.assign(financeForm, {
      category: row.category,
      amount: row.amount,
      expected_date: row.expected_date,
      description: row.description,
      file_path: row.file_path || ''
    })
    fileList.value = row.file_path ? [{ name: '已上传文件', url: row.file_path }] : []
  } else if (type === 'invoice') {
    financeDialog.title = '编辑收票记录'
    Object.assign(financeForm, {
      invoice_number: row.invoice_number,
      amount: row.amount,
      invoice_date: row.invoice_date,
      invoice_type: row.invoice_type,
      supplier_name: row.supplier_name,
      file_path: row.file_path || '',
      tax_rate: row.tax_rate ? String(row.tax_rate) : '0'
    })
    fileList.value = row.file_path ? [{ name: '已上传文件', url: row.file_path }] : []
  } else if (type === 'payment') {
    financeDialog.title = '编辑付款记录'
    Object.assign(financeForm, {
      amount: row.amount,
      payment_date: row.payment_date,
      payment_method: row.payment_method,
      payee_name: row.payee_name,
      file_path: row.file_path || ''
    })
    fileList.value = row.file_path ? [{ name: '已上传文件', url: row.file_path }] : []
  } else if (type === 'settlement') {
    financeDialog.title = '编辑结算记录'
    Object.assign(financeForm, {
      settlement_code: row.settlement_code,
      settlement_amount: row.settlement_amount,
      settlement_date: row.settlement_date,
      completion_date: row.completion_date,
      warranty_date: row.warranty_date,
      status: row.status,
      description: row.description,
      file_path: row.file_path || ''
    })
    fileList.value = row.file_path ? [{ name: '已上传文件', url: row.file_path }] : []
  }
}

const handleDelete = (type, row) => {
  const typeNames = {
    payable: '应付款',
    invoice: '收票',
    payment: '付款',
    settlement: '结算'
  }
  ElMessageBox.confirm(`确定删除该${typeNames[type]}记录吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      if (type === 'payable') {
        await deletePayable(contractId, row.id)
        await loadPayables()
      } else if (type === 'invoice') {
        await deleteInvoice(contractId, row.id)
        await loadInvoices()
      } else if (type === 'payment') {
        await deletePayment(contractId, row.id)
        await loadPayments()
      } else if (type === 'settlement') {
        await deleteSettlement(contractId, row.id)
        await loadSettlements()
      }
      ElMessage.success('删除成功')
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const submitFinance = async () => {
  try {
    console.log('Submitting finance form:', financeForm)
    console.log('Finance type:', financeDialog.type)
    console.log('File path:', financeForm.file_path)
    
    if (financeDialog.type === 'payable') {
      if (financeDialog.isEdit) {
        await updatePayable(contractId, financeDialog.editingId, financeForm)
      } else {
        await createPayable(contractId, financeForm)
      }
      await loadPayables()
    } else if (financeDialog.type === 'invoice') {
      if (financeDialog.isEdit) {
        await updateInvoice(contractId, financeDialog.editingId, financeForm)
      } else {
        await createInvoice(contractId, financeForm)
      }
      await loadInvoices()
    } else if (financeDialog.type === 'payment') {
      if (financeDialog.isEdit) {
        await updatePayment(contractId, financeDialog.editingId, financeForm)
      } else {
        await createPayment(contractId, financeForm)
      }
      await loadPayments()
    } else if (financeDialog.type === 'settlement') {
      // Clean up dates
      if (financeForm.completion_date === '') financeForm.completion_date = null
      if (financeForm.warranty_date === '') financeForm.warranty_date = null
      if (financeDialog.isEdit) {
        await updateSettlement(contractId, financeDialog.editingId, financeForm)
      } else {
        await createSettlement(contractId, financeForm)
      }
      await loadSettlements()
    }
    ElMessage.success(financeDialog.isEdit ? '修改成功' : '保存成功')
    financeDialog.visible = false
  } catch (e) {
    console.error('Submit error:', e)
    ElMessage.error(financeDialog.isEdit ? '修改失败' : '保存失败')
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
    &.warning-text { color: #e6a23c; }
    &.info-text { color: #409eff; }
  }
}

.tab-actions {
  margin-bottom: 15px;
}
</style>
