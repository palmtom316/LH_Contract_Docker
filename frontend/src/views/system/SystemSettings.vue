
<template>
  <div class="system-settings-page">
    <AppWorkspacePanel panel-class="system-settings-panel">
    <el-tabs v-model="activeTab" class="system-settings-tabs app-tabs--line">
      <el-tab-pane label="系统配置" name="config">
        <AppSectionCard class="system-settings-card">
            <template #header>基础设置</template>
            <el-form :model="configForm" label-width="120px">
                <el-form-item label="系统名称(第一行)">
                    <el-input v-model="configForm.system_name" placeholder="例如：合同管理系统" />
                </el-form-item>
                <el-form-item label="系统名称(第二行)">
                    <el-input v-model="configForm.system_name_line_2" placeholder="例如：合同管理系统" />
                </el-form-item>
                <el-form-item label="系统Logo">
                    <el-upload
                        class="avatar-uploader"
                        action="/api/v1/system/logo"
                        :show-file-list="false"
                        :on-success="handleLogoSuccess"
                        :headers="headers"
                        name="file"
                    >
                        <img v-if="configForm.system_logo" :src="configForm.system_logo" class="avatar" />
                        <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
                    </el-upload>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="saveConfig">保存配置</el-button>
                </el-form-item>
            </el-form>
        </AppSectionCard>
      </el-tab-pane>

      <el-tab-pane label="数据字典" name="dict">
        <AppSectionCard class="system-settings-card">
        <template #header>数据字典</template>
        <template #actions>
          <el-button type="primary" plain :icon="Download" @click="handleExportDict">导出</el-button>
          <el-upload
            class="upload-inline"
            action="#"
            :http-request="handleImportDict"
            :show-file-list="false"
            accept=".xlsx,.xls"
          >
            <el-button :icon="Upload">导入</el-button>
          </el-upload>
        </template>
        
        <div class="dict-layout">
            <aside class="dict-layout__aside">
                <el-menu :default-active="activeCategory" class="dict-menu" @select="handleSelectCategory">
                    <el-menu-item index="contract_category">上游合同类别</el-menu-item>
                    <el-menu-item index="project_category">上游合同公司分类</el-menu-item>
                    <el-menu-item index="pricing_mode">上游合同计价模式</el-menu-item>
                    <el-menu-item index="receivable_category">上游应收款类别</el-menu-item>
                    <el-menu-item index="management_mode">上游合同管理模式</el-menu-item>
                    <el-menu-item index="downstream_contract_category">下游合同类别</el-menu-item>
                    <el-menu-item index="management_contract_category">管理合同类别</el-menu-item>
                    <el-menu-item index="downstream_pricing_mode">下游及管理合同计价模式</el-menu-item>
                    <el-menu-item index="payment_category">下游及管理合同应付款类别</el-menu-item>
                    <el-menu-item index="expense_type">无合同费用类别</el-menu-item>
                </el-menu>
            </aside>
            <div class="dict-layout__main">
                <div class="dict-toolbar">
                    <el-button type="primary" :icon="Plus" @click="handleCreateOption">新增选项</el-button>
                    <span class="dict-current-category">{{ categoryLabels[activeCategory] }}</span>
                </div>
                
                <el-table :data="currentOptions" v-loading="loading" border class="dict-table">
                    <el-table-column prop="label" label="显示名称" />
                    <el-table-column prop="value" label="存值" />
                    <el-table-column prop="sort_order" label="排序" width="80" />
                    <el-table-column label="操作" width="180">
                        <template #default="scope">
                            <el-button size="small" @click="handleEditOption(scope.row)">编辑</el-button>
                            <el-button size="small" type="danger" @click="handleDeleteOption(scope.row)">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </div>
        </div>
        </AppSectionCard>
      </el-tab-pane>
    </el-tabs>
    </AppWorkspacePanel>

    <!-- Option Dialog -->
    <el-dialog v-model="dialogVisible" :title="dialogType==='create'?'新增选项':'编辑选项'">
        <el-form :model="optionForm" label-width="100px">
            <el-form-item label="显示名称">
                <el-input v-model="optionForm.label" />
            </el-form-item>
            <el-form-item label="存储值">
                 <el-input v-model="optionForm.value" :disabled="dialogType==='edit' && false" />
            </el-form-item>
            <el-form-item label="排序">
                <el-input-number v-model="optionForm.sort_order" :min="0" />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitOption">确定</el-button>
        </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useSystemStore } from '@/stores/system'
