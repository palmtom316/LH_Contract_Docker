<template>
  <div class="app-container">
    <!-- Search Bar -->
    <el-card class="filter-container" shadow="never">
      <el-form :inline="true" :model="queryParams" class="demo-form-inline">

        <el-form-item label="费用归属">
          <el-select v-model="queryParams.attribution" placeholder="费用归属" clearable style="width: 140px">
            <el-option label="公司费用" value="公司费用" />
            <el-option label="项目费用" value="项目费用" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="queryParams.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
            clearable
          />
        </el-form-item>
        <el-form-item label="上游合同序号">
          <el-input v-model="queryParams.upstream_contract_id" placeholder="上游合同序号" clearable style="width: 120px" @keyup.enter="handleQuery" />
        </el-form-item>
        <el-form-item label="费用分类">
          <el-select v-model="queryParams.category" placeholder="费用分类" clearable style="width: 140px">
            <el-option label="工资" value="工资" />
            <el-option label="奖金" value="奖金" />
            <el-option label="培训费" value="培训费" />
            <el-option label="资质费" value="资质费" />
            <el-option label="办公费" value="办公费" />
            <el-option label="餐饮费" value="餐饮费" />
            <el-option label="房屋租赁" value="房屋租赁" />
            <el-option label="交通费" value="交通费" />
            <el-option label="车辆使用费" value="车辆使用费" />
            <el-option label="其他租赁" value="其他租赁" />
            <el-option label="水电费" value="水电费" />
            <el-option label="业务费" value="业务费" />
            <el-option label="住宿费" value="住宿费" />
            <el-option label="通讯费" value="通讯费" />
            <el-option label="投标费" value="投标费" />
            <el-option label="中介费" value="中介费" />
            <el-option label="零星采购" value="零星采购" />
            <el-option label="其他费用" value="其他费用" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
          <el-button icon="Refresh" @click="resetQuery">重置</el-button>
          <el-button type="warning" icon="Download" @click="handleExport">导出Excel</el-button>
          <el-button type="success" icon="Plus" @click="handleAdd">新增无合同费用</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Table -->
    <div v-if="isMobile" class="mobile-list-container">
      <el-card v-for="item in expenseList" :key="item.id" class="mobile-card" shadow="sm">
        <div class="mobile-card-header">
          <span class="mobile-card-title">{{ item.expense_code }}</span>
          <el-tag size="small" :type="item.category === '项目费用' ? 'warning' : 'info'">{{ translateCategory(item.category) }}</el-tag>
        </div>
        <div class="mobile-card-body">
          <div class="mobile-card-row">
            <span class="label">金额:</span>
            <span class="value amount">¥ {{ Number(item.amount).toLocaleString() }}</span>
          </div>
          <div class="mobile-card-row">
            <span class="label">日期:</span>
            <span class="value">{{ item.expense_date }}</span>
          </div>
          <div class="mobile-card-row">
            <span class="label">分类:</span>
            <span class="value">{{ translateExpenseType(item.expense_type) }}</span>
          </div>
          <div v-if="item.upstream_contract" class="mobile-card-row">
            <span class="label">关联合同:</span>
            <span class="value contract-link">{{ item.upstream_contract.contract_name }}</span>
          </div>
          <div class="mobile-card-row">
            <span class="label">说明:</span>
            <div class="value description">{{ item.description || '-' }}</div>
          </div>
        </div>
        <div class="mobile-card-footer">
          <div class="left-actions">
             <el-button v-if="item.file_path" link type="primary" size="small" icon="Document" @click="viewExpenseFile(item.file_path)">附件</el-button>
          </div>
          <div class="right-actions">
            <el-button link type="primary" size="small" icon="Edit" @click="handleEdit(item)">编辑</el-button>
            <el-button link type="danger" size="small" icon="Delete" @click="handleDelete(item)">删除</el-button>
          </div>
        </div>
      </el-card>
      
       <!-- Mobile Pagination -->
       <div class="pagination-container">
          <el-pagination
            v-model:current-page="queryParams.page"
            v-model:page-size="queryParams.page_size"
            layout="prev, pager, next"
            :total="total"
            small
            @current-change="getList"
          />
       </div>
    </div>

    <el-card v-else class="table-container" shadow="always">
      <el-table 
        v-loading="loading" 
        :data="expenseList" 
        style="width: 100%" 
        border
        highlight-current-row
        show-summary
        :summary-method="getSummaries"
        class="custom-footer-table"
        :footer-cell-style="footerCellStyle"
      >
        <el-table-column prop="expense_code" label="编号" width="140" fixed />
        <el-table-column prop="expense_date" label="日期" width="120" sortable />
        <el-table-column label="费用归属" width="120">
          <template #default="scope">
            {{ translateCategory(scope.row.category) }}
          </template>
        </el-table-column>
        <el-table-column label="费用分类" width="100">
          <template #default="scope">
            <el-tag effect="plain">{{ translateExpenseType(scope.row.expense_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="上游合同名称" min-width="180">
          <template #default="scope">
            <div v-if="scope.row.upstream_contract" :style="{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.5', maxHeight: '4.5em', overflow: 'hidden' }">
              {{ scope.row.upstream_contract.contract_name }}
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="说明" min-width="200">
          <template #default="scope">
            <div :style="{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.5', maxHeight: '4.5em', overflow: 'hidden' }">{{ scope.row.description }}</div>
          </template>
        </el-table-column>

        <el-table-column label="费用文件" width="100" align="center">
          <template #default="scope">
            <el-link v-if="scope.row.file_path" type="primary" @click="viewExpenseFile(scope.row.file_path)">查看</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="140" align="right">
          <template #default="scope">
             ¥ {{ Number(scope.row.amount).toLocaleString() }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-button link type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>

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

    <!-- Dialog -->
    <el-dialog
      :title="dialog.title"
      v-model="dialog.visible"
      :width="isMobile ? '90%' : '600px'"
      append-to-body
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" :label-position="isMobile ? 'top' : 'right'">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12">
             <el-form-item label="费用编号" prop="expense_code">
              <el-input v-model="form.expense_code" placeholder="系统自动生成" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="费用日期" prop="expense_date">
              <el-date-picker 
                v-model="form.expense_date" 
                type="date" 
                placeholder="选择日期" 
                style="width: 100%" 
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :xs="24" :sm="12">
            <el-form-item label="费用归属" prop="category">
              <el-select v-model="form.category" placeholder="请选择" style="width: 100%">
                <el-option label="公司费用" value="公司费用" />
                <el-option label="项目费用" value="项目费用" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="费用分类" prop="expense_type">
              <el-select v-model="form.expense_type" placeholder="请选择" style="width: 100%">
            <el-option label="工资" value="工资" />
            <el-option label="奖金" value="奖金" />
            <el-option label="培训费" value="培训费" />
            <el-option label="资质费" value="资质费" />
            <el-option label="办公费" value="办公费" />
            <el-option label="餐饮费" value="餐饮费" />
            <el-option label="房屋租赁" value="房屋租赁" />
            <el-option label="交通费" value="交通费" />
            <el-option label="车辆使用费" value="车辆使用费" />
            <el-option label="其他租赁" value="其他租赁" />
            <el-option label="水电费" value="水电费" />
            <el-option label="业务费" value="业务费" />
            <el-option label="住宿费" value="住宿费" />
            <el-option label="通讯费" value="通讯费" />
            <el-option label="投标费" value="投标费" />
            <el-option label="中介费" value="中介费" />
            <el-option label="零星采购" value="零星采购" />
            <el-option label="其他费用" value="其他费用" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" v-if="form.category === '项目费用'">
          <el-col :span="24">
            <el-form-item label="关联上游" prop="upstream_contract_id">
              <el-select
                v-model="form.upstream_contract_id"
                filterable
                remote
                clearable
                placeholder="请输入合同序号/编号/名称搜索"
                :remote-method="searchUpstreamContracts"
                :loading="loadingContracts"
                style="width: 100%"
              >
                <el-option
                  v-for="item in upstreamContracts"
                  :key="item.id"
                  :label="item.contract_code + ' - ' + item.contract_name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="金额" prop="amount">
          <el-input-number 
            v-model="form.amount" 
            :precision="2" 
            :step="100" 
            :min="0" 
            :controls="false"
            style="width: 100%" 
          />
        </el-form-item>

        <el-form-item label="费用说明" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>

        <el-form-item label="费用文件" prop="file_path">
          <el-upload
            v-model:file-list="fileList"
            class="upload-demo"
            action="#"
            :http-request="handleUploadRequest"
            :limit="1"
            :on-exceed="handleExceed"
            :on-remove="handleRemove"
            :on-preview="handlePreview"
            accept=".pdf"
          >
            <el-button type="primary">点击上传</el-button>
            <template #tip>
              <div class="el-upload__tip">只能上传 PDF 文件</div>
            </template>
          </el-upload>
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
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { getExpenses, createExpense, updateExpense, deleteExpense, approveExpense, exportExpenses } from '@/api/expense'
import { getContracts, getContract } from '@/api/contractUpstream'
import { uploadFile } from '@/api/common'
import { getFileUrl, formatMoney } from '@/utils/common'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const total = ref(0)
const expenseList = ref([])
const fileList = ref([])
const upstreamContracts = ref([])
const loadingContracts = ref(false)
const isMobile = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

const queryParams = reactive({
  page: 1,
  page_size: 10,

  attribution: '',
  category: '',

  dateRange: null,
  upstream_contract_id: ''
})

const dialog = reactive({
  title: '',
  visible: false,
  isEdit: false
})

const formRef = ref(null)
const form = reactive({
  id: undefined,
  expense_code: '',
  category: '', // 费用归属（公司费用/项目费用）
  expense_type: '', // 费用分类（工资、奖金等）
  upstream_contract_id: undefined,
  amount: 0,
  tax_amount: 0,
  expense_date: '',
  description: '',
  file_path: ''
})

const rules = {
  expense_code: [{ required: true, message: '请输入编号', trigger: 'blur' }],
  category: [{ required: true, message: '请选择费用归属', trigger: 'change' }],
  expense_type: [{ required: true, message: '请选择费用分类', trigger: 'change' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }],
  expense_date: [{ required: true, message: '请选择日期', trigger: 'change' }]
}

const getList = async () => {
  loading.value = true
  try {
    // Build query params
    const params = {
      page: queryParams.page,
      page_size: queryParams.page_size,
      category: queryParams.attribution, // "Company/Project" maps to category
      expense_type: queryParams.category, // "Salary/Bonus" maps to expense_type
      upstream_contract_id: queryParams.upstream_contract_id || undefined
    }
    // Handle date range
    if (queryParams.dateRange && queryParams.dateRange.length === 2) {
      params.start_date = queryParams.dateRange[0]
      params.end_date = queryParams.dateRange[1]
    }
    const res = await getExpenses(params)
    expenseList.value = res.items
    total.value = res.total
    
    // Debug: Log expense data
    console.log('Loaded expenses:', expenseList.value.length)
    if (expenseList.value.length > 0) {
      console.log('First expense file_path:', expenseList.value[0].file_path)
    }
  } finally {
    loading.value = false
  }
}

const handleQuery = () => {
  queryParams.page = 1
  getList()
}

const resetQuery = () => {
  queryParams.attribution = ''
  queryParams.category = ''
  queryParams.dateRange = null
  queryParams.upstream_contract_id = ''
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
    
    if (column.property === 'amount') {
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

// Form handling
const handleExport = async () => {
  try {
    const params = {
      category: queryParams.attribution, // "Company/Project" maps to category
      expense_type: queryParams.category, // "Salary/Bonus" maps to expense_type
      upstream_contract_id: queryParams.upstream_contract_id || undefined
    }
    
    if (queryParams.dateRange && queryParams.dateRange.length === 2) {
      params.start_date = queryParams.dateRange[0]
      params.end_date = queryParams.dateRange[1]
    }

    const res = await exportExpenses(params)
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    link.download = `费用列表_${new Date().toISOString().slice(0, 10)}.xlsx`
    link.click()
    window.URL.revokeObjectURL(link.href)
    ElMessage.success('导出成功')
  } catch (e) {
    console.error('Export Error:', e)
    ElMessage.error('导出失败: ' + (e.message || e))
  }
}

const resetForm = () => {
  form.id = undefined
  form.expense_code = 'FY' + new Date().getTime().toString().substr(-8) // Generate simple code
  form.category = '' // 费用归属
  form.expense_type = '' // 费用分类
  form.upstream_contract_id = undefined
  form.amount = 0
  form.tax_amount = 0
  form.expense_date = new Date().toISOString().split('T')[0]
  form.description = ''
  form.file_path = ''
  fileList.value = []
}

const handleAdd = () => {
  resetForm()
  dialog.title = '新建费用记录'
  dialog.isEdit = false
  dialog.visible = true
}

const handleEdit = async (row) => {
  resetForm()
  Object.assign(form, row)
  fileList.value = row.file_path ? [{ name: '费用文件', url: row.file_path }] : []
  
  if (row.upstream_contract_id) {
    try {
      const contract = await getContract(row.upstream_contract_id)
      upstreamContracts.value = [contract]
    } catch (e) {
      console.error(e)
    }
  } else {
    upstreamContracts.value = []
  }
  
  dialog.title = '编辑费用'
  dialog.isEdit = true
  dialog.visible = true
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      console.log('Submitting expense form:', form)
      console.log('File path:', form.file_path)
      
      if (dialog.isEdit) {
        await updateExpense(form.id, form)
        ElMessage.success('更新成功')
      } else {
        await createExpense(form)
        ElMessage.success('创建成功')
      }
      dialog.visible = false
      getList()
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除这条费用记录吗?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteExpense(row.id)
      ElMessage.success('删除成功')
      getList()
    } catch (e) {
      console.error(e)
    }
  })
}

const handleApprove = async (row, approved) => {
  await approveExpense(row.id, approved)
  ElMessage.success(approved ? '审核通过' : '已驳回')
  getList()
}

const searchUpstreamContracts = async (query) => {
  if (query) {
    loadingContracts.value = true
    try {
      const res = await getContracts({ keyword: query, page: 1, page_size: 20 })
      upstreamContracts.value = res.items
    } finally {
      loadingContracts.value = false
    }
  } else {
    upstreamContracts.value = []
  }
}

const handleUploadRequest = async (option) => {
  try {
    const res = await uploadFile(option.file)
    console.log('Upload result:', res)
    form.file_path = res.path
    console.log('File path set to:', form.file_path)
    fileList.value = [{ name: option.file.name, url: res.path }]
    ElMessage.success('上传成功')
  } catch (e) {
    console.error('Upload error:', e)
    ElMessage.error('上传失败')
    option.onError(e)
  }
}

const handleExceed = (files) => {
  ElMessage.warning('只能上传一个文件，请先删除旧文件')
}

const handleRemove = () => {
  form.file_path = ''
  fileList.value = []
}

const handlePreview = (file) => {
  if (file.url) {
    const url = getFileUrl(file.url)
    if (url) window.open(url, '_blank')
  } else {
    ElMessage.warning('没有可查看的文件')
  }
}

const viewExpenseFile = (filePath) => {
  if (filePath) {
    const url = getFileUrl(filePath)
    if (url) window.open(url, '_blank')
  } else {
    ElMessage.warning('没有可查看的文件')
  }
}

// Translation functions
const translateCategory = (category) => {
  const map = {
    'COMPANY': '公司费用',
    'PROJECT': '项目费用',
    '公司费用': '公司费用',
    '项目费用': '项目费用'
  }
  return map[category] || category || '-'
}

const translateExpenseType = (expenseType) => {
  const map = {
    'MANAGEMENT': '管理费',
    'TRAINING': '培训费',
    'CATERING': '餐饮费',
    'TRANSPORT': '交通费',
    'CONSULTING': '咨询费',
    'BUSINESS': '业务费',
    'LEASING': '租赁费',
    'QUALIFICATION': '资质费',
    'VEHICLE': '车辆使用费',
    '工资': '工资',
    '奖金': '奖金',
    '培训费': '培训费',
    '资质费': '资质费',
    '办公费': '办公费',
    '餐饮费': '餐饮费',
    '房屋租赁': '房屋租赁',
    '交通费': '交通费',
    '车辆使用费': '车辆使用费',
    '其他租赁': '其他租赁',
    '水电费': '水电费',
    '业务费': '业务费',
    '住宿费': '住宿费',
    '通讯费': '通讯费',
    '投标费': '投标费',
    '中介费': '中介费',
    '零星采购': '零星采购',
    '其他费用': '其他费用'
  }
  return map[expenseType] || expenseType || '-'
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  getList()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.filter-container {
  margin-bottom: 20px;
}
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* Mobile List Styles */
.mobile-list-container {
  padding-bottom: 20px;
}
.mobile-card {
  margin-bottom: 12px;
  border-radius: 8px;
}
.mobile-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  border-bottom: 1px solid #f0f2f5;
  padding-bottom: 8px;
}
.mobile-card-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}
.mobile-card-body {
  font-size: 14px;
}
.mobile-card-row {
  display: flex;
  margin-bottom: 8px;
  line-height: 1.4;
}
.mobile-card-row .label {
  color: #909399;
  width: 70px;
  flex-shrink: 0;
}
.mobile-card-row .value {
  color: #606266;
  flex: 1;
  word-break: break-word;
}
.mobile-card-row .value.amount {
  color: #F56C6C;
  font-weight: bold;
}
.mobile-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #f0f2f5;
}
.description {
  white-space: pre-wrap;
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
