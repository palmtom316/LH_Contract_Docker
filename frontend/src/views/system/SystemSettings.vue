
<template>
  <div class="app-container">
    <el-tabs v-model="activeTab" class="demo-tabs app-tabs--line">
      <el-tab-pane label="系统配置" name="config">
        <el-card>
            <template #header>
                <span>基础设置</span>
            </template>
            <el-form :model="configForm" label-width="120px">
                <el-form-item label="系统名称(第一行)">
                    <el-input v-model="configForm.system_name" placeholder="例如：蓝海" />
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
                    <div class="el-upload__tip">建议使用 PNG 格式，点击图片替换</div>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="saveConfig">保存配置</el-button>
                </el-form-item>
            </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="数据字典" name="dict">
        <!-- Global actions for all categories -->
        <div class="dict-global-actions" style="margin-bottom: 15px;">
          <el-button type="success" :icon="Download" @click="handleExportDict">导出全部字典Excel</el-button>
          <el-upload
            class="upload-demo"
            style="display: inline-block; margin-left: 10px;"
            action="#"
            :http-request="handleImportDict"
            :show-file-list="false"
            accept=".xlsx,.xls"
          >
            <el-button type="warning" :icon="Upload">导入Excel</el-button>
          </el-upload>
          <span style="margin-left: 20px; color: #999; font-size: 12px;">导入导出包含所有分类的数据字典</span>
        </div>
        
        <el-container style="height: 550px; border: 1px solid #eee">
            <el-aside width="220px" style="background-color: #fcfcfc">
                <el-menu :default-active="activeCategory" @select="handleSelectCategory">
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
            </el-aside>
            <el-main>
                <div class="filter-container">
                    <el-button type="primary" :icon="Plus" @click="handleCreateOption">新增选项</el-button>
                    <span style="margin-left:20px; color:#999">当前分类: {{ categoryLabels[activeCategory] }}</span>
                </div>
                
                <el-table :data="currentOptions" v-loading="loading" border style="width: 100%; margin-top: 10px;">
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
            </el-main>
        </el-container>
      </el-tab-pane>
    </el-tabs>

    <!-- Option Dialog -->
    <el-dialog v-model="dialogVisible" :title="dialogType==='create'?'新增选项':'编辑选项'">
        <el-form :model="optionForm" label-width="100px">
            <el-form-item label="显示名称">
                <el-input v-model="optionForm.label" />
            </el-form-item>
            <el-form-item label="存储值">
                 <el-input v-model="optionForm.value" :disabled="dialogType==='edit' && false" />
                 <div style="font-size:12px;color:#999">建议与显示名称一致</div>
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
    configForm.value.system_logo = res.path
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
.avatar-uploader .avatar {
  width: 178px;
  height: 178px;
  display: block;
}
</style>
