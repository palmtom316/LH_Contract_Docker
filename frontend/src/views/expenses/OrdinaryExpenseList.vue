<template>
  <div class="expense-list-page">
    <AppWorkspacePanel panel-class="expense-list-panel expense-list-panel--filters">
      <AppSectionCard class="expense-list-card">
      <AppFilterBar inline-actions>
        <el-select v-model="queryParams.attribution" placeholder="费用归属" clearable>
          <el-option label="公司费用" value="公司费用" />
          <el-option label="项目费用" value="项目费用" />
        </el-select>
        <AppRangeField
          v-model="dateRange"
          class="filter-control--time"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
        />
        <el-select
          v-model="queryParams.upstream_contract_id"
          class="filter-control--wide"
          placeholder="上游合同(序号/编号/名称/甲方)"
          filterable
          remote
          reserve-keyword
          clearable
          :remote-method="searchUpstreamContractsForFilter"
          :loading="loadingContracts"
        >
          <el-option
            v-for="item in filterUpstreamContracts"
            :key="item.id"
            :label="buildUpstreamOptionLabel(item)"
            :value="item.id"
          >
            <div style="display: flex; flex-direction: column; gap: 2px; line-height: 1.4;">
              <span>{{ buildUpstreamOptionLabel(item) }}</span>
              <span class="contract-option-code">{{ buildUpstreamOptionMeta(item) }}</span>
            </div>
          </el-option>
        </el-select>
        <DictSelect
          v-model="queryParams.category"
          category="expense_type"
          placeholder="费用分类"
          clearable
        />
        <template #actions>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
        <el-button v-if="!isMobile" type="primary" plain icon="Plus" @click="handleAdd">新增费用</el-button>
        <el-button v-if="!isMobile" icon="Download" @click="handleExport">导出</el-button>
        <el-dropdown v-if="isMobile" trigger="click" class="action-item">
          <el-button icon="More" circle />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleAdd"><el-icon><Plus /></el-icon> 新增费用</el-dropdown-item>
              <el-dropdown-item @click="handleExport"><el-icon><Download /></el-icon> 导出 Excel</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        </template>
      </AppFilterBar>
      </AppSectionCard>
    </AppWorkspacePanel>

    <!-- Table -->
    <AppWorkspacePanel panel-class="expense-list-panel expense-list-panel--results">
      <AppSectionCard v-if="isMobile" class="expense-list-card">
      <template #header>费用列表</template>
      <AppEmptyState
        v-if="!loading && !expenseList.length"
        title="暂无费用记录"
      />
      <div v-else class="mobile-list-container">
      <el-card v-for="item in expenseList" :key="item.id" class="mobile-card" shadow="sm">
        <div class="mobile-card-header">
          <span class="mobile-card-title">{{ item.expense_code }}</span>
          <el-tag size="small" :type="isProjectExpense(item.category) ? 'warning' : 'info'">{{ translateCategory(item.category) }}</el-tag>
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
            <span class="label">备注:</span>
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
      </AppSectionCard>

      <AppSectionCard v-else class="expense-list-card">
      <template #header>费用列表</template>
      <AppDataTable>
      <el-table 
        v-loading="loading" 
        :data="expenseList" 
        style="width: 100%" 
        border
        highlight-current-row
        show-summary
        :summary-method="getSummaries"
        class="custom-footer-table"
      >
        <el-table-column prop="expense_code" label="编号" width="120" fixed />
        <el-table-column prop="expense_date" label="日期" width="110" sortable />
        <el-table-column label="费用归属" width="100">
          <template #default="scope">
            {{ translateCategory(scope.row.category) }}
          </template>
        </el-table-column>
        <el-table-column label="费用分类" width="100">
          <template #default="scope">
            <el-tag effect="plain">{{ translateExpenseType(scope.row.expense_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="上游合同名称" min-width="150">
          <template #default="scope">
            <div v-if="scope.row.upstream_contract" :style="{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.5', maxHeight: '4.5em', overflow: 'hidden' }">
              {{ scope.row.upstream_contract.contract_name }}
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="说明" min-width="150">
          <template #default="scope">
            <div :style="{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.5', maxHeight: '4.5em', overflow: 'hidden' }">{{ scope.row.description }}</div>
          </template>
        </el-table-column>

        <el-table-column label="费用文件" width="80" align="center">
          <template #default="scope">
            <el-button 
              v-if="scope.row.file_path" 
              link 
              type="primary" 
              size="small"
              icon="Document"
              @click="viewExpenseFile(scope.row.file_path)"
            >查看</el-button>
            <span v-else class="cell-placeholder">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="amount" label="金额" width="120" align="right">
          <template #default="scope">
             <span style="white-space: nowrap;">¥ {{ Number(scope.row.amount).toLocaleString() }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="140" fixed="right">
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
      </AppDataTable>
      </AppSectionCard>
    </AppWorkspacePanel>

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
             <el-input v-model="form.expense_code" placeholder="留空则自动生成 (F-年-月-序号)">
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="费用日期" prop="expense_date">
              <SmartDateInput 
                v-model="form.expense_date" 
                placeholder="选择日期" 
                style="width: 100%" 
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
              <DictSelect 
                v-model="form.expense_type" 
                category="expense_type" 
                placeholder="请选择" 
                style="width: 100%" 
              />
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
                  :label="'[' + (item.serial_number || '-') + '] ' + item.contract_name"
                  :value="item.id"
                >
                  <span>[{{ item.serial_number || '-' }}] {{ item.contract_name }}</span>
                  <span class="contract-option-code">{{ item.contract_code }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="金额" prop="amount">
          <FormulaInput 
            v-model="form.amount" 
            placeholder="支持公式计算" 
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
              <div class="el-upload__tip">仅支持 PDF</div>
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
import { defineAsyncComponent, ref, reactive, onMounted, onUnmounted } from 'vue'
import { getExpenses, createExpense, updateExpense, deleteExpense, exportExpenses } from '@/api/expense'
import { getContracts, getContract } from '@/api/contractUpstream'
import { uploadFile } from '@/api/common'
import { getFileUrl, formatMoney } from '@/utils/common'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Download, Document, Edit, Delete, More } from '@element-plus/icons-vue'
import AppSectionCard from '@/components/ui/AppSectionCard.vue'
import AppFilterBar from '@/components/ui/AppFilterBar.vue'
import AppDataTable from '@/components/ui/AppDataTable.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import AppRangeField from '@/components/ui/AppRangeField.vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'

const loading = ref(false)
const total = ref(0)
const expenseList = ref([])
const fileList = ref([])
const upstreamContracts = ref([])
const filterUpstreamContracts = ref([])
const loadingContracts = ref(false)
const isMobile = ref(false)
const dateRange = ref([])

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

const queryParams = reactive({
  page: 1,
  page_size: 10,

  attribution: '',
  category: '',
  upstream_contract_id: null
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
  notes: '',
  file_path: '',
  file_key: ''
})

const rules = {
  // expense_code is now optional - auto-generated if empty
  category: [{ required: true, message: '请选择费用归属', trigger: 'change' }],
  expense_type: [{ required: true, message: '请选择费用分类', trigger: 'change' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }],
  expense_date: [{ required: true, message: '请选择日期', trigger: 'change' }]
}

import SmartDateInput from '@/components/SmartDateInput.vue'
import DictSelect from '@/components/DictSelect.vue'

const FormulaInput = defineAsyncComponent(() => import('@/components/FormulaInput.vue'))

const buildUpstreamOptionLabel = (item) => {
  const serialNumber = item?.serial_number ?? '-'
  const contractName = item?.contract_name || '未命名合同'
  return `[${serialNumber}] ${contractName}`
}

const buildUpstreamOptionMeta = (item) => {
  const contractCode = item?.contract_code || '未填写编号'
  const partyAName = item?.party_a_name || '未填写甲方'
  return `${contractCode} · ${partyAName}`
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
    const [startDate, endDate] = dateRange.value || []
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    const res = await getExpenses(params)
    expenseList.value = res.items
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
  queryParams.attribution = ''
  queryParams.category = ''
  dateRange.value = []
  queryParams.upstream_contract_id = null
  filterUpstreamContracts.value = []
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

// Form handling
const handleExport = async () => {
  try {
    const params = {
      category: queryParams.attribution, // "Company/Project" maps to category
      expense_type: queryParams.category, // "Salary/Bonus" maps to expense_type
      upstream_contract_id: queryParams.upstream_contract_id || undefined
    }
    
    const [startDate, endDate] = dateRange.value || []
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate

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
  form.expense_code = '' // Leave empty for auto-generation (F-YYYY-MM-NNN)
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

const searchUpstreamContractsForFilter = async (query) => {
  if (!query) {
    filterUpstreamContracts.value = []
    return
  }
  loadingContracts.value = true
  try {
    const res = await getContracts({ keyword: query, page: 1, page_size: 20 })
    filterUpstreamContracts.value = res.items || []
  } finally {
    loadingContracts.value = false
  }
}

const handleUploadRequest = async (option) => {
  try {
    const result = await uploadFile(option.file, 'expenses')
    form.file_path = result.path
    if (result.key) form.file_key = result.key
    fileList.value = [{ name: option.file.name, url: result.path }]
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

const isProjectExpense = category => ['PROJECT', '项目费用'].includes(category)

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

// Feishu Approval Helpers (V1.4)
const getApprovalStatusType = (status) => {
  const map = {
    'DRAFT': 'info',
    'PENDING': 'warning',
    'APPROVED': 'success',
    'REJECTED': 'danger'
  }
  return map[status] || 'info'
}

const formatApprovalStatus = (status) => {
  const map = {
    'DRAFT': '草稿',
    'PENDING': '审批中',
    'APPROVED': '已通过',
    'REJECTED': '已拒绝'
  }
  return map[status] || status
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

<style scoped lang="scss">
.expense-list-page {
  display: grid;
  gap: var(--workspace-shell-gap);
}

.expense-list-panel {
  gap: 0;
}

.expense-list-card {
  border: 0;
  background: transparent;
  box-shadow: none;
  border-radius: 0;
}

.expense-list-card :deep(.el-card__header) {
  padding: 0 0 16px;
}

.expense-list-card :deep(.el-card__body) {
  padding: 0;
}

.expense-list-panel :deep(.el-table td.el-table__cell),
.expense-list-panel :deep(.el-table th.el-table__cell) {
  padding-top: 14px;
  padding-bottom: 14px;
}

.pagination-container {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.mobile-list-container {
  display: grid;
  gap: 14px;
}

.mobile-card {
  border-radius: 18px;
  box-shadow: none;
}

.mobile-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 10px;
}

.mobile-card-title {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
}

.mobile-card-body {
  font-size: 14px;
}

.mobile-card-row {
  display: flex;
  margin-bottom: 8px;
  gap: 10px;
  line-height: 1.55;
}

.mobile-card-row .label {
  color: var(--text-muted);
  width: 70px;
  flex-shrink: 0;
}

.mobile-card-row .value {
  color: var(--text-secondary);
  flex: 1;
  word-break: break-word;
}

.mobile-card-row .value.amount {
  color: var(--status-danger);
  font-weight: bold;
}

.mobile-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border-subtle);
}

.description {
  white-space: pre-wrap;
}

.action-item {
  display: inline-flex;
}

.cell-placeholder {
  color: var(--text-muted);
}

.contract-name-cell {
  white-space: normal;
  word-break: break-word;
  line-height: 1.5;
}

.contract-option-code {
  float: right;
  font-size: 12px;
  color: var(--text-muted);
}

@media (max-width: 767px) {
  .mobile-card-header,
  .mobile-card-footer {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
