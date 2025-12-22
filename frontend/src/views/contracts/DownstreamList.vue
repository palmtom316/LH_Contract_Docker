<template>
  <div class="app-container">
    <!-- Search Bar -->
    <el-card class="filter-container" shadow="never">
      <el-form :inline="true" :model="queryParams" class="demo-form-inline">
        <el-form-item label="关键词">
          <el-input v-model="queryParams.keyword" placeholder="合同序号/编号/名称/乙方" clearable @keyup.enter="handleSearch" />
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="合同状态" clearable style="width: 120px">
            <el-option label="执行中" value="执行中" />
            <el-option label="已完工" value="已完工" />
            <el-option label="已结算" value="已结算" />
            <el-option label="质保到期" value="质保到期" />
            <el-option label="合同终止" value="合同终止" />
            <el-option label="合同中止" value="合同中止" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="handleSearch">搜索</el-button>
          <el-button icon="Refresh" @click="resetQuery">重置</el-button>
          <el-button v-if="userStore.canManageDownstreamContracts" type="success" icon="Plus" @click="handleAdd">新建合同</el-button>
          <el-button type="warning" icon="Download" @click="handleExport">导出Excel</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Table View (PC) -->
    <el-card v-if="!isMobile" class="table-container" shadow="always">
      <el-table 
        v-loading="loading" 
        :data="contractList" 
        style="width: 100%" 
        border
        highlight-current-row
        show-summary
        :summary-method="getSummaries"
        class="custom-footer-table"
        :footer-cell-style="footerCellStyle"
      >
        <el-table-column prop="serial_number" label="合同序号" width="100" fixed />
        <el-table-column prop="contract_code" label="合同编号" width="150" fixed />
        <el-table-column prop="contract_name" label="合同名称" min-width="220">
          <template #default="scope">
            <div :style="{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.5', maxHeight: '4.5em', overflow: 'hidden' }">{{ scope.row.contract_name }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="party_b_name" label="乙方(供应商)" min-width="180">
          <template #default="scope">
            <div :style="{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.5', maxHeight: '4.5em', overflow: 'hidden' }">{{ scope.row.party_b_name }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="合同类别" width="120" show-overflow-tooltip />
        <el-table-column prop="pricing_mode" label="计价模式" width="120" show-overflow-tooltip />
        <el-table-column prop="contract_amount" label="合同金额" width="140" align="right">
          <template #default="scope">
            ¥ {{ Number(scope.row.contract_amount).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="total_payable" label="应付款" width="120" align="right">
          <template #default="scope">
            <span v-if="scope.row.total_payable">¥ {{ Number(scope.row.total_payable).toLocaleString() }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_invoiced" label="挂账" width="120" align="right">
          <template #default="scope">
            <span v-if="scope.row.total_invoiced">¥ {{ Number(scope.row.total_invoiced).toLocaleString() }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_paid" label="已付款" width="120" align="right">
          <template #default="scope">
            <span v-if="scope.row.total_paid">¥ {{ Number(scope.row.total_paid).toLocaleString() }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_settlement" label="结算" width="120" align="right">
          <template #default="scope">
            <span v-if="scope.row.total_settlement">¥ {{ Number(scope.row.total_settlement).toLocaleString() }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="sign_date" label="签订日期" width="120" sortable />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="合同文件" width="100" align="center">
          <template #default="scope">
            <el-button 
              v-if="scope.row.contract_file_path" 
              link 
              type="primary" 
              size="small"
              icon="Document"
              @click="openPdfInNewTab(scope.row.contract_file_path)"
            >查看</el-button>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="scope">
            <el-button v-if="userStore.canManageDownstreamContracts" link type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button link type="primary" size="small" @click="handleDetail(scope.row)">详情</el-button>
            <el-button v-if="userStore.canManageDownstreamContracts" link type="danger" size="small" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="getList"
          @current-change="getList"
        />
      </div>
    </el-card>

    <!-- Card View (Mobile) -->
    <div v-else class="card-list">
      <el-card v-for="item in contractList" :key="item.id" class="contract-card" shadow="hover">
        <div class="card-header">
          <div class="title">{{ item.contract_name }}</div>
          <el-tag :type="getStatusType(item.status)" size="small">{{ item.status }}</el-tag>
        </div>
        <div class="card-body">
          <div class="info-row">
            <span class="label">合同编号:</span>
            <span class="value">{{ item.contract_code }}</span>
          </div>
          <div class="info-row">
            <span class="label">乙方:</span>
            <span class="value">{{ item.supplier_name }}</span>
          </div>
          <div class="info-row">
            <span class="label">合同金额:</span>
            <span class="value amount">¥ {{ Number(item.contract_amount).toLocaleString() }}</span>
          </div>
        </div>
        <div class="card-footer">
          <el-button v-if="userStore.canManageDownstreamContracts" size="small" type="primary" @click="handleEdit(item)">编辑</el-button>
          <el-button size="small" @click="handleDetail(item)">详情</el-button>
          <el-button v-if="userStore.canManageDownstreamContracts" size="small" type="danger" @click="handleDelete(item)">删除</el-button>
        </div>
      </el-card>
    </div>

    <!-- Dialog -->
    <el-dialog
      :title="dialog.title"
      v-model="dialog.visible"
      width="600px"
      :fullscreen="isMobile"
      append-to-body
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        
        
        <!-- Contract Serial Number (Editable) -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="合同序号" prop="serial_number">
              <el-input-number 
                v-model="form.serial_number" 
                :disabled="false"
                placeholder="请输入合同序号（正整数）" 
                :controls="false"
                :min="1"
                :step="1"
                :precision="0"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
             <!-- Placeholder to keep grid balanced if needed, or move another field here -->
          </el-col>
        </el-row>

        <!-- Upstream Contract Selection & Summary Banner -->
         <el-form-item label="关联上游" prop="upstream_contract_id">
          <el-select
            v-model="form.upstream_contract_id"
            filterable
            remote
            reserve-keyword
            placeholder="搜索关联的上游合同(序号/编号/名称)"
            :remote-method="searchUpstream"
            :loading="upstreamLoading"
            style="width: 100%"
            @change="handleUpstreamSelect"
            clearable
          >
            <el-option
              v-for="item in upstreamOptions"
              :key="item.id"
              :label="'[' + (item.serial_number || '-') + '] ' + item.contract_name"
              :value="item.id"
            >
              <span>[{{ item.serial_number || '-' }}] {{ item.contract_name }}</span>
              <span style="float: right; color: #8492a6; font-size: 12px">{{ item.contract_code }}</span>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- Summary Banner -->
        <div v-if="upstreamSummary" class="summary-banner">
          <div class="banner-title"><el-icon><Connection /></el-icon> 已关联上游合同信息</div>
          <div class="banner-grid">
            <div class="item">
              <span class="label">合同编号:</span>
              <span class="value">{{ upstreamSummary.contract_code }}</span>
            </div>
            <div class="item">
              <span class="label">甲方:</span>
              <span class="value">{{ upstreamSummary.party_a_name }}</span>
            </div>
            <div class="item">
              <span class="label">总金额:</span>
              <span class="value">¥ {{ Number(upstreamSummary.contract_amount).toLocaleString() }}</span>
            </div>
          </div>
        </div>

        <el-row :gutter="20">
          <el-col :span="12">
             <el-form-item label="合同编号" prop="contract_code">
              <el-input v-model="form.contract_code" placeholder="请输入编号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="签订日期" prop="sign_date">
              <SmartDateInput 
                v-model="form.sign_date" 
                style="width: 100%" 
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="合同类别" prop="category">
              <DictSelect v-model="form.category" category="downstream_contract_category" placeholder="请选择合同类别" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计价模式" prop="pricing_mode">
              <DictSelect v-model="form.pricing_mode" category="downstream_pricing_mode" placeholder="请选择计价模式" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="合同名称" prop="contract_name">
          <el-input v-model="form.contract_name" placeholder="请输入合同名称" />
        </el-form-item>

        <el-form-item label="甲方名称" prop="party_a_name">
          <SmartAutocomplete v-model="form.party_a_name" placeholder="一般为本公司名称" />
        </el-form-item>

        <el-form-item label="乙方名称" prop="party_b_name">
          <SmartAutocomplete v-model="form.party_b_name" placeholder="输入乙方名称，支持自动补全" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="乙方联系人" prop="party_b_contact">
              <el-input v-model="form.party_b_contact" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="乙方电话" prop="party_b_phone">
              <el-input v-model="form.party_b_phone" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="合同金额" prop="contract_amount">
          <FormulaInput 
            v-model="form.contract_amount" 
            placeholder="支持公式计算"
            show-icon
            style="width: 100%" 
          />
        </el-form-item>

        <el-form-item label="合同文件">
          <el-upload
            class="upload-demo"
            action="#"
            :http-request="handleUpload"
            :file-list="fileList"
            :limit="1"
            accept=".pdf"
          >
            <el-button type="primary" icon="Document">点击上传PDF</el-button>
            <template #tip>
              <div class="el-upload__tip">只能上传 PDF 文件</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialog.visible = false">取 消</el-button>
          <el-button type="primary" :loading="loading" @click="submitForm">确 定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getContracts, createContract, updateContract, deleteContract, exportContracts } from '@/api/contractDownstream'
import { getContracts as getUpstreamContracts, getContractSummary } from '@/api/contractUpstream'
import { uploadFile } from '@/api/common'
import { useContractList, useTableSummary, useMobileDetection } from '@/composables/useContractList'
import { getFileUrl } from '@/utils/common'

// Open PDF in new tab
const openPdfInNewTab = (path) => {
  if (!path) return
  window.open(getFileUrl(path), '_blank')
}
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Refresh, Search, Plus, Download } from '@element-plus/icons-vue'
import SmartAutocomplete from '@/components/SmartAutocomplete.vue'
import DictSelect from '@/components/DictSelect.vue'
import SmartDateInput from '@/components/SmartDateInput.vue'
import FormulaInput from '@/components/FormulaInput.vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()
const { getSummaries, footerCellStyle } = useTableSummary()
const { isMobile, checkIsMobile } = useMobileDetection()

const {
  loading,
  list: contractList,
  total,
  queryParams,
  getList,
  handleQuery: handleSearch,
  resetQuery,
  handleDelete,
  handleExport,
  formatMoney,
  getStatusType
} = useContractList({
  api: { getContracts, deleteContract, exportContracts },
  contractType: '下游合同',
  exportPrefix: '下游合同列表'
})

const fileList = ref([])
const originalId = ref(null)

// Upstream Search
const upstreamLoading = ref(false)
const upstreamOptions = ref([])
const upstreamSummary = ref(null)

const dialog = reactive({
  title: '',
  visible: false,
  isEdit: false
})

const formRef = ref(null)
const form = reactive({
  serial_number: undefined,
  id: undefined,
  upstream_contract_id: undefined,
  contract_code: '',
  contract_name: '',
  party_a_name: '蓝海建设集团',
  party_b_name: '',
  party_b_contact: '',
  party_b_phone: '',
  contract_amount: 0,
  sign_date: '',
  category: '其他合同',
  pricing_mode: '',
  contract_file_path: '',
  notes: '',
  status: '执行中'
})

const rules = {
  serial_number: [
    { required: true, message: '请输入合同序号', trigger: 'blur' },
    { type: 'number', message: '合同序号必须是数字', trigger: 'blur' },
    { validator: (rule, value, callback) => {
        if (value && value <= 0) {
          callback(new Error('合同序号必须大于0'))
        } else {
          callback()
        }
      }, trigger: 'blur' }
  ],
  contract_code: [{ required: true, message: '请输入合同编号', trigger: 'blur' }],
  contract_name: [{ required: true, message: '请输入合同名称', trigger: 'blur' }],
  party_b_name: [{ required: true, message: '请输入乙方名称', trigger: 'blur' }],
  contract_amount: [{ required: true, message: '请输入合同金额', trigger: 'blur' }],
  category: [{ required: true, message: '请选择合同类别', trigger: 'change' }]
}

// Check Is Mobile
const handleResize = () => checkIsMobile()

// Logic for Upstream Search
const searchUpstream = async (query) => {
  if (query) {
    upstreamLoading.value = true
    try {
      const res = await getUpstreamContracts({ keyword: query, page_size: 20 })
      upstreamOptions.value = res.items
    } catch (e) {
      console.error(e)
    }
    upstreamLoading.value = false
  } else {
    upstreamOptions.value = []
  }
}

const handleUpstreamSelect = async (val) => {
  form.upstream_contract_id = val
  if (val) {
    try {
      const summary = await getContractSummary(val)
      upstreamSummary.value = summary
    } catch (e) {
      upstreamSummary.value = null
    }
  } else {
    upstreamSummary.value = null
  }
}

// getFileUrl imported from @/utils/common

// Upload
const handleUpload = async (option) => {
  try {
    const result = await uploadFile(option.file)
    form.contract_file_path = result.path
    fileList.value = [{ name: option.file.name, url: result.path }]
    option.onSuccess(result)
    ElMessage.success('上传成功')
  } catch (e) {
    ElMessage.error('上传失败')
    option.onError(e)
  }
}

// Form handling
const resetForm = () => {
  form.serial_number = undefined
  form.id = undefined
  form.upstream_contract_id = undefined
  form.contract_code = ''
  form.contract_name = ''
  form.party_a_name = '蓝海建设集团'
  form.party_b_name = ''
  form.party_b_contact = ''
  form.party_b_phone = ''
  form.contract_amount = 0
  form.sign_date = new Date().toISOString().split('T')[0]
  form.category = '其他合同'
  form.pricing_mode = ''
  form.contract_file_path = ''
  form.notes = ''
  form.status = '执行中'
  
  fileList.value = []
  upstreamOptions.value = []
  upstreamSummary.value = null
}

const handleAdd = () => {
  resetForm()
  dialog.title = '新建下游合同'
  dialog.isEdit = false
  dialog.visible = true
}


const handleEdit = async (row) => {
  resetForm()
  Object.assign(form, row)
  originalId.value = row.id
  
  if (row.contract_file_path) {
    fileList.value = [{ name: '合同文件', url: row.contract_file_path }]
  } else {
    fileList.value = []
  }

  // Create mock option so the select displays the current stored ID correctly initially
  if (form.upstream_contract_id) {
    handleUpstreamSelect(form.upstream_contract_id)
  }
  
  dialog.title = '编辑合同'
  dialog.isEdit = true
  dialog.visible = true
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        // Clean data
        const submitData = { ...form }
        if (!submitData.start_date) submitData.start_date = null
        if (!submitData.end_date) submitData.end_date = null
        if (!submitData.category) submitData.category = '其他合同'
        if (!submitData.pricing_mode) submitData.pricing_mode = null
        
        if (dialog.isEdit) {
          // Use originalId for the URL to handle ID updates correctly
          await updateContract(originalId.value, submitData)
          ElMessage.success('更新成功')
        } else {
          await createContract(submitData)
          ElMessage.success('创建成功')
        }
        dialog.visible = false
        getList()
      } catch (error) {
        // Error is handled by request interceptor usually, but safe to log
        console.error(error)
      }
    }
  })
}


const handleDetail = (row) => {
  router.push(`/contracts/downstream/${row.id}`)
}

onMounted(() => {
  checkIsMobile()
  window.addEventListener('resize', handleResize)
  getList()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})


</script>

<style scoped lang="scss">
.filter-container {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* Summary Banner */
.summary-banner {
  background-color: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 4px;
  padding: 10px 15px;
  margin-bottom: 20px;
  
  .banner-title {
    font-weight: bold;
    color: #52c41a;
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    
    .el-icon { margin-right: 5px; }
  }
  
  .banner-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    
    .item {
      font-size: 13px;
      .label { color: #8c8c8c; margin-right: 5px; }
      .value { color: #262626; font-weight: 500; }
    }
  }
}

/* Mobile Card View */
.card-list {
  .contract-card {
    margin-bottom: 15px;
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 12px;
      border-bottom: 1px solid #f0f0f0;
      
      .title {
        font-weight: bold;
        font-size: 15px;
        color: var(--color-text-main);
        flex: 1;
        margin-right: 10px;
      }
    }
    
    .card-body {
      .info-row {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        font-size: 14px;
        
        .label {
          color: var(--color-text-secondary);
          min-width: 80px;
        }
        
        .value {
          color: var(--color-text-main);
          font-weight: 500;
          text-align: right;
          flex: 1;
          
          &.amount {
            color: var(--color-primary);
            font-weight: bold;
          }
        }
      }
    }
    
    .card-footer {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid #f0f0f0;
      display: flex;
      justify-content: flex-end;
      gap: 8px;
    }
  }
}
</style>

<style>
/* Global override for table footer - Bold black text with yellow background */
.custom-footer-table .el-table__footer-wrapper tbody td,
.custom-footer-table .el-table__fixed-footer-wrapper tbody td,
.custom-footer-table .el-table__footer-wrapper tbody tr,
.custom-footer-table .el-table__fixed-footer-wrapper tbody tr {
  background-color: #FFFF00 !important; /* Bright Yellow */
  color: #000000 !important; /* Black */
  font-weight: bold !important;
  font-size: 16px !important;
  --el-table-row-hover-bg-color: #FFFF00 !important;
}
.custom-footer-table .el-table__footer-wrapper tbody td .cell,
.custom-footer-table .el-table__fixed-footer-wrapper tbody td .cell {
  background-color: #FFFF00 !important;
  color: #000000 !important; /* Black */
  font-weight: bold !important;
}
</style>