import { Plus, Download, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import AppSectionCard from '@/components/ui/AppSectionCard.vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'

const activeTab = ref('config')
const systemStore = useSystemStore()

// Config Logic
const configForm = ref({
    system_name: '',
    system_name_line_2: '',
    system_logo: ''
})
// Headers for upload (if Auth needed, add Authorization header here)
const headers = computed(() => {
    const token = localStorage.getItem('token') // Assuming stored here
    return token ? { Authorization: `Bearer ${token}` } : {}
})

function handleLogoSuccess(res) {
    configForm.value.system_logo = res?.path || ''
    ElMessage.success('Logo uploaded')
}

async function saveConfig() {
    await systemStore.updateConfig(configForm.value)
    ElMessage.success('配置已保存')
    // Maybe refresh page title immediately? 
    document.title = configForm.value.system_name
}

// Dictionary Logic
const activeCategory = ref('contract_category')
const categoryLabels = {
    contract_category: '上游合同类别',
    project_category: '上游合同公司分类',
    pricing_mode: '上游合同计价模式',
    receivable_category: '上游应收款类别',
    management_mode: '上游合同管理模式',
    downstream_contract_category: '下游合同类别',
    management_contract_category: '管理合同类别',
    downstream_pricing_mode: '下游及管理合同计价模式',
    payment_category: '下游及管理合同应付款类别',
    expense_type: '无合同费用类别'
}

const loading = ref(false)
const currentOptions = ref([])

const dialogVisible = ref(false)
const dialogType = ref('create')
const optionForm = reactive({
    id: null,
    label: '',
    value: '',
    sort_order: 0,
    category: ''
})

async function loadOptions() {
    loading.value = true
    currentOptions.value = await systemStore.fetchOptions(activeCategory.value)
    loading.value = false
}

function handleSelectCategory(index) {
    activeCategory.value = index
    loadOptions()
}

function handleCreateOption() {
    dialogType.value = 'create'
    optionForm.id = null
    optionForm.label = ''
    optionForm.value = ''
    optionForm.sort_order = 0
    optionForm.category = activeCategory.value
    dialogVisible.value = true
}

function handleEditOption(row) {
    dialogType.value = 'edit'
    optionForm.id = row.id
    optionForm.label = row.label
    optionForm.value = row.value
    optionForm.sort_order = row.sort_order
    optionForm.category = row.category
    dialogVisible.value = true
}

async function handleDeleteOption(row) {
    try {
        await ElMessageBox.confirm('确定删除该选项? 如果正在使用可能会导致数据显示问题', '警告', { type: 'warning' })
        await systemStore.deleteOption(row.id, activeCategory.value)
        loadOptions()
        ElMessage.success('删除成功')
    } catch(e) { /* cancel */ }
}

async function submitOption() {
    try {
        if (dialogType.value === 'create') {
            await systemStore.addOption(optionForm)
        } else {
            await systemStore.updateOption(optionForm.id, optionForm, activeCategory.value)
        }
        dialogVisible.value = false
        loadOptions()
        ElMessage.success('操作成功')
    } catch(e) {
        ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
    }
}

// Export dictionary to Excel
async function handleExportDict() {
    try {
        const response = await request({
            url: '/system/options/export',
            method: 'get',
            responseType: 'blob'
        })
        
        // Create download link
        const blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `数据字典_${new Date().toISOString().slice(0,10)}.xlsx`
        link.click()
        window.URL.revokeObjectURL(url)
        ElMessage.success('导出成功')
    } catch(e) {
        ElMessage.error('导出失败: ' + (e.response?.data?.detail || e.message))
    }
}

// Import dictionary from Excel
async function handleImportDict(options) {
    try {
        const formData = new FormData()
        formData.append('file', options.file)
        
        const response = await request({
            url: '/system/options/import',
            method: 'post',
            data: formData,
            headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        ElMessage.success(`导入成功: 新增 ${response.imported} 条, 更新 ${response.updated} 条, 跳过 ${response.skipped} 条`)
        loadOptions()
    } catch(e) {
        ElMessage.error('导入失败: ' + (e.response?.data?.detail || e.message))
    }
}

onMounted(async () => {
    await systemStore.fetchConfig()
    configForm.value = { ...systemStore.config }
    loadOptions()
})
</script>

<style scoped>
.system-settings-page {
  display: grid;
  gap: var(--space-5);
}

.system-settings-panel {
  gap: var(--space-4);
}

.system-settings-card {
  gap: var(--space-4);
}

.system-settings-tabs :deep(.el-tabs__header) {
  margin-bottom: var(--space-5);
}

.upload-inline {
  display: inline-flex;
}

.dict-layout {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  min-height: 560px;
  border: 1px solid var(--border-subtle);
  border-radius: calc(var(--radius-lg) + 2px);
  overflow: hidden;
  background: var(--surface-panel);
  box-shadow: var(--shadow-soft);
}

.dict-layout__aside {
  border-right: 1px solid var(--border-subtle);
  background: color-mix(in srgb, var(--surface-panel-muted) 70%, var(--surface-panel) 30%);
}

.dict-layout__main {
  display: grid;
  align-content: start;
  gap: 16px;
  padding: 18px;
  min-width: 0;
}

.dict-menu {
  border-right: 0;
  background: transparent;
}

.dict-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.dict-current-category {
  font-size: 13px;
  color: var(--text-muted);
}

.dict-table {
  width: 100%;
}

.dict-table :deep(.el-table__cell) {
  padding-top: 10px;
  padding-bottom: 10px;
}

.avatar-uploader .avatar {
  width: 178px;
  height: 178px;
  display: block;
}

@media (max-width: 900px) {
  .dict-layout {
    grid-template-columns: 1fr;
  }

  .dict-layout__aside {
    border-right: 0;
    border-bottom: 1px solid var(--border-subtle);
  }
}
</style>
