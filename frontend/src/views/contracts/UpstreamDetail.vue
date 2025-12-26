<template>
<div class="app-container">
    
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <div class="back-link" @click="handleBack">
          <el-icon><ArrowLeft /></el-icon> 返回
        </div>
        <h2 class="title">{{ contract.contract_name || '合同详情' }}</h2>
        <el-tag :type="getStatusType(contract.status)">{{ contract.status }}</el-tag>
      </div>
      <div class="header-right">
        <!-- Edit button removed -->
      </div>
    </div>

    <!-- Summary Cards -->
    <!-- Summary Cards -->
    <el-row :gutter="20" class="summary-cards">
      <el-col :span="4" :xs="12">
        <el-card shadow="hover">
          <template #header><span>合同总额</span></template>
          <div class="amount-text">¥ {{ formatMoney(contract.contract_amount) }}</div>
        </el-card>
      </el-col>
      <el-col :span="4" :xs="12">
        <el-card shadow="hover">
          <template #header><span>累计应收款</span></template>
          <div class="amount-text info-text">¥ {{ formatMoney(totalReceivables) }}</div>
        </el-card>
      </el-col>
      <el-col :span="4" :xs="12">
        <el-card shadow="hover">
          <template #header><span>累计回款</span></template>
          <div class="amount-text success-text">¥ {{ formatMoney(totalReceipts) }} <span class="percentage-inline">({{ receiptPercentage }}%)</span></div>
        </el-card>
      </el-col>
      <el-col :span="4" :xs="12">
        <el-card shadow="hover">
          <template #header><span>累计开票</span></template>
          <div class="amount-text warning-text">¥ {{ formatMoney(totalInvoices) }}</div>
        </el-card>
      </el-col>
      <el-col :span="4" :xs="12">
        <el-card shadow="hover">
          <template #header><span>累计结算</span></template>
          <div class="amount-text" style="color: #626aef">¥ {{ formatMoney(totalSettlements) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Main Content Tabs -->
    <el-tabs v-model="activeTab" class="main-tabs" type="border-card">
      
      <!-- 1. Basic Info -->
      <el-tab-pane label="基本信息" name="info">
        <el-descriptions :column="isMobile ? 1 : 2" border>
          <el-descriptions-item label="合同序号">{{ contract.serial_number }}</el-descriptions-item>
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
          <el-button v-if="userStore.canManageReceivables" type="primary" size="small" icon="Plus" @click="openFinanceDialog('receivable')">新增应收款</el-button>
        </div>
        <el-table :data="receivables" border style="width: 100%">
          <el-table-column prop="category" label="应收款类别" width="120">
            <template #default="{ row }">{{ formatReceivableCategory(row.category) }}</template>
          </el-table-column>
          <el-table-column prop="amount" label="金额" align="right">
            <template #default="{ row }">¥ {{ formatMoney(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="expected_date" label="发生时间" width="120" />
          <el-table-column prop="description" label="备注" show-overflow-tooltip />
          <el-table-column label="应收款审批文件" width="150" align="center">
            <template #default="{ row }">
              <el-button 
                v-if="row.file_path" 
                link 
                type="primary" 
                @click="openFile(row.file_path)"
              >
                <el-icon class="el-icon--left"><Document /></el-icon> 查看文件
              </el-button>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center" fixed="right">
            <template #default="{ row }">
              <el-button v-if="userStore.canManageReceivables" link type="primary" size="small" @click="openEditDialog('receivable', row)">编辑</el-button>
              <el-button v-if="userStore.canManageReceivables" link type="danger" size="small" @click="handleDelete('receivable', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 3. Invoices (Guazhang) -->
      <el-tab-pane label="挂账" name="invoices">
          <div class="tab-actions">
          <el-button v-if="userStore.canManageInvoices" type="primary" size="small" icon="Plus" @click="openFinanceDialog('invoice')">新增挂账</el-button>
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
          <el-table-column prop="description" label="说明" show-overflow-tooltip />
          <el-table-column label="发票文件" width="120" align="center">
            <template #default="{ row }">
              <el-button 
                v-if="row.file_path" 
                link 
                type="primary" 
                @click="openFile(row.file_path)"
              >
                <el-icon class="el-icon--left"><Document /></el-icon> 查看文件
              </el-button>
              <span v-else style="color: #909399">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center" fixed="right">
            <template #default="{ row }">
              <el-button v-if="userStore.canManageInvoices" link type="primary" size="small" @click="openEditDialog('invoice', row)">编辑</el-button>
              <el-button v-if="userStore.canManageInvoices" link type="danger" size="small" @click="handleDelete('invoice', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 4. Receipts (Payment) -->
      <el-tab-pane label="回款" name="receipts">
          <div class="tab-actions">
          <el-button v-if="userStore.canManagePayments" type="success" size="small" icon="Plus" @click="openFinanceDialog('receipt')">新增回款</el-button>
        </div>
        <el-table :data="receipts" border style="width: 100%">
          <el-table-column prop="receipt_date" label="到账日期" width="120" />
          <el-table-column prop="amount" label="金额" align="right">
            <template #default="{ row }">¥ {{ formatMoney(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="payment_method" label="方式" width="100" />
          <el-table-column prop="payer_name" label="付款单位" show-overflow-tooltip />
          <el-table-column label="回款附件" width="120" align="center">
            <template #default="{ row }">
              <el-button 
                v-if="row.file_path" 
                link 
                type="primary" 
                @click="openFile(row.file_path)"
              >
                <el-icon class="el-icon--left"><Document /></el-icon> 查看文件
              </el-button>
              <span v-else style="color: #909399">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center" fixed="right">
            <template #default="{ row }">
              <el-button v-if="userStore.canManagePayments" link type="primary" size="small" @click="openEditDialog('receipt', row)">编辑</el-button>
              <el-button v-if="userStore.canManagePayments" link type="danger" size="small" @click="handleDelete('receipt', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <!-- 5. Settlements -->
      <el-tab-pane label="结算" name="settlements">
          <div class="tab-actions">
          <el-button v-if="userStore.canManageSettlements" type="warning" size="small" icon="Plus" @click="openFinanceDialog('settlement')">新增结算</el-button>
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
          <el-table-column label="审核报告" width="100" align="center">
            <template #default="{ row }">
              <el-button v-if="row.audit_report_path" link type="primary" @click="openFile(row.audit_report_path)">
                <el-icon class="el-icon--left"><Document /></el-icon> 查看
              </el-button>
              <span v-else style="color: #909399">-</span>
            </template>
          </el-table-column>
          <el-table-column label="开工报告" width="100" align="center">
            <template #default="{ row }">
              <el-button v-if="row.start_report_path" link type="primary" @click="openFile(row.start_report_path)">
                <el-icon class="el-icon--left"><Document /></el-icon> 查看
              </el-button>
              <span v-else style="color: #909399">-</span>
            </template>
          </el-table-column>
          <el-table-column label="竣工报告" width="100" align="center">
            <template #default="{ row }">
              <el-button v-if="row.completion_report_path" link type="primary" @click="openFile(row.completion_report_path)">
                <el-icon class="el-icon--left"><Document /></el-icon> 查看
              </el-button>
              <span v-else style="color: #909399">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center" fixed="right">
            <template #default="{ row }">
              <el-button v-if="userStore.canManageSettlements" link type="primary" size="small" @click="openEditDialog('settlement', row)">编辑</el-button>
              <el-button v-if="userStore.canManageSettlements" link type="danger" size="small" @click="handleDelete('settlement', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- Finance Create Dialog -->
    <el-dialog v-model="financeDialog.visible" :title="financeDialog.title" width="500px" append-to-body>
      <el-form :model="financeForm" label-width="100px">
        
        <!-- Receivable Fields -->
        <template v-if="financeDialog.type === 'receivable'">
          <el-form-item label="应收款类别">
             <DictSelect 
              v-model="financeForm.category" 
              category="receivable_category" 
              placeholder="请选择类别" 
              style="width: 100%" 
            />
          </el-form-item>
          <el-form-item label="应收款金额">
            <FormulaInput v-model="financeForm.amount" class="amount-input-right" style="width: 100%" />
          </el-form-item>
          <el-form-item label="发生时间">
            <SmartDateInput v-model="financeForm.expected_date" style="width: 100%" />
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
            <FormulaInput v-model="financeForm.amount" class="amount-input-right" style="width: 100%" />
          </el-form-item>
          <el-form-item label="税率">
            <el-select v-model="financeForm.tax_rate" style="width: 100%">
              <el-option label="0%" value="0" />
              <el-option label="1%" value="1" />
              <el-option label="3%" value="3" />
              <el-option label="6%" value="6" />
              <el-option label="9%" value="9" />
              <el-option label="13%" value="13" />
            </el-select>
          </el-form-item>
          <el-form-item label="开票日期">
            <SmartDateInput v-model="financeForm.invoice_date" style="width: 100%" />
          </el-form-item>
          <el-form-item label="发票类型">
             <el-select v-model="financeForm.invoice_type" style="width: 100%">
              <el-option label="专票" value="专票" />
              <el-option label="普票" value="普票" />
            </el-select>
          </el-form-item>
          <el-form-item label="发票文件">
            <el-upload
              :show-file-list="true"
              :file-list="invoiceFileList"
              :http-request="handleInvoiceUpload"
              accept=".pdf,.jpg,.jpeg,.png"
              :limit="1"
            >
              <template #trigger>
                <el-button type="primary">选择文件</el-button>
              </template>
            </el-upload>
          </el-form-item>
        </template>

        <!-- Receipt Fields -->
        <template v-if="financeDialog.type === 'receipt'">
          <el-form-item label="回款金额">
            <FormulaInput v-model="financeForm.amount" style="width: 100%" />
          </el-form-item>
          <el-form-item label="到账日期">
            <SmartDateInput v-model="financeForm.receipt_date" style="width: 100%" />
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
          <el-form-item label="结算办结日期">
             <SmartDateInput v-model="financeForm.settlement_date" style="width: 100%" />
          </el-form-item>
          <el-form-item label="完工日期">
             <SmartDateInput v-model="financeForm.completion_date" style="width: 100%" />
          </el-form-item>
          <el-form-item label="质保到期日期">
             <SmartDateInput v-model="financeForm.warranty_date" style="width: 100%" />
          </el-form-item>
          <el-form-item label="结算金额">
            <FormulaInput v-model="financeForm.settlement_amount" style="width: 100%" />
          </el-form-item>
          <el-form-item label="说明">
            <el-input v-model="financeForm.description" type="textarea" />
          </el-form-item>
          <el-form-item label="结算审核报告">
            <el-upload
              action="#"
              :http-request="(opt) => handleSettlementUpload(opt, 'audit_report_path')"
              :limit="1"
              :file-list="auditReportFileList"
              accept=".pdf"
            >
              <template #trigger>
                <el-button type="primary">选择文件 (PDF)</el-button>
              </template>
            </el-upload>
          </el-form-item>
          <el-form-item label="开工报告">
            <el-upload
              action="#"
              :http-request="(opt) => handleSettlementUpload(opt, 'start_report_path')"
              :limit="1"
              :file-list="startReportFileList"
              accept=".pdf"
            >
              <template #trigger>
                <el-button type="primary">选择文件 (PDF)</el-button>
              </template>
            </el-upload>
          </el-form-item>
          <el-form-item label="竣工报告">
            <el-upload
              action="#"
              :http-request="(opt) => handleSettlementUpload(opt, 'completion_report_path')"
              :limit="1"
              :file-list="completionReportFileList"
              accept=".pdf"
            >
              <template #trigger>
                <el-button type="primary">选择文件 (PDF)</el-button>
              </template>
            </el-upload>
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
import { ref, reactive, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import DictSelect from '@/components/DictSelect.vue'
import FormulaInput from '@/components/FormulaInput.vue'
import SmartDateInput from '@/components/SmartDateInput.vue'
import { useRoute, useRouter } from 'vue-router'
import { Document } from '@element-plus/icons-vue'
import { 
  getContract, 
  getReceivables, createReceivable, updateReceivable, deleteReceivable,
  getInvoices, createInvoice, updateInvoice, deleteInvoice,
  getReceipts, createReceipt, updateReceipt, deleteReceipt,
  getSettlements, createSettlement, updateSettlement, deleteSettlement, getContractSummary
} from '@/api/contractUpstream'
import { uploadFile } from '@/api/common'
import { getFileUrl, formatMoney, getStatusType } from '@/utils/common'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

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
const invoiceFileList = ref([]) // For invoice file uploads
// Settlement report file lists
const auditReportFileList = ref([])
const startReportFileList = ref([])
const completionReportFileList = ref([])

// Dialog State
const financeDialog = reactive({
  visible: false,
  title: '',
  type: '', // 'receivable', 'invoice', 'receipt', 'settlement'
  isEdit: false,
  editingId: null
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

const totalSettlements = computed(() => {
  return settlements.value.reduce((sum, item) => sum + Number(item.settlement_amount), 0)
})

const receiptPercentage = computed(() => {
  if (!totalReceivables.value || totalReceivables.value === 0) return 0
  const p = (totalReceipts.value / totalReceivables.value) * 100
  return Math.min(p, 100).toFixed(1)
})

// Initial Load
const loadData = async () => {
  loading.value = true
  try {
    contract.value = await getContract(contractId)
    await Promise.all([loadReceivables(), loadInvoices(), loadReceipts(), loadSettlements()])
  } catch (e) {
    ElMessage.error('加载合同数据失败')
  } finally {
    loading.value = false
  }
}

const loadReceivables = async () => { receivables.value = await getReceivables(contractId) }
const loadInvoices = async () => { invoices.value = await getInvoices(contractId) }
const loadReceipts = async () => { receipts.value = await getReceipts(contractId) }
const loadSettlements = async () => { settlements.value = await getSettlements(contractId) }

// Helpers
const formatReceivableCategory = (value) => {
  const map = {
    'ADVANCE_PAYMENT': '预付款',
    'PROGRESS_PAYMENT': '进度款',
    'SETTLEMENT_PAYMENT': '结算款',
    'RETENTION_MONEY': '质保金',
    'OTHER': '其他'
  }
  return map[value] || value
}

const handleUploadRequest = async (option) => {
  console.log('===== handleUploadRequest START =====')
  console.log('Uploading file:', option.file.name)
  console.log('financeForm BEFORE upload:', JSON.parse(JSON.stringify(financeForm)))
  
  try {
    const res = await uploadFile(option.file)
    console.log('Upload response:', res)
    console.log('Setting file_path to:', res.path)
    
    financeForm.file_path = res.path
    
    console.log('financeForm AFTER setting file_path:', JSON.parse(JSON.stringify(financeForm)))
    console.log('financeForm.file_path value:', financeForm.file_path)
    
    fileList.value = [{ name: option.file.name, url: res.path }]
    option.onSuccess(res)
    ElMessage.success('上传成功')
  } catch (e) {
    console.error('Upload error:', e)
    ElMessage.error('上传失败')
    option.onError(e)
  }
  console.log('===== handleUploadRequest END =====')
}

const handleInvoiceUpload = async (option) => {
  try {
    const res = await uploadFile(option.file)
    console.log('Invoice upload result:', res)
    financeForm.file_path = res.path
    console.log('Invoice file path set to:', financeForm.file_path)
    invoiceFileList.value = [{ name: option.file.name, url: res.path }]
    ElMessage.success('上传成功')
  } catch (e) {
    ElMessage.error('上传失败')
    option.onError(e)
  }
}

const handleSettlementUpload = async (option, fieldName) => {
  try {
    const res = await uploadFile(option.file)
    financeForm[fieldName] = res.path
    const fileData = [{ name: option.file.name, url: res.path }]
    if (fieldName === 'audit_report_path') {
      auditReportFileList.value = fileData
    } else if (fieldName === 'start_report_path') {
      startReportFileList.value = fileData
    } else if (fieldName === 'completion_report_path') {
      completionReportFileList.value = fileData
    }
    ElMessage.success('上传成功')
  } catch (e) {
    ElMessage.error('上传失败')
    option.onError(e)
  }
}

// Actions
const openFile = (path) => {
  if (!path) return
  window.open(getFileUrl(path), '_blank')
}

const handleEdit = () => {
  // Navigate back to list or open edit dialog (not implemented in this view directly)
  ElMessage.info('请在列表页点击编辑')
}

const openFinanceDialog = (type) => {
  financeDialog.type = type
  financeDialog.visible = true
  financeDialog.isEdit = false
  financeDialog.editingId = null
  
  // Reset form - use Object.assign with empty object to preserve reactivity
  Object.assign(financeForm, {
    contract_id: Number(contractId),
    category: undefined,
    amount: 0,
    expected_date: '',
    description: '',
    file_path: '',
    invoice_number: '',
    tax_rate: '',
    invoice_date: '',
    invoice_type: '',
    receipt_date: '',
    payment_method: '',
    payer_name: '',
    payer_account: '',
    settlement_code: '',
    settlement_amount: 0,
    settlement_date: '',
    completion_date: null,
    warranty_date: null,
    status: '',
    audit_report_path: '',
    start_report_path: '',
    completion_report_path: ''
  })
  
  fileList.value = [] // Reset file list
  
  if (type === 'receivable') {
    financeDialog.title = '新增应收款'
    financeForm.category = 'PROGRESS_PAYMENT'
    financeForm.amount = 0
    financeForm.expected_date = ''
    financeForm.description = ''
    financeForm.file_path = ''
  } else if (type === 'invoice') {
    financeDialog.title = '新增开票记录'
    invoiceFileList.value = [] // Reset invoice file list
    financeForm.invoice_number = ''
    financeForm.amount = 0
    financeForm.tax_rate = '13'
    financeForm.invoice_date = new Date().toISOString().split('T')[0]
    financeForm.invoice_type = '专票'
    financeForm.file_path = ''
  } else if (type === 'receipt') {
    financeDialog.title = '新增回款记录'
    financeForm.amount = 0
    financeForm.receipt_date = new Date().toISOString().split('T')[0]
    financeForm.payment_method = '银行转账'
    financeForm.payer_name = contract.value.party_a_name
    financeForm.file_path = ''
  } else if (type === 'settlement') {
    financeDialog.title = '新增结算记录'
    // Reset settlement report file lists
    auditReportFileList.value = []
    startReportFileList.value = []
    completionReportFileList.value = []
    financeForm.settlement_code = ''
    financeForm.settlement_amount = 0
    financeForm.settlement_date = new Date().toISOString().split('T')[0]
    financeForm.completion_date = null
    financeForm.warranty_date = null
    financeForm.status = '待审核'
    financeForm.description = ''
    financeForm.file_path = ''
    financeForm.audit_report_path = ''
    financeForm.start_report_path = ''
    financeForm.completion_report_path = ''
  }
}

const openEditDialog = (type, row) => {
  financeDialog.type = type
  financeDialog.visible = true
  financeDialog.isEdit = true
  financeDialog.editingId = row.id
  
  // Reset form first to clear all fields, then populate
  Object.assign(financeForm, {
    contract_id: Number(contractId),
    category: undefined,
    amount: 0,
    expected_date: '',
    description: '',
    file_path: '',
    invoice_number: '',
    tax_rate: '',
    invoice_date: '',
    invoice_type: '',
    receipt_date: '',
    payment_method: '',
    payer_name: '',
    payer_account: '',
    settlement_code: '',
    settlement_amount: 0,
    settlement_date: '',
    completion_date: null,
    warranty_date: null,
    status: '',
    audit_report_path: '',
    start_report_path: '',
    completion_report_path: ''
  })
  
  if (type === 'receivable') {
    financeDialog.title = '编辑应收款'
    financeForm.category = row.category
    financeForm.amount = row.amount
    financeForm.expected_date = row.expected_date
    financeForm.description = row.description
    financeForm.file_path = row.file_path || ''
    fileList.value = row.file_path ? [{ name: '已上传文件', url: row.file_path }] : []
  } else if (type === 'invoice') {
    financeDialog.title = '编辑挂账记录'
    financeForm.invoice_number = row.invoice_number
    financeForm.amount = row.amount
    financeForm.tax_rate = row.tax_rate
    financeForm.invoice_date = row.invoice_date
    financeForm.invoice_type = row.invoice_type
    financeForm.description = row.description
    financeForm.file_path = row.file_path || ''
    invoiceFileList.value = row.file_path ? [{ name: '已上传文件', url: row.file_path }] : []
  } else if (type === 'receipt') {
    financeDialog.title = '编辑回款记录'
    financeForm.amount = row.amount
    financeForm.receipt_date = row.receipt_date
    financeForm.payment_method = row.payment_method
    financeForm.payer_name = row.payer_name
    financeForm.file_path = row.file_path || ''
    fileList.value = row.file_path ? [{ name: '已上传文件', url: row.file_path }] : []
  } else if (type === 'settlement') {
    financeDialog.title = '编辑结算记录'
    financeForm.settlement_code = row.settlement_code
    financeForm.settlement_amount = row.settlement_amount
    financeForm.settlement_date = row.settlement_date
    financeForm.completion_date = row.completion_date
    financeForm.warranty_date = row.warranty_date
    financeForm.status = row.status
    financeForm.description = row.description
    financeForm.file_path = row.file_path || ''
    financeForm.audit_report_path = row.audit_report_path || ''
    financeForm.start_report_path = row.start_report_path || ''
    financeForm.completion_report_path = row.completion_report_path || ''
    auditReportFileList.value = row.audit_report_path ? [{ name: '审核报告', url: row.audit_report_path }] : []
    startReportFileList.value = row.start_report_path ? [{ name: '开工报告', url: row.start_report_path }] : []
    completionReportFileList.value = row.completion_report_path ? [{ name: '竣工报告', url: row.completion_report_path }] : []
  }
}

const submitFinance = async () => {
  try {
    console.log('Submitting finance form:', financeForm)
    console.log('Finance type:', financeDialog.type)
    console.log('File path:', financeForm.file_path)
    
    if (financeDialog.type === 'receivable') {
      if (financeDialog.isEdit) {
        await updateReceivable(contractId, financeDialog.editingId, financeForm)
      } else {
        await createReceivable(contractId, financeForm)
      }
      await loadReceivables()
    } else if (financeDialog.type === 'invoice') {
      if (financeDialog.isEdit) {
        await updateInvoice(contractId, financeDialog.editingId, financeForm)
      } else {
        await createInvoice(contractId, financeForm)
      }
      await loadInvoices()
    } else if (financeDialog.type === 'receipt') {
      if (financeDialog.isEdit) {
        await updateReceipt(contractId, financeDialog.editingId, financeForm)
      } else {
        await createReceipt(contractId, financeForm)
      }
      await loadReceipts()
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

const handleDelete = (type, row) => {
  const typeNames = {
    receivable: '应收款',
    invoice: '挂账',
    receipt: '回款',
    settlement: '结算'
  }
  ElMessageBox.confirm(`确定删除该${typeNames[type]}记录吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      if (type === 'receivable') {
        await deleteReceivable(contractId, row.id)
        await loadReceivables()
      } else if (type === 'invoice') {
        await deleteInvoice(contractId, row.id)
        await loadInvoices()
      } else if (type === 'receipt') {
        await deleteReceipt(contractId, row.id)
        await loadReceipts()
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



// Force reload to avoid router freeze
const handleBack = () => {
  location.href = '/contracts/upstream'
}

// Resize handler function (named so we can remove it properly)
const handleResize = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
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
    
    .back-link {
      display: flex;
      align-items: center;
      color: #606266;
      text-decoration: none;
      font-size: 14px;
      cursor: pointer;
      line-height: 1;
      
      &:hover {
        color: var(--color-primary);
      }
      
      .el-icon {
        margin-right: 4px;
      }
    }
    
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
  .percentage-inline {
    font-size: 14px;
    font-weight: normal;
    color: #909399;
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
