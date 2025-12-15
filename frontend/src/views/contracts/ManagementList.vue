<template>
  <div class="app-container">
    <!-- Search Bar -->
    <el-card class="filter-container" shadow="never">
      <el-form :inline="true" :model="queryParams" class="demo-form-inline">
        <el-form-item label="关键词">
          <el-input v-model="queryParams.keyword" placeholder="合同名称/编号/乙方" clearable @keyup.enter="handleQuery" />
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="合同状态" clearable style="width: 120px">
            <el-option label="执行中" value="执行中" />
            <el-option label="进行中" value="进行中" />
            <el-option label="已完工" value="已完工" />
            <el-option label="已结算" value="已结算" />
            <el-option label="质保到期" value="质保到期" />
            <el-option label="合同终止" value="合同终止" />
            <el-option label="合同中止" value="合同中止" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
          <el-button icon="Refresh" @click="resetQuery">重置</el-button>
          <el-button v-if="userStore.canManageManagementContracts" type="success" icon="Plus" @click="handleAdd">新建合同</el-button>
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
        <el-table-column prop="company_category" label="费用归属" width="100" show-overflow-tooltip />
        <el-table-column prop="category" label="合同类别" width="120" show-overflow-tooltip />
        <el-table-column prop="contract_amount" label="合同金额" width="140" align="right">
          <template #default="scope">
            ¥ {{ Number(scope.row.contract_amount).toLocaleString() }}
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
            <el-link 
              v-if="scope.row.contract_file_path" 
              :href="getFileUrl(scope.row.contract_file_path)" 
              target="_blank" 
              type="primary"
            >
              <el-icon><Document /></el-icon>
            </el-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-button v-if="userStore.canManageManagementContracts" link type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button link type="primary" size="small" @click="handleDetail(scope.row)">详情</el-button>
            <el-button v-if="userStore.canManageManagementContracts" link type="danger" size="small" @click="handleDelete(scope.row)">删除</el-button>
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
            <span class="value">{{ item.party_b_name }}</span>
          </div>
          <div class="info-row">
            <span class="label">合同金额:</span>
            <span class="value amount">¥ {{ Number(item.contract_amount).toLocaleString() }}</span>
          </div>
        </div>
        <div class="card-footer">
          <el-button v-if="userStore.canManageManagementContracts" size="small" type="primary" @click="handleEdit(item)">编辑</el-button>
          <el-button size="small" @click="handleDetail(item)">详情</el-button>
          <el-button v-if="userStore.canManageManagementContracts" size="small" type="danger" @click="handleDelete(item)">删除</el-button>
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
                :precision="0"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
          </el-col>
        </el-row>

        <!-- Upstream Contract Selection & Summary Banner -->
        <el-form-item label="费用归属" prop="company_category">
          <el-select v-model="form.company_category" placeholder="请选择费用归属" style="width: 100%" @change="handleCategoryChange">
            <el-option label="公司费用" value="公司费用" />
            <el-option label="项目费用" value="项目费用" />
          </el-select>
        </el-form-item>

        <!-- Upstream Contract Selection & Summary Banner -->
         <el-form-item label="关联上游" prop="upstream_contract_id" v-if="form.company_category === '项目费用'">
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
              :label="item.contract_name + ' (' + item.contract_code + ')'"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <!-- Summary Banner -->
        <div v-if="upstreamSummary && form.company_category === '项目费用'" class="summary-banner">
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
              <el-date-picker 
                v-model="form.sign_date" 
                type="date" 
                placeholder="选择日期" 
                style="width: 100%" 
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="费用分类" prop="category">
          <el-select v-model="form.category" placeholder="请选择费用分类" style="width: 100%">
            <el-option label="办公费" value="办公费" />
            <el-option label="培训费" value="培训费" />
            <el-option label="租赁费" value="租赁费" />
            <el-option label="资质费" value="资质费" />
            <el-option label="咨询费" value="咨询费" />
            <el-option label="其他费用" value="其他费用" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="合同名称" prop="contract_name">
          <el-input v-model="form.contract_name" placeholder="请输入合同名称" />
        </el-form-item>
        
        <el-form-item label="甲方单位" prop="party_a_name">
          <el-input v-model="form.party_a_name" placeholder="请输入甲方名称" />
        </el-form-item>

        <el-form-item label="乙方单位" prop="party_b_name">
          <SmartAutocomplete v-model="form.party_b_name" placeholder="输入乙方名称，支持自动补全" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="联系人" prop="party_b_contact">
              <el-input v-model="form.party_b_contact" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话" prop="party_b_phone">
              <el-input v-model="form.party_b_phone" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="合同金额" prop="contract_amount">
          <el-input-number 
            v-model="form.contract_amount" 
            :precision="2" 
            :step="1000" 
            :min="0" 
            :controls="false"
            style="width: 100%" 
          />
        </el-form-item>


        


        <el-form-item label="合同文件" prop="contract_file_path">
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
          <el-input v-model="form.notes" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialog.visible = false">取 消</el-button>
          <el-button type="primary" @click="submitForm">确 定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getContracts, createContract, updateContract, deleteContract, exportContracts } from '@/api/contractManagement'
