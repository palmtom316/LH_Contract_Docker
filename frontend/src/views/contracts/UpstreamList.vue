<template>
  <div class="app-container">
    <!-- Search Bar -->
    <el-card class="filter-container" shadow="never">
      <el-form :inline="true" :model="queryParams" class="demo-form-inline">
        <el-form-item label="关键词">
          <el-input v-model="queryParams.keyword" placeholder="合同名称/编号/甲方" clearable @keyup.enter="handleQuery" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="合同状态" clearable style="width: 120px">
            <el-option label="进行中" value="进行中" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已终止" value="已终止" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
          <el-button icon="Refresh" @click="resetQuery">重置</el-button>
          <el-button type="warning" icon="Download" @click="handleExport">导出Excel</el-button>
          <el-dropdown @command="handleImportCommand" style="margin-left: 10px;">
            <el-button type="info" icon="Upload">
              导入Excel<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="template">下载导入模板</el-dropdown-item>
                <el-dropdown-item command="import">选择Excel文件导入</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button type="success" icon="Plus" @click="handleAdd" style="margin-left: 10px;">新建合同</el-button>
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
      >
        <el-table-column prop="id" label="合同序号" width="100" align="center" fixed="left" />
        <el-table-column prop="contract_name" label="合同名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="party_a_name" label="甲方单位" min-width="160" show-overflow-tooltip />
        <el-table-column prop="party_b_name" label="乙方单位" min-width="160" show-overflow-tooltip />
        <el-table-column prop="contract_amount" label="签约金额" width="140" align="right">
          <template #default="scope">
            ¥ {{ formatMoney(scope.row.contract_amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="sign_date" label="签约时间" width="120" align="center" />
        <el-table-column prop="company_category" label="公司合同分类" width="130" align="center" show-overflow-tooltip />
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
            <el-button link type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button link type="primary" size="small" @click="handleDetail(scope.row)">详情</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(scope.row)">删除</el-button>
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
            <span class="label">甲方:</span>
            <span class="value">{{ item.party_a_name }}</span>
          </div>
          <div class="info-row">
            <span class="label">合同金额:</span>
            <span class="value amount">¥ {{ formatMoney(item.contract_amount) }}</span>
          </div>
          <div class="info-row">
            <span class="label">签订日期:</span>
            <span class="value">{{ item.sign_date }}</span>
          </div>
        </div>
        <div class="card-footer">
           <el-button 
            v-if="item.contract_file_path" 
            size="small" 
            type="warning" 
            icon="Document" 
            circle
            @click="handlePreview(item.contract_file_path)"
          />
          <el-button size="small" type="primary" @click="handleEdit(item)">编辑</el-button>
          <el-button size="small" @click="handleDetail(item)">详情</el-button>
          <el-button size="small" type="danger" @click="handleDelete(item)">删除</el-button>
        </div>
      </el-card>

      <!-- Mobile Pagination -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :page-sizes="[10, 20, 50]"
          layout="total, prev, pager, next"
          :total="total"
          small
          @size-change="getList"
          @current-change="getList"
        />
      </div>
    </div>

    <!-- Edit/Create Dialog -->
    <el-dialog
      :title="dialog.title"
      v-model="dialog.visible"
      width="850px"
      :fullscreen="isMobile"
      append-to-body
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <!-- Contract Serial Number (Read-only) -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="合同序号">
              <el-input 
                :value="dialog.isEdit ? form.id : '自动生成'" 
                disabled 
                placeholder="系统自动生成"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="签约日期" prop="sign_date">
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
        
        <el-row :gutter="20">
          <el-col :span="12">
             <el-form-item label="合同编号" prop="contract_code">
              <el-input v-model="form.contract_code" placeholder="请输入编号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="合同状态" prop="status">
              <el-select v-model="form.status" placeholder="请选择状态" style="width: 100%">
                <el-option label="进行中" value="进行中" />
                <el-option label="已完成" value="已完成" />
                <el-option label="已终止" value="已终止" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="合同名称" prop="contract_name">
              <el-input v-model="form.contract_name" placeholder="请输入合同名称" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="甲方单位" prop="party_a_name">
              <SmartAutocomplete v-model="form.party_a_name" placeholder="输入甲方名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="乙方单位" prop="party_b_name">
              <el-input v-model="form.party_b_name" placeholder="请输入乙方名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="签约金额" prop="contract_amount">
              <el-input-number 
                v-model="form.contract_amount" 
                class="amount-input-right"
                :precision="2" 
                :controls="false"
                :min="0" 
                style="width: 100%" 
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计价模式" prop="pricing_mode">
              <el-select v-model="form.pricing_mode" placeholder="请选择" style="width: 100%">
                <el-option label="总价包干" value="总价包干" />
                <el-option label="单价包干" value="单价包干" />
                <el-option label="工日单价" value="工日单价" />
                <el-option label="费率下浮" value="费率下浮" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="合同类别" prop="category">
              <el-select v-model="form.category" placeholder="请选择" style="width: 100%">
                <el-option label="总包合同" value="总包合同" />
                <el-option label="专业分包" value="专业分包" />
                <el-option label="劳务分包" value="劳务分包" />
                <el-option label="技术服务" value="技术服务" />
                <el-option label="运营维护" value="运营维护" />
                <el-option label="物资采购" value="物资采购" />
                <el-option label="其他合同" value="其他合同" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="公司合同分类" prop="company_category">
              <el-select v-model="form.company_category" placeholder="请选择" style="width: 100%">
                <el-option label="市区配网" value="市区配网" />
                <el-option label="市北配网" value="市北配网" />
                <el-option label="用户工程" value="用户工程" />
                <el-option label="维护工程" value="维护工程" />
                <el-option label="变电工程" value="变电工程" />
                <el-option label="营销工程" value="营销工程" />
                <el-option label="北源工程" value="北源工程" />
                <el-option label="安驰工程" value="安驰工程" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="管理模式" prop="management_mode">
              <el-select v-model="form.management_mode" placeholder="请选择" style="width: 100%">
                <el-option label="自营" value="自营" />
                <el-option label="合作" value="合作" />
                <el-option label="挂靠" value="挂靠" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
             <el-form-item label="负责人" prop="responsible_person">
              <el-input v-model="form.responsible_person" placeholder="请输入负责人姓名" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- File Upload -->
        <el-form-item label="合同文件">
          <el-upload
            class="upload-demo"
            action="#"
            :http-request="handleUploadRequest"
            :limit="1"
            :on-remove="handleRemoveFile"
            :file-list="fileList"
            accept=".pdf"
          >
            <template #trigger>
              <el-button type="primary">选择文件 (PDF)</el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                支持PDF文件
              </div>
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

    <!-- PDF Viewer Dialog -->
    <el-dialog 
      v-model="pdfDialog.visible" 
      title="合同附件预览" 
      fullscreen 
      destroy-on-close
      append-to-body
    >
      <PdfViewer :source="pdfDialog.url" />
    </el-dialog>

    <!-- Hidden file input for import -->
    <input 
      ref="importFileInput"
      type="file" 
      accept=".xlsx,.xls" 
      style="display: none;"
      @change="handleImportFileChange"
    />

    <!-- Import Result Dialog -->
    <el-dialog
      v-model="importResult.visible"
      title="导入结果"
      width="500px"
      append-to-body
    >
      <div class="import-result">
        <el-result v-if="importResult.success_count > 0 && importResult.error_count === 0" icon="success" title="导入成功">
          <template #sub-title>
            <p>成功导入 {{ importResult.success_count }} 条合同记录</p>
          </template>
        </el-result>
        <el-result v-else-if="importResult.success_count === 0 && importResult.error_count > 0" icon="error" title="导入失败">
          <template #sub-title>
            <p>全部 {{ importResult.error_count }} 条记录导入失败</p>
          </template>
        </el-result>
        <el-result v-else icon="warning" title="部分导入成功">
          <template #sub-title>
            <p>成功: {{ importResult.success_count }} 条，失败: {{ importResult.error_count }} 条</p>
          </template>
        </el-result>
        
        <div v-if="importResult.errors && importResult.errors.length > 0" class="error-list">
          <el-divider>错误详情</el-divider>
          <el-table :data="importResult.errors" max-height="200" size="small">
            <el-table-column prop="row" label="行号" width="80" />
            <el-table-column prop="error" label="错误信息" show-overflow-tooltip />
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="importResult.visible = false">确 定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { getContracts, createContract, updateContract, deleteContract, exportContracts, downloadImportTemplate, importContracts } from '@/api/contractUpstream'
import { uploadFile } from '@/api/common'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import SmartAutocomplete from '@/components/SmartAutocomplete.vue'
import PdfViewer from '@/components/PdfViewer.vue'

const loading = ref(false)
const total = ref(0)
const contractList = ref([])
const isMobile = ref(false)

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

const pdfDialog = reactive({
  visible: false,
  url: ''
})

// Import functionality
const importResult = reactive({
  visible: false,
  success_count: 0,
  error_count: 0,
  errors: []
})
const importFileInput = ref(null)
const importLoading = ref(false)

const formRef = ref(null)
const fileList = ref([])

const form = reactive({
  id: undefined,
  contract_code: '',
  contract_name: '',
  party_a_name: '',
  party_b_name: '',
  party_a_contact: '',
  party_a_phone: '',
  contract_amount: 0,
  sign_date: '',
  start_date: '',
  end_date: '',
  category: '',
  company_category: '', // 公司合同分类
  pricing_mode: '',     // 计价模式
  management_mode: '',  // 管理模式
  responsible_person: '', // 负责人
  notes: '',
  status: '进行中',
  contract_file_path: ''
})

const rules = {
  contract_code: [{ required: true, message: '请输入合同编号', trigger: 'blur' }],
  contract_name: [{ required: true, message: '请输入合同名称', trigger: 'blur' }],
  party_a_name: [{ required: true, message: '请输入甲方名称', trigger: 'blur' }],
  party_b_name: [{ required: true, message: '请输入乙方名称', trigger: 'blur' }],
  contract_amount: [{ required: true, message: '请输入合同金额', trigger: 'blur' }]
}

// Check if mobile
const checkIsMobile = () => {
  isMobile.value = window.innerWidth < 768
}

const handleResize = () => {
  checkIsMobile()
}

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

const getStatusType = (status) => {
  const map = {
    '进行中': 'primary',
    '已完成': 'success',
    '已终止': 'info',
    '待审核': 'warning'
  }
  return map[status] || ''
}

const formatMoney = (value) => {
  if (value === undefined || value === null) return '0.00'
  return Number(value).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// File Upload Logic
const handleUploadRequest = async (option) => {
  try {
    const res = await uploadFile(option.file)
    form.contract_file_path = res.path
    // Update file list to display the name
    fileList.value = [{
      name: option.file.name,
      url: res.path
    }]
    ElMessage.success('上传成功')
  } catch (e) {
    ElMessage.error('上传失败')
    option.onError(e)
  }
}

const handleRemoveFile = () => {
  form.contract_file_path = ''
  fileList.value = []
}

// PDF Preview
const handlePreview = (path) => {
  if (!path) return
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
  pdfDialog.url = path 
  pdfDialog.visible = true
}

// Open PDF in new tab
const openPdfInNewTab = (path) => {
  if (!path) return
  // PDF files are served from the backend server
  // In development, backend is at localhost:8000
  // The path from API is like /uploads/contracts/xxx.pdf
  const backendUrl = 'http://localhost:8000'
  const pdfUrl = path.startsWith('http') ? path : `${backendUrl}${path}`
  window.open(pdfUrl, '_blank')
}

// Form handling
const resetForm = () => {
  form.id = undefined
  form.contract_code = ''
  form.contract_name = ''
  form.party_a_name = ''
  form.party_b_name = ''
  form.party_a_contact = ''
  form.party_a_phone = ''
  form.contract_amount = 0
  form.sign_date = new Date().toISOString().split('T')[0]
  form.start_date = ''
  form.end_date = ''
  form.category = ''
  form.company_category = ''
  form.pricing_mode = ''
  form.management_mode = ''
  form.responsible_person = ''
  form.notes = ''
  form.status = '进行中'
  form.contract_file_path = ''
  fileList.value = []
}

const handleAdd = () => {
  resetForm()
  dialog.title = '新建上游合同'
  dialog.isEdit = false
  dialog.visible = true
}

const handleEdit = (row) => {
  resetForm()
  Object.assign(form, row)
  
  if (row.contract_file_path) {
    // Use contract name as display name instead of UUID filename
    const displayName = row.contract_name ? `${row.contract_name}.pdf` : '合同文件.pdf'
    fileList.value = [{
      name: displayName,
      url: row.contract_file_path
    }]
  }
  
  dialog.title = '编辑合同'
  dialog.isEdit = true
  dialog.visible = true
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      // Sanitize data: convert empty strings to null for optional API fields
      const dataToSubmit = { ...form }
      if (!dataToSubmit.start_date) dataToSubmit.start_date = null
      if (!dataToSubmit.end_date) dataToSubmit.end_date = null
      if (!dataToSubmit.category) dataToSubmit.category = null
      if (!dataToSubmit.company_category) dataToSubmit.company_category = null
      if (!dataToSubmit.pricing_mode) dataToSubmit.pricing_mode = null
      if (!dataToSubmit.management_mode) dataToSubmit.management_mode = null
      if (!dataToSubmit.responsible_person) dataToSubmit.responsible_person = null
      if (!dataToSubmit.notes) dataToSubmit.notes = null
      if (!dataToSubmit.party_a_contact) dataToSubmit.party_a_contact = null
      if (!dataToSubmit.party_a_phone) dataToSubmit.party_a_phone = null
      
      try {
        if (dialog.isEdit) {
            await updateContract(form.id, dataToSubmit)
            ElMessage.success('更新成功')
        } else {
            await createContract(dataToSubmit)
            ElMessage.success('创建成功')
        }
        dialog.visible = false
        getList()
      } catch (error) {
        console.error('Submit error:', error)
      }
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

const router = useRouter() // Ensure router is imported or available

const handleDetail = (row) => {
  router.push({ name: 'UpstreamDetail', params: { id: row.id } })
}

const handleExport = async () => {
  try {
    const res = await exportContracts(queryParams)
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    link.download = `上游合同导出_${new Date().toISOString().slice(0, 10)}.xlsx`
    link.click()
    window.URL.revokeObjectURL(link.href)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

// Import functionality
const handleImportCommand = (command) => {
  if (command === 'template') {
    handleDownloadTemplate()
  } else if (command === 'import') {
    importFileInput.value?.click()
  }
}

const handleDownloadTemplate = async () => {
  try {
    ElMessage.info('正在下载模板...')
    const res = await downloadImportTemplate()
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    link.download = '上游合同导入模板.xlsx'
    link.click()
    window.URL.revokeObjectURL(link.href)
    ElMessage.success('模板下载成功')
  } catch (e) {
    ElMessage.error('模板下载失败')
  }
}

const handleImportFileChange = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  
  // Reset file input for next use
  event.target.value = ''
  
  try {
    importLoading.value = true
    ElMessage.info('正在导入数据...')
    
    const result = await importContracts(file)
    
    // Show result dialog
    importResult.success_count = result.success_count || 0
    importResult.error_count = result.error_count || 0
    importResult.errors = result.errors || []
    importResult.visible = true
    
    // Refresh list if any successful imports
    if (result.success_count > 0) {
      getList()
    }
  } catch (e) {
    ElMessage.error('导入失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    importLoading.value = false
  }
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

:deep(.amount-input-right .el-input__inner) {
  text-align: right;
}

.text-gray {
  color: #c0c4cc;
}
</style>
