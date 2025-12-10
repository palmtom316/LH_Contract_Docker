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
            <el-option label="进行中" value="进行中" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已终止" value="已终止" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
          <el-button icon="Refresh" @click="resetQuery">重置</el-button>
          <el-button type="success" icon="Plus" @click="handleAdd">新建合同</el-button>
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
        <el-table-column prop="contract_code" label="合同编号" width="150" fixed />
        <el-table-column prop="contract_name" label="合同名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="party_b_name" label="乙方(供应商/服务商)" min-width="180" show-overflow-tooltip />
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
        <el-table-column label="操作" width="220" fixed="right">
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
            <span class="label">乙方:</span>
            <span class="value">{{ item.party_b_name }}</span>
          </div>
          <div class="info-row">
            <span class="label">合同金额:</span>
            <span class="value amount">¥ {{ Number(item.contract_amount).toLocaleString() }}</span>
          </div>
        </div>
        <div class="card-footer">
          <el-button size="small" type="primary" @click="handleEdit(item)">编辑</el-button>
          <el-button size="small" @click="handleDetail(item)">详情</el-button>
          <el-button size="small" type="danger" @click="handleDelete(item)">删除</el-button>
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
        
        <!-- Upstream Contract Selection & Summary Banner -->
         <el-form-item label="关联上游" prop="upstream_contract_id">
          <el-select
            v-model="form.upstream_contract_id"
            filterable
            remote
            reserve-keyword
            placeholder="搜索关联的上游合同(编号/名称)"
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
        
        <el-form-item label="合同名称" prop="contract_name">
          <el-input v-model="form.contract_name" placeholder="请输入合同名称" />
        </el-form-item>
        
        <el-form-item label="甲方(我们)" prop="party_a_name">
          <el-input v-model="form.party_a_name" placeholder="请输入甲方名称" />
        </el-form-item>

        <el-form-item label="乙方名称" prop="party_b_name">
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

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期" prop="start_date">
              <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期" prop="end_date">
              <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="合同类别" prop="category">
          <el-input v-model="form.category" placeholder="例如：材料采购、分包施工" />
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
import { useRouter } from 'vue-router'
import { getContracts, createContract, updateContract, deleteContract } from '@/api/contractManagement'
import { getContracts as getUpstreamContracts, getContractSummary } from '@/api/contractUpstream'
import { ElMessage, ElMessageBox } from 'element-plus'
import SmartAutocomplete from '@/components/SmartAutocomplete.vue'

const router = useRouter()
const loading = ref(false)
const total = ref(0)
const contractList = ref([])
const isMobile = ref(false)

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
  start_date: '',
  end_date: '',
  category: '',
  notes: '',
  status: '进行中'
})

const rules = {
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

const getStatusType = (status) => {
  const map = {
    '进行中': 'primary',
    '已完成': 'success',
    '已终止': 'info',
    '待审核': 'warning'
  }
  return map[status] || ''
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

// Form handling
const resetForm = () => {
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
  form.start_date = ''
  form.end_date = ''
  form.category = ''
  form.notes = ''
  form.status = '进行中'
  
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
        await updateContract(form.id, form)
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
