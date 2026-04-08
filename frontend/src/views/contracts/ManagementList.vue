<template>
  <div class="management-page-shell">
    <AppPageHeader
      class="management-page-header"
      title="管理合同"
    />

    <AppWorkspacePanel panel-class="management-page-panel management-page-panel--filters">
      <AppSectionCard class="management-page-card">
      <template #header>合同筛选</template>
      <AppFilterBar inline-actions>
        <el-input v-model="queryParams.keyword" class="filter-control--search" placeholder="合同序号/编号/名称/乙方" clearable @keyup.enter="handleQuery" />
        <el-select
          v-model="queryParams.upstream_contract_id"
          class="filter-control--wide"
          placeholder="上游合同(序号/编号/名称/甲方)"
          filterable
          remote
          reserve-keyword
          clearable
          :remote-method="searchUpstreamFilter"
          :loading="upstreamFilterLoading"
        >
          <el-option
            v-for="item in upstreamFilterOptions"
            :key="item.id"
            :label="buildUpstreamOptionLabel(item)"
            :value="item.id"
          >
            <div style="display: flex; flex-direction: column; gap: 2px; line-height: 1.4;">
              <span>{{ buildUpstreamOptionLabel(item) }}</span>
              <span class="contract-option-meta">{{ buildUpstreamOptionMeta(item) }}</span>
            </div>
          </el-option>
        </el-select>
        <AppRangeField
          v-model="dateRange"
          class="filter-control--time"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
        />
        <el-select v-model="queryParams.status" placeholder="合同状态" clearable>
          <el-option label="执行中" value="执行中" />
          <el-option label="已完工" value="已完工" />
          <el-option label="已结算" value="已结算" />
          <el-option label="质保到期" value="质保到期" />
          <el-option label="合同终止" value="合同终止" />
          <el-option label="合同中止" value="合同中止" />
        </el-select>
        <DictSelect v-model="queryParams.category" category="management_contract_category" placeholder="合同分类" clearable />
        <template #actions>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
        <el-button type="primary" plain icon="Download" @click="handleExport">导出</el-button>
        <el-button v-if="userStore.canManageManagementContracts" type="primary" icon="Plus" @click="handleAdd">新建合同</el-button>
        </template>
      </AppFilterBar>
      </AppSectionCard>
    </AppWorkspacePanel>

    <!-- Table View (PC) -->
    <AppWorkspacePanel panel-class="management-page-panel management-page-panel--list">
      <AppSectionCard v-if="!isMobile" class="management-page-card">
      <template #header>合同列表</template>
      <AppDataTable>
      <el-table 
        v-loading="loading" 
        :data="contractList" 
        style="width: 100%" 
        border
        highlight-current-row
        show-summary
        :summary-method="getSummaries"
        class="custom-footer-table contract-table--dense"
        :footer-cell-style="footerCellStyle"
      >
        <el-table-column prop="serial_number" label="合同序号" width="100" fixed />
        <el-table-column prop="contract_code" label="合同编号" min-width="100" fixed />
        <el-table-column prop="contract_name" label="合同名称" min-width="220">
          <template #default="scope">
            <div class="contract-cell--wrap">{{ scope.row.contract_name }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="party_b_name" label="乙方(供应商)" min-width="180">
          <template #default="scope">
            <div class="contract-cell--wrap">{{ scope.row.party_b_name }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="company_category" label="费用归属" width="100" show-overflow-tooltip />
        <el-table-column prop="category" label="合同类别" width="140" show-overflow-tooltip />
        <el-table-column prop="contract_amount" label="合同金额" width="150" align="right">
          <template #default="scope">
            <span class="contract-cell--amount">¥ {{ Number(scope.row.contract_amount).toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_payable" label="应付款" width="140" align="right">
          <template #default="scope">
            <span v-if="scope.row.total_payable" class="contract-cell--amount">¥ {{ Number(scope.row.total_payable).toLocaleString() }}</span>
            <span v-else class="cell-placeholder">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_invoiced" label="挂账" width="140" align="right">
          <template #default="scope">
            <span v-if="scope.row.total_invoiced" class="contract-cell--amount">¥ {{ Number(scope.row.total_invoiced).toLocaleString() }}</span>
            <span v-else class="cell-placeholder">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_paid" label="已付款" width="140" align="right">
          <template #default="scope">
            <span v-if="scope.row.total_paid" class="contract-cell--amount">¥ {{ Number(scope.row.total_paid).toLocaleString() }}</span>
            <span v-else class="cell-placeholder">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_settlement" label="结算" width="140" align="right">
          <template #default="scope">
            <span v-if="scope.row.total_settlement" class="contract-cell--amount">¥ {{ Number(scope.row.total_settlement).toLocaleString() }}</span>
            <span v-else class="cell-placeholder">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="sign_date" label="签订日期" width="100" sortable />
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
            <span v-else class="cell-placeholder">-</span>
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
      </AppDataTable>
      </AppSectionCard>

      <!-- Card View (Mobile) -->
      <AppSectionCard v-else class="management-page-card">
      <template #header>合同列表</template>
      <AppEmptyState
        v-if="!loading && !contractList.length"
        title="暂无管理合同"
      />
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
          <el-button
            v-if="item.contract_file_path"
            size="small"
            @click="openPdfInNewTab(item.contract_file_path)"
          >
            文件
          </el-button>
          <el-button v-if="userStore.canManageManagementContracts" size="small" type="primary" @click="handleEdit(item)">编辑</el-button>
          <el-button size="small" @click="handleDetail(item)">详情</el-button>
          <el-button v-if="userStore.canManageManagementContracts" size="small" type="danger" @click="handleDelete(item)">删除</el-button>
        </div>
      </el-card>
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
      </AppSectionCard>
    </AppWorkspacePanel>

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
              :label="buildUpstreamOptionLabel(item)"
              :value="item.id"
            >
              <div style="display: flex; flex-direction: column; gap: 2px; line-height: 1.4;">
                <span>{{ buildUpstreamOptionLabel(item) }}</span>
                <span class="contract-option-meta">{{ buildUpstreamOptionMeta(item) }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- Summary Banner -->
        <div v-if="upstreamSummary && form.company_category === '项目费用'" class="summary-strip">
          <div class="summary-strip__item">
            <span class="summary-strip__label">上游编号</span>
            <span class="summary-strip__value">{{ upstreamSummary.contract_code }}</span>
          </div>
          <div class="summary-strip__item">
            <span class="summary-strip__label">甲方</span>
            <span class="summary-strip__value">{{ upstreamSummary.party_a_name }}</span>
          </div>
          <div class="summary-strip__item">
            <span class="summary-strip__label">总金额</span>
            <span class="summary-strip__value">¥ {{ Number(upstreamSummary.contract_amount).toLocaleString() }}</span>
          </div>
        </div>

        <el-row :gutter="20">
          <el-col :span="12">
             <el-form-item label="合同编号" prop="contract_code">
              <el-input v-model="form.contract_code" placeholder="留空则自动生成 (G-年-月-序号)">
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="签订日期" prop="sign_date">
              <SmartDateInput 
                v-model="form.sign_date" 
                placeholder="选择日期" 
                style="width: 100%" 
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="费用分类" prop="category">
          <DictSelect 
            v-model="form.category" 
            category="management_contract_category" 
            placeholder="请选择费用分类" 
            style="width: 100%" 
          />
        </el-form-item>
        
        <el-form-item label="合同名称" prop="contract_name">
          <el-input v-model="form.contract_name" placeholder="请输入合同名称" />
        </el-form-item>
        
        <el-form-item label="甲方单位" prop="party_a_name">
          <SmartAutocomplete v-model="form.party_a_name" placeholder="请输入甲方名称" />
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
          <FormulaInput 
            v-model="form.contract_amount" 
            placeholder="支持公式计算" 
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

        <el-row :gutter="20">
          <el-col :span="12">
             <el-form-item label="合同经办人" prop="contract_handler">
              <el-input v-model="form.contract_handler" placeholder="请输入合同经办人姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
             <el-form-item label="合同负责人" prop="contract_manager">
              <el-input v-model="form.contract_manager" placeholder="请输入合同负责人姓名" />
            </el-form-item>
          </el-col>
        </el-row>

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
import { defineAsyncComponent, ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getContracts, createContract, updateContract, deleteContract, exportContracts } from '@/api/contractManagement'
import { getContracts as getUpstreamContracts, getContractSummary } from '@/api/contractUpstream'
import { uploadFile } from '@/api/common'
import { getFileUrl } from '@/utils/common'
import { useContractList, useTableSummary, useMobileDetection } from '@/composables/useContractList'
import { downloadExcel, generateFilename } from '@/utils/download'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Download, Document, Connection, More } from '@element-plus/icons-vue'
import SmartDateInput from '@/components/SmartDateInput.vue'
import DictSelect from '@/components/DictSelect.vue'
import { useUserStore } from '@/stores/user'
import AppSectionCard from '@/components/ui/AppSectionCard.vue'
import AppFilterBar from '@/components/ui/AppFilterBar.vue'
import AppDataTable from '@/components/ui/AppDataTable.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppRangeField from '@/components/ui/AppRangeField.vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'

const SmartAutocomplete = defineAsyncComponent(() => import('@/components/SmartAutocomplete.vue'))
const FormulaInput = defineAsyncComponent(() => import('@/components/FormulaInput.vue'))

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()
const { isMobile, checkIsMobile } = useMobileDetection()

const {
  loading,
  list: contractList,
  total,
  queryParams,
  getList,
  handleQuery: baseHandleQuery,
  resetQuery: baseResetQuery,
  handleDelete,
  handleExport: baseHandleExport,
  formatMoney,
  getStatusType
} = useContractList({
  api: { getContracts, deleteContract, exportContracts },
  contractType: '管理合同',
  exportPrefix: '管理合同列表'
})

const dateRange = ref([])
queryParams.upstream_contract_id = queryParams.upstream_contract_id || undefined

const handleQuery = () => {
  queryParams.page = 1
  const [startDate, endDate] = dateRange.value || []
  queryParams.start_date = startDate || undefined
  queryParams.end_date = endDate || undefined
  getList()
}

const handleExport = async () => {
  const [startDate, endDate] = dateRange.value || []
  queryParams.start_date = startDate || undefined
  queryParams.end_date = endDate || undefined
  await baseHandleExport()
}

const resetQuery = () => {
  dateRange.value = []
  queryParams.start_date = undefined
  queryParams.end_date = undefined
  queryParams.category = undefined
  queryParams.upstream_contract_id = undefined
  upstreamFilterOptions.value = []
  baseResetQuery()
}

const { getSummaries: baseGetSummaries, footerCellStyle } = useTableSummary()

const getSummaries = (param) => {
  return baseGetSummaries(param, ['contract_amount', 'total_payable', 'total_invoiced', 'total_paid', 'total_settlement'])
}

const fileList = ref([])
const originalId = ref(null)

// Upstream Search
const upstreamLoading = ref(false)
const upstreamOptions = ref([])
const upstreamSummary = ref(null)
const upstreamFilterLoading = ref(false)
const upstreamFilterOptions = ref([])

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
  contract_handler: '',   // 合同经办人
  contract_manager: '',   // 合同负责人
  contract_file_path: '',
  contract_file_key: '',
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
  // contract_code is now optional - auto-generated if empty
  contract_name: [{ required: true, message: '请输入合同名称', trigger: 'blur' }],
  party_a_name: [{ required: true, message: '请输入甲方名称', trigger: 'blur' }],
  party_b_name: [{ required: true, message: '请输入乙方名称', trigger: 'blur' }],
  contract_amount: [{ required: true, message: '请输入合同金额', trigger: 'blur' }]
}

// Check Is Mobile
const handleResize = () => checkIsMobile()

// Logic for Upstream Search
const searchUpstream = async (query) => {
  if (query) {
    upstreamLoading.value = true
    try {
      const res = await getUpstreamContracts({ keyword: query, page_size: 100 })
      upstreamOptions.value = res.items
    } catch (e) {
      console.error(e)
    }
    upstreamLoading.value = false
  } else {
    upstreamOptions.value = []
  }
}

const searchUpstreamFilter = async (query) => {
  if (!query) {
    upstreamFilterOptions.value = []
    return
  }
  upstreamFilterLoading.value = true
  try {
    const res = await getUpstreamContracts({ keyword: query, page_size: 100 })
    upstreamFilterOptions.value = res.items || []
  } catch (e) {
    console.error(e)
  } finally {
    upstreamFilterLoading.value = false
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
    const result = await uploadFile(option.file)
    form.contract_file_path = result.path
    if (result.key) form.contract_file_key = result.key
    fileList.value = [{ name: option.file.name, url: result.path }]
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
  form.contract_handler = ''
  form.contract_manager = ''
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


const openPdfInNewTab = (path) => {
  if (path) {
    window.open(getFileUrl(path), '_blank')
  }
}

const handleDetail = (row) => {
  router.push({ 
    name: 'ManagementDetail', 
    params: { id: row.id },
    query: {
      page: queryParams.page,
      keyword: queryParams.keyword || undefined,
      status: queryParams.status || undefined,
      upstream_contract_id: queryParams.upstream_contract_id || undefined
    }
  })
}

onMounted(() => {
  // 从 URL 参数恢复查询条件
  if (route.query.page) {
    queryParams.page = parseInt(route.query.page, 10)
  }
  if (route.query.keyword) {
    queryParams.keyword = route.query.keyword
  }
  if (route.query.status) {
    queryParams.status = route.query.status
  }
  if (route.query.upstream_contract_id) {
    queryParams.upstream_contract_id = parseInt(route.query.upstream_contract_id, 10)
  }
  
  checkIsMobile()
  window.addEventListener('resize', handleResize)
  getList()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})


</script>

<style scoped lang="scss">
.management-page-shell {
  display: grid;
  gap: var(--workspace-shell-gap);
}

.management-page-panel {
  gap: 0;
}

.management-page-card {
  border: 0;
  background: transparent;
  box-shadow: none;
  border-radius: 0;
}

.management-page-card :deep(.el-card__header) {
  padding: 0 0 16px;
}

.management-page-card :deep(.el-card__body) {
  padding: 0;
}

.management-page-panel :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.management-page-panel :deep(.el-table td.el-table__cell),
.management-page-panel :deep(.el-table th.el-table__cell) {
  padding-top: 14px;
  padding-bottom: 14px;
}

:deep(.contract-table--dense .el-table__cell) {
  padding-top: 8px;
  padding-bottom: 8px;
  vertical-align: top;
  font-size: 12px;
  line-height: 1.45;
}

.contract-cell--wrap {
  white-space: normal !important;
  word-break: break-word;
  line-height: 1.45;
  display: block;
}

.contract-cell--amount {
  white-space: nowrap;
}

.filter-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.mobile-actions {
  justify-content: space-between;
  width: 100%;
  margin-top: 10px;
  
  .el-button {
    margin-left: 0 !important;
  }
  
  .action-item {
    margin-left: 0;
  }
}

.pagination-container {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.contract-option-meta,
.cell-placeholder {
  color: var(--text-muted);
}

.contract-option-meta {
  font-size: 12px;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 20px;
  padding: 12px 14px;
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface-panel-muted) 76%, var(--surface-panel) 24%);
}

.summary-strip__item {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.summary-strip__label {
  font-size: 12px;
  color: var(--text-muted);
}

.summary-strip__value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  word-break: break-word;
}

/* Mobile Card View */
.card-list {
  display: grid;
  gap: 14px;

  .contract-card {
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    background: var(--surface-panel);
    box-shadow: none;
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-subtle);
      
      .title {
        font-weight: bold;
        font-size: 15px;
        color: var(--text-primary);
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
          color: var(--text-secondary);
          min-width: 80px;
        }
        
        .value {
          color: var(--text-primary);
          font-weight: 500;
          text-align: right;
          flex: 1;
          
          &.amount {
            color: var(--text-primary);
            font-weight: bold;
          }
        }
      }
    }
    
    .card-footer {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid var(--border-subtle);
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      flex-wrap: wrap;
    }
  }
}

@media (max-width: 900px) {
  .summary-strip {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
/* Global override for table footer */
.custom-footer-table.contract-table--dense .el-table__footer-wrapper tbody td,
.custom-footer-table.contract-table--dense .el-table__fixed-footer-wrapper tbody td,
.custom-footer-table.contract-table--dense .el-table__footer-wrapper tbody tr,
.custom-footer-table.contract-table--dense .el-table__fixed-footer-wrapper tbody tr {
  background-color: color-mix(in srgb, var(--surface-panel-muted) 76%, var(--surface-panel) 24%) !important;
  color: var(--text-primary) !important;
  font-weight: 700 !important;
  font-size: 14px !important;
  --el-table-row-hover-bg-color: color-mix(in srgb, var(--surface-panel-muted) 76%, var(--surface-panel) 24%) !important;
}
.custom-footer-table.contract-table--dense .el-table__footer-wrapper tbody td .cell,
.custom-footer-table.contract-table--dense .el-table__fixed-footer-wrapper tbody td .cell {
  background-color: transparent !important;
  color: var(--text-primary) !important;
  font-weight: 700 !important;
  white-space: nowrap !important;
}
</style>
