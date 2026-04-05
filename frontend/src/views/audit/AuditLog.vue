<template>
  <div class="audit-log">
    <AppSectionCard>
      <template #header>日志筛选</template>
      <AppFilterBar>
        <el-select v-model="queryParams.action" placeholder="操作类型" clearable>
          <el-option v-for="item in actionOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="queryParams.resource_type" placeholder="资源类型" clearable>
          <el-option v-for="item in resourceOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <AppRangeField
          v-model="dateRange"
          class="filter-control--time"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
        />
        <el-input v-model="queryParams.keyword" class="filter-control--search" placeholder="用户名 / 描述 / 资源名称" clearable @keyup.enter="handleQuery" />
        <template #actions>
        <el-button type="primary" @click="handleQuery">查询</el-button>
        <el-button @click="resetQuery">重置</el-button>
        </template>
      </AppFilterBar>
    </AppSectionCard>

    <AppSectionCard>
      <template #header>操作记录</template>

      <AppEmptyState
        v-if="!loading && !logList.length"
        title="暂无审计日志"
        description="当前筛选条件下没有可展示的操作记录。"
      />

      <template v-else-if="isMobile">
        <div v-loading="loading" class="audit-card-list">
          <article v-for="log in logList" :key="log.id" class="audit-card">
            <div class="audit-card__header">
              <div>
                <div class="audit-card__time">{{ formatDateTime(log.created_at) }}</div>
                <div class="audit-card__user">{{ log.username || '-' }}</div>
              </div>
              <el-tag :type="getActionTagType(log.action)" effect="plain">{{ getActionLabel(log.action) }}</el-tag>
            </div>

            <div class="audit-card__body">
              <div class="audit-field">
                <span class="audit-field__label">资源</span>
                <span class="audit-field__value">{{ log.resource_type }} / {{ log.resource_name || '-' }}</span>
              </div>
              <div class="audit-field">
                <span class="audit-field__label">描述</span>
                <span class="audit-field__value">{{ log.description || '-' }}</span>
              </div>
              <div class="audit-field">
                <span class="audit-field__label">IP</span>
                <span class="audit-field__value">{{ log.ip_address || '-' }}</span>
              </div>
            </div>

            <div class="audit-card__footer">
              <el-button
                v-if="log.old_values || log.new_values"
                link
                type="primary"
                size="small"
                @click="showDetail(log)"
              >
                查看详情
              </el-button>
              <span v-else class="audit-card__placeholder">无变更快照</span>
            </div>
          </article>

          <div class="pagination-container pagination-container--mobile">
            <el-pagination
              v-model:current-page="queryParams.page"
              v-model:page-size="queryParams.page_size"
              layout="prev, pager, next"
              :total="total"
              small
              @current-change="fetchLogs"
            />
          </div>
        </div>
      </template>

      <template v-else>
        <AppDataTable>
          <el-table v-loading="loading" :data="logList" border>
            <el-table-column prop="id" label="ID" width="80" align="center" />
            <el-table-column prop="created_at" label="时间" width="190">
              <template #default="scope">
                {{ formatDateTime(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="username" label="用户" width="120" />
            <el-table-column prop="action" label="操作" width="110" align="center">
              <template #default="scope">
                <el-tag :type="getActionTagType(scope.row.action)" effect="plain">
                  {{ getActionLabel(scope.row.action) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="resource_type" label="资源类型" width="120" align="center" />
            <el-table-column prop="resource_name" label="资源名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="description" label="描述" min-width="240" show-overflow-tooltip />
            <el-table-column prop="ip_address" label="IP地址" width="140" />
            <el-table-column label="操作" width="100" align="center">
              <template #default="scope">
                <el-button
                  v-if="scope.row.old_values || scope.row.new_values"
                  link
                  type="primary"
                  size="small"
                  @click="showDetail(scope.row)"
                >
                  详情
                </el-button>
                <span v-else class="text-gray">-</span>
              </template>
            </el-table-column>
          </el-table>

          <template #footer>
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
          </template>
        </AppDataTable>
      </template>
    </AppSectionCard>

    <el-dialog title="操作详情" v-model="detailVisible" :width="isMobile ? '92%' : '720px'">
      <div class="audit-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="操作时间">{{ formatDateTime(currentLog.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="用户">{{ currentLog.username }}</el-descriptions-item>
          <el-descriptions-item label="操作类型">{{ getActionLabel(currentLog.action) }}</el-descriptions-item>
          <el-descriptions-item label="资源类型">{{ currentLog.resource_type }}</el-descriptions-item>
          <el-descriptions-item label="资源名称">{{ currentLog.resource_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ currentLog.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="IP地址">{{ currentLog.ip_address || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="currentLog.old_values" class="audit-detail__block">
          <h4>修改前数据</h4>
          <el-input type="textarea" :value="formatJson(currentLog.old_values)" :rows="6" readonly />
        </div>

        <div v-if="currentLog.new_values" class="audit-detail__block">
          <h4>修改后数据</h4>
          <el-input type="textarea" :value="formatJson(currentLog.new_values)" :rows="6" readonly />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppSectionCard from '@/components/ui/AppSectionCard.vue'
import AppFilterBar from '@/components/ui/AppFilterBar.vue'
import AppDataTable from '@/components/ui/AppDataTable.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import AppRangeField from '@/components/ui/AppRangeField.vue'
import request from '@/utils/request'
import { useDevice } from '@/composables/useDevice'

const { isMobile } = useDevice()

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
  { value: 'DOWNLOAD', label: '下载' }
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
  { value: '系统', label: '系统' }
]

const actionLabelMap = {
  LOGIN: '登录',
  LOGOUT: '登出',
  CHANGE_PASSWORD: '改密',
  CREATE: '新增',
  UPDATE: '修改',
  DELETE: '删除',
  VIEW: '查看',
  EXPORT: '导出',
  IMPORT: '导入',
  UPLOAD: '上传',
  DOWNLOAD: '下载',
  APPROVE: '审批',
  REJECT: '驳回'
}

const getActionLabel = action => actionLabelMap[action] || action

const getActionTagType = action => {
  const typeMap = {
    LOGIN: 'success',
    LOGOUT: 'info',
    CREATE: 'primary',
    UPDATE: 'warning',
    DELETE: 'danger',
    EXPORT: '',
    UPLOAD: ''
  }
  return typeMap[action] || ''
}

const formatDateTime = dt => {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN')
}

const formatJson = jsonStr => {
  try {
    return JSON.stringify(JSON.parse(jsonStr), null, 2)
  } catch {
    return jsonStr
  }
}

const fetchLogs = async () => {
  loading.value = true
  try {
    if (dateRange.value && dateRange.value.length === 2) {
      queryParams.start_date = dateRange.value[0]
      queryParams.end_date = dateRange.value[1]
    } else {
      queryParams.start_date = ''
      queryParams.end_date = ''
    }

    const params = { ...queryParams }
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

const showDetail = row => {
  currentLog.value = row
  detailVisible.value = true
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped lang="scss">
.audit-log {
  display: grid;
  gap: 20px;
}

.audit-card-list {
  display: grid;
  gap: 12px;
}

.audit-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-panel);
  box-shadow: var(--shadow-soft);
}

.audit-card__header,
.audit-card__footer,
.audit-field {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.audit-card__time {
  font-size: 13px;
  color: var(--text-muted);
}

.audit-card__user {
  margin-top: 4px;
  font-weight: 700;
  color: var(--text-primary);
}

.audit-card__body {
  display: grid;
  gap: 10px;
}

.audit-field__label {
  min-width: 42px;
  color: var(--text-muted);
}

.audit-field__value {
  flex: 1;
  text-align: right;
  color: var(--text-secondary);
  word-break: break-word;
}

.audit-card__placeholder,
.text-gray {
  color: var(--text-muted);
}

.audit-detail {
  display: grid;
  gap: 20px;
}

.audit-detail__block {
  display: grid;
  gap: 10px;
}

.audit-detail__block h4 {
  margin: 0;
  font-size: 14px;
  color: var(--text-primary);
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  width: 100%;
}

.pagination-container--mobile {
  justify-content: center;
  margin-top: 8px;
}

@media (max-width: 767px) {
  .audit-card__header,
  .audit-card__footer,
  .audit-field {
    flex-direction: column;
  }

  .audit-field__value {
    text-align: left;
  }
}
</style>
