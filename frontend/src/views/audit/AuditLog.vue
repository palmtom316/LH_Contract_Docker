<template>
  <div class="app-container">
    <el-card class="filter-container" shadow="never">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="操作类型">
          <el-select v-model="queryParams.action" placeholder="全部" clearable style="width: 120px">
            <el-option 
              v-for="item in actionOptions" 
              :key="item.value" 
              :label="item.label" 
              :value="item.value" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="资源类型">
          <el-select v-model="queryParams.resource_type" placeholder="全部" clearable style="width: 120px">
            <el-option 
              v-for="item in resourceOptions" 
              :key="item.value" 
              :label="item.label" 
              :value="item.value" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input 
            v-model="queryParams.keyword" 
            placeholder="用户名/描述" 
            clearable 
            style="width: 180px"
            @keyup.enter="handleQuery"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="always">
      <el-table v-loading="loading" :data="logList" border style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户" width="100" />
        <el-table-column prop="action" label="操作" width="100" align="center">
          <template #default="scope">
            <el-tag :type="getActionTagType(scope.row.action)" size="small">
              {{ getActionLabel(scope.row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resource_type" label="资源类型" width="120" align="center" />
        <el-table-column prop="resource_name" label="资源名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP地址" width="130" />
        <el-table-column label="操作" width="80" align="center">
          <template #default="scope">
            <el-button 
              v-if="scope.row.old_values || scope.row.new_values" 
              link 
              type="primary" 
              size="small" 
              @click="showDetail(scope.row)"
            >详情</el-button>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :page-sizes="[20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchLogs"
          @current-change="fetchLogs"
        />
      </div>
    </el-card>

    <!-- Detail Dialog -->
    <el-dialog title="操作详情" v-model="detailVisible" width="600px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="操作时间">{{ formatDateTime(currentLog.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="用户">{{ currentLog.username }}</el-descriptions-item>
        <el-descriptions-item label="操作类型">{{ getActionLabel(currentLog.action) }}</el-descriptions-item>
        <el-descriptions-item label="资源类型">{{ currentLog.resource_type }}</el-descriptions-item>
        <el-descriptions-item label="资源名称">{{ currentLog.resource_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="描述">{{ currentLog.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentLog.ip_address || '-' }}</el-descriptions-item>
      </el-descriptions>
      
      <div v-if="currentLog.old_values" style="margin-top: 20px">
        <h4>修改前数据：</h4>
        <el-input 
          type="textarea" 
          :value="formatJson(currentLog.old_values)" 
          :rows="6" 
          readonly 
        />
      </div>
      
      <div v-if="currentLog.new_values" style="margin-top: 20px">
        <h4>修改后数据：</h4>
        <el-input 
          type="textarea" 
          :value="formatJson(currentLog.new_values)" 
          :rows="6" 
          readonly 
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const loading = ref(false)
const logList = ref([])
const total = ref(0)
const dateRange = ref(null)
const detailVisible = ref(false)
const currentLog = ref({})

const queryParams = reactive({
  page: 1,
  page_size: 20,
  action: '',
  resource_type: '',
  keyword: '',
  start_date: '',
  end_date: ''
})

const actionOptions = [
  { value: 'LOGIN', label: '登录' },
  { value: 'LOGOUT', label: '登出' },
  { value: 'CHANGE_PASSWORD', label: '修改密码' },
  { value: 'CREATE', label: '新增' },
  { value: 'UPDATE', label: '修改' },
  { value: 'DELETE', label: '删除' },
  { value: 'EXPORT', label: '导出' },
  { value: 'UPLOAD', label: '上传' },
  { value: 'DOWNLOAD', label: '下载' },
]

const resourceOptions = [
  { value: '用户', label: '用户' },
  { value: '上游合同', label: '上游合同' },
  { value: '下游合同', label: '下游合同' },
  { value: '管理合同', label: '管理合同' },
  { value: '无合同费用', label: '无合同费用' },
  { value: '应收款', label: '应收款' },
  { value: '应付款', label: '应付款' },
  { value: '挂账', label: '挂账' },
  { value: '付款', label: '付款' },
  { value: '回款', label: '回款' },
  { value: '结算', label: '结算' },
  { value: '文件', label: '文件' },
  { value: '系统', label: '系统' },
]

const actionLabelMap = {
  'LOGIN': '登录',
  'LOGOUT': '登出',
  'CHANGE_PASSWORD': '改密',
  'CREATE': '新增',
  'UPDATE': '修改',
  'DELETE': '删除',
  'VIEW': '查看',
  'EXPORT': '导出',
  'IMPORT': '导入',
  'UPLOAD': '上传',
  'DOWNLOAD': '下载',
  'APPROVE': '审批',
  'REJECT': '驳回',
}

const getActionLabel = (action) => actionLabelMap[action] || action

const getActionTagType = (action) => {
  const typeMap = {
    'LOGIN': 'success',
    'LOGOUT': 'info',
    'CREATE': 'primary',
    'UPDATE': 'warning',
    'DELETE': 'danger',
    'EXPORT': '',
    'UPLOAD': '',
  }
  return typeMap[action] || ''
}

const formatDateTime = (dt) => {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN')
}

const formatJson = (jsonStr) => {
  try {
    return JSON.stringify(JSON.parse(jsonStr), null, 2)
  } catch {
    return jsonStr
  }
}

const fetchLogs = async () => {
  loading.value = true
  try {
    // Update date params from range picker
    if (dateRange.value && dateRange.value.length === 2) {
      queryParams.start_date = dateRange.value[0]
      queryParams.end_date = dateRange.value[1]
    } else {
      queryParams.start_date = ''
      queryParams.end_date = ''
    }

    const params = { ...queryParams }
    // Remove empty params
    Object.keys(params).forEach(key => {
      if (!params[key]) delete params[key]
    })

    const res = await request({
      url: '/audit/',
      method: 'get',
      params
    })
    logList.value = res.items
    total.value = res.total
  } catch (e) {
    ElMessage.error('获取审计日志失败')
  } finally {
    loading.value = false
  }
}

const handleQuery = () => {
  queryParams.page = 1
  fetchLogs()
}

const resetQuery = () => {
  queryParams.page = 1
  queryParams.action = ''
  queryParams.resource_type = ''
  queryParams.keyword = ''
  dateRange.value = null
  fetchLogs()
}

const showDetail = (row) => {
  currentLog.value = row
  detailVisible.value = true
}

onMounted(() => {
  fetchLogs()
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

.text-gray {
  color: #999;
}
</style>