import { getContracts as getUpstreamContracts, getContractSummary } from '@/api/contractUpstream'
import { uploadFile } from '@/api/common'
import { getFileUrl, formatMoney, getStatusType } from '@/utils/common'
import { downloadExcel, generateFilename } from '@/utils/download'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Download, Document, Connection } from '@element-plus/icons-vue'
import SmartAutocomplete from '@/components/SmartAutocomplete.vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()
const loading = ref(false)
const total = ref(0)
const contractList = ref([])
const isMobile = ref(false)
const fileList = ref([])
const originalId = ref(null)

// Upstream Search
const upstreamLoading = ref(false)
const upstreamOptions = ref([])
const upstreamSummary = ref(null)

const queryParams = reactive({
  page: 1,
  page_size: 10,
  keyword: '',
  status: ''
})

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
  party_a_name: '重庆蓝海电气工程有限公司',
  party_b_name: '',
  party_b_contact: '',
  party_b_phone: '',
  contract_amount: 0,
  sign_date: '',
  start_date: null,
  end_date: null,
  category: '',
  company_category: '公司费用',
  contract_file_path: '',
  notes: '',
  status: '进行中'
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
  party_a_name: [{ required: true, message: '请输入甲方名称', trigger: 'blur' }],
  party_b_name: [{ required: true, message: '请输入乙方名称', trigger: 'blur' }],
  contract_amount: [{ required: true, message: '请输入合同金额', trigger: 'blur' }]
}

// Check Is Mobile
const checkIsMobile = () => {
  isMobile.value = window.innerWidth < 768
}
const handleResize = () => checkIsMobile()

const getList = async () => {
  loading.value = true
  try {
    const res = await getContracts(queryParams)
    contractList.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

const handleQuery = () => {
  queryParams.page = 1
  getList()
}

const resetQuery = () => {
  queryParams.keyword = ''
  queryParams.status = ''
  handleQuery()
}

// Summary row calculation
const getSummaries = (param) => {
  const { columns, data } = param
  const sums = []
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '金额合计'
      return
    }
    
    if (column.property === 'contract_amount') {
      const values = data.map(item => Number(item[column.property]))
      if (!values.every(value => Number.isNaN(value))) {
        const sum = values.reduce((prev, curr) => {
          const value = Number(curr)
          if (!Number.isNaN(value)) {
            return prev + curr
          } else {
            return prev
          }
        }, 0)
        sums[index] = '¥ ' + formatMoney(sum)
      } else {
        sums[index] = '0.00'
      }
    } else {
      sums[index] = ''
    }
  })
  return sums
}

const footerCellStyle = () => {
  return {
    backgroundColor: '#FFFF00',
    color: '#000000',
    fontWeight: 'bold',
    fontSize: '16px'
  }
}

// Logic for Upstream Search
const searchUpstream = async (query) => {
  if (query) {
    upstreamLoading.value = true
    try {
      const res = await getUpstreamContracts({ keyword: query, page_size: 20 })
      upstreamOptions.value = res.items
    } finally {
      upstreamLoading.value = false
    }
  } else {
    upstreamOptions.value = []
  }
}

const handleUpstreamSelect = async (val) => {
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

const handleCategoryChange = (val) => {
  if (val === '公司费用') {
    form.upstream_contract_id = undefined
    upstreamSummary.value = null
  }
}

const handleUploadRequest = async (option) => {
  try {
    const res = await uploadFile(option.file)
    form.contract_file_path = res.path
    fileList.value = [{ name: option.file.name, url: res.path }]
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
  form.party_a_name = '重庆蓝海电气工程有限公司'
  form.party_b_name = ''
  form.party_b_contact = ''
  form.party_b_phone = ''
  form.contract_amount = 0
  form.sign_date = new Date().toISOString().split('T')[0]
  form.start_date = null
  form.end_date = null
  form.category = ''
  form.company_category = '公司费用'
  form.notes = ''
  form.status = '执行中'
  form.contract_file_path = ''
  
  fileList.value = []
  upstreamOptions.value = []
  upstreamSummary.value = null
}

const handleAdd = () => {
  resetForm()
  dialog.title = '新建管理合同'
  dialog.isEdit = false
  dialog.visible = true
}

const handleExport = async () => {
  try {
    ElMessage.info('正在导出...')
    const res = await exportContracts(queryParams)
    const filename = generateFilename('管理合同导出', 'xlsx')
    downloadExcel(res, filename)
    ElMessage.success('导出成功')
  } catch (e) {
    console.error('Export Error:', e)
    ElMessage.error('导出失败: ' + (e.message || e))
  }
}

const handleEdit = async (row) => {
  resetForm()
  Object.assign(form, row)
  originalId.value = row.id
  
  if (form.contract_file_path) {
    fileList.value = [{ name: '已上传文件', url: form.contract_file_path }]
  }

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
      if (dialog.isEdit) {
        // Use originalId for the URL
        await updateContract(originalId.value, form)
        ElMessage.success('更新成功')
      } else {
        await createContract(form)
        ElMessage.success('创建成功')
      }
      dialog.visible = false
      getList()
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确认删除合同 "${row.contract_name}" 吗?`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await deleteContract(row.id)
    ElMessage.success('删除成功')
    getList()
  })
}

const handleDetail = (row) => {
  router.push({ name: 'ManagementDetail', params: { id: row.id }})
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
