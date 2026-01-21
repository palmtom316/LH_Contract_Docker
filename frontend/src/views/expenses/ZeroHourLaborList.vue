<template>
  <div class="app-container">
    <el-card class="filter-container" shadow="never">
      <el-form :inline="!isMobile" :model="queryParams" class="demo-form-inline" :label-position="isMobile ? 'top' : 'right'">
        <el-form-item label="用工日期">
          <el-date-picker
            v-model="queryParams.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            :style="{ width: isMobile ? '100%' : '240px' }"
            clearable
          />
        </el-form-item>
        <el-form-item label="用工归属">
          <el-select v-model="queryParams.attribution" placeholder="全部" clearable :style="{ width: isMobile ? '100%' : '140px' }">
            <el-option label="公司用工" value="COMPANY" />
            <el-option label="项目用工" value="PROJECT" />
          </el-select>
        </el-form-item>
        <el-form-item label="上游合同">
          <el-select
            v-model="queryParams.upstream_contract_id"
            placeholder="请输入关键词搜索"
            filterable
            remote
            clearable
            :remote-method="searchUpstreamContractsForFilter"
            :loading="loadingContracts"
            :style="{ width: isMobile ? '100%' : '200px' }"
          >
            <el-option
              v-for="item in filterUpstreamContracts"
              :key="item.id"
              :label="item.contract_name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
            <el-input v-model="queryParams.keyword" placeholder="派工单位/材料名称" clearable :style="{ width: isMobile ? '100%' : '180px' }" @keyup.enter="handleQuery" />
        </el-form-item>
        <el-form-item>
          <div class="filter-actions" :class="{ 'mobile-actions': isMobile }">
            <el-button type="primary" :icon="Search" @click="handleQuery">搜索</el-button>
            <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
            
            <template v-if="!isMobile">
              <el-button type="success" :icon="Plus" @click="handleAdd">新增零星用工</el-button>
              <el-button type="warning" :icon="Download" @click="handleExport" :loading="exporting">导出Excel</el-button>
            </template>
            
            <!-- Mobile Menu -->
            <el-dropdown v-if="isMobile" trigger="click" class="action-item">
              <el-button type="info" :icon="More" circle />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleAdd"><el-icon><Plus /></el-icon> 新增用工</el-dropdown-item>
                  <el-dropdown-item @click="handleExport"><el-icon><Download /></el-icon> 导出Excel</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table 
        v-loading="loading" 
        :data="list" 
        style="width: 100%" 
        border
        highlight-current-row
        show-summary
        :summary-method="getSummaries"
        class="custom-footer-table"
    >
        <el-table-column prop="labor_date" label="用工时间" width="120" sortable />
        <el-table-column label="归属" width="100">
            <template #default="{ row }">
                <el-tag :type="row.attribution === 'PROJECT' ? 'warning' : 'info'">
                    {{ row.attribution === 'PROJECT' ? '项目用工' : '公司用工' }}
                </el-tag>
            </template>
        </el-table-column>
        <el-table-column label="上游合同" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">
                {{ row.upstream_contract ? row.upstream_contract.contract_name : '-' }}
            </template>
        </el-table-column>
        <el-table-column prop="dispatch_unit" label="派工单位" min-width="120" show-overflow-tooltip />

        <el-table-column label="派工单" width="80" align="center">
            <template #default="{ row }">
                <el-button 
                    v-if="row.dispatch_file_path" 
                    link 
                    type="primary" 
                    size="small" 
                    :icon="Document" 
                    @click="viewFile(row.dispatch_file_path)"
                >查看</el-button>
                <span v-else class="text-gray">-</span>
            </template>
        </el-table-column>

        <el-table-column label="审批状态" width="100">
            <template #default="{ row }">
                <el-tag :type="getApprovalStatusType(row.approval_status)" v-if="row.approval_status">
                    {{ formatApprovalStatus(row.approval_status) }}
                </el-tag>
                <span v-else>-</span>
            </template>
        </el-table-column>
        <el-table-column label="审批单" width="100" align="center">
            <template #default="{ row }">
                 <el-button 
                    v-if="row.approval_pdf_path" 
                    link 
                    type="primary" 
                    size="small" 
                    :icon="Document" 
                    @click="viewFile(row.approval_pdf_path)"
                >查看</el-button>
                <span v-else class="text-gray">-</span>
            </template>
        </el-table-column>


        <el-table-column label="用工费用" width="120" align="right">
            <template #default="{ row }">¥ {{ formatMoney(row.labor_price_total) }}</template>
        </el-table-column>
        <el-table-column label="用车费用" width="120" align="right">
            <template #default="{ row }">¥ {{ formatMoney(row.vehicle_price_total) }}</template>
        </el-table-column>
        <el-table-column label="材料费用" width="120" align="right">
            <template #default="{ row }">¥ {{ formatMoney(row.material_price_total) }}</template>
        </el-table-column>
        <el-table-column label="总计" width="120" align="right" prop="total_amount">
            <template #default="{ row }">
                <span style="color: #F56C6C; font-weight: bold;">¥ {{ formatMoney(row.total_amount) }}</span>
            </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
                <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
            </template>
        </el-table-column>
    </el-table>

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

    <!-- Dialog -->
    <el-dialog
        :title="dialog.title"
        v-model="dialog.visible"
        width="800px"
        append-to-body
        :close-on-click-modal="false"
    >
        <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
            <el-row :gutter="20">
                <el-col :span="12">
                    <el-form-item label="用工归属" prop="attribution">
                        <el-select v-model="form.attribution" style="width: 100%" placeholder="请选择">
                            <el-option label="公司用工" value="COMPANY" />
                            <el-option label="项目用工" value="PROJECT" />
                        </el-select>
                    </el-form-item>
                </el-col>
                <el-col :span="12">
                    <el-form-item label="用工时间" prop="labor_date">
                        <el-date-picker v-model="form.labor_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
                    </el-form-item>
                </el-col>
            </el-row>

            <!-- Approval Status (Read Only) -->
            <div v-if="form.approval_status && form.approval_status !== 'DRAFT'" style="margin-bottom: 18px; padding: 10px; background-color: #f0f9eb; border-radius: 4px;">
                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item label="审批状态" style="margin-bottom: 0;">
                             <el-tag :type="getApprovalStatusType(form.approval_status)">
                                {{ formatApprovalStatus(form.approval_status) }}
                            </el-tag>
                        </el-form-item>
                    </el-col>
                    <el-col :span="12">
                        <el-form-item label="审批单" style="margin-bottom: 0;">
                             <el-button 
                                v-if="form.approval_pdf_path" 
                                link 
                                type="primary" 
                                :icon="Document" 
                                @click="viewFile(form.approval_pdf_path)"
                            >查看审批单</el-button>
                             <span v-else>暂无</span>
                        </el-form-item>
                    </el-col>
                </el-row>
            </div>

            <!-- Manually Bind Feishu Instance (Optional) -->
            <el-form-item label="飞书审批实例" prop="feishu_instance_code">
                <el-input v-model="form.feishu_instance_code" placeholder="手动绑定审批实例ID (Instance Code)" clearable>
                     <template #append>
                        <el-button :icon="item" @click="viewFile(form.approval_pdf_path)" v-if="form.approval_pdf_path" />
                        <span v-else>可选</span>
                    </template>
                </el-input>
                <div style="font-size: 12px; color: #909399; line-height: 1.2; margin-top: 4px;">
                    用于关联飞书审批流程。若为空，则无法通过Webhook自动同步审批状态。
                </div>
            </el-form-item>

            <div v-if="form.attribution === 'PROJECT'" style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin-bottom: 18px;">
                 <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item label="关联上游合同" prop="upstream_contract_id">
                             <el-select
                                v-model="form.upstream_contract_id"
                                filterable
                                remote
                                clearable
                                placeholder="请输入搜索"
                                :remote-method="searchUpstreamContracts"
                                :loading="loadingContracts"
                                style="width: 100%"
                              >
                                <el-option
                                  v-for="item in upstreamContracts"
                                  :key="item.id"
                                  :label="item.contract_name"
                                  :value="item.id"
                                />
                              </el-select>
                        </el-form-item>
                    </el-col>
                    <el-col :span="12">
                        <el-form-item label="派工单位名称" prop="dispatch_unit">
                            <el-input v-model="form.dispatch_unit" />
                        </el-form-item>
                    </el-col>
                </el-row>
            </div>

            <!-- Labor Section -->
            <el-divider content-position="left">人工费用</el-divider>
            
            <!-- Skilled Labor (Use specific fields for skilled) -->
            <div style="margin-bottom: 10px; padding: 10px; border: 1px dashed #dcdfe6; border-radius: 4px;">
                <el-row :gutter="20" align="middle">
                    <el-col :span="4">
                        <div style="font-weight: bold; text-align: center;">技工</div>
                    </el-col>
                     <el-col :span="6">
                        <el-form-item label="单价" label-width="50px" style="margin-bottom: 0;">
                            <el-input-number v-model="form.skilled_unit_price" :min="0" :precision="2" :controls="false" style="width: 100%" placeholder="技工单价" />
                        </el-form-item>
                    </el-col>
                    <el-col :span="6">
                        <el-form-item label="数量" label-width="50px" style="margin-bottom: 0;">
                            <el-input-number v-model="form.skilled_quantity" :min="0" :precision="2" :controls="false" style="width: 100%" placeholder="技工数量" />
                        </el-form-item>
                    </el-col>
                    <el-col :span="6">
                        <div style="text-align: right;">合计: ¥ {{ formatMoney(calcSkilledTotal) }}</div>
                    </el-col>
                </el-row>
            </div>
            
             <!-- General Labor (Use specific fields for general) -->
            <div style="margin-bottom: 10px; padding: 10px; border: 1px dashed #dcdfe6; border-radius: 4px;">
                <el-row :gutter="20" align="middle">
                    <el-col :span="4">
                        <div style="font-weight: bold; text-align: center;">普工</div>
                    </el-col>
                     <el-col :span="6">
                        <el-form-item label="单价" label-width="50px" style="margin-bottom: 0;">
                            <el-input-number v-model="form.general_unit_price" :min="0" :precision="2" :controls="false" style="width: 100%" placeholder="普工单价" />
                        </el-form-item>
                    </el-col>
                    <el-col :span="6">
                        <el-form-item label="数量" label-width="50px" style="margin-bottom: 0;">
                            <el-input-number v-model="form.general_quantity" :min="0" :precision="2" :controls="false" style="width: 100%" placeholder="普工数量" />
                        </el-form-item>
                    </el-col>
                    <el-col :span="6">
                        <div style="text-align: right;">合计: ¥ {{ formatMoney(calcGeneralTotal) }}</div>
                    </el-col>
                </el-row>
            </div>

            <!-- Vehicle Section -->
            <el-divider content-position="left">用车费用</el-divider>
            <el-row :gutter="20">
                <el-col :span="8">
                    <el-form-item label="用车单价" prop="vehicle_unit_price">
                        <el-input-number v-model="form.vehicle_unit_price" :min="0" :precision="2" :controls="false" style="width: 100%" />
                    </el-form-item>
                </el-col>
                <el-col :span="8">
                    <el-form-item label="用车数量" prop="vehicle_quantity">
                         <el-input-number v-model="form.vehicle_quantity" :min="0" :precision="2" :controls="false" style="width: 100%" />
                    </el-form-item>
                </el-col>
                <el-col :span="8">
                     <el-form-item label="合计">
                        <span style="font-weight: bold;">{{ formatMoney(calcVehicleTotal) }}</span>
                    </el-form-item>
                </el-col>
            </el-row>

            <!-- Material Section -->
            <el-divider content-position="left">
                零星材料
                <el-button link type="primary" size="small" :icon="Plus" @click="addMaterial">添加材料</el-button>
            </el-divider>
             
             <el-table :data="form.materials" border show-summary :summary-method="getMaterialSummaries" style="width: 100%; margin-bottom: 20px;">
                <el-table-column label="材料名称" min-width="150">
                    <template #default="{ row }">
                        <el-input v-model="row.material_name" placeholder="输入材料名称" />
                    </template>
                </el-table-column>
                <el-table-column label="单位" width="100">
                    <template #default="{ row }">
                        <el-input v-model="row.material_unit" placeholder="T/KG等" />
                    </template>
                </el-table-column>
                <el-table-column label="数量" width="120">
                    <template #default="{ row }">
                        <el-input v-model.number="row.material_quantity" type="number" placeholder="0" @input="updateMaterialTotal(row)" />
                    </template>
                </el-table-column>
                <el-table-column label="单价" width="120">
                    <template #default="{ row }">
                        <el-input v-model.number="row.material_unit_price" type="number" placeholder="0" @input="updateMaterialTotal(row)" />
                    </template>
                </el-table-column>
                <el-table-column label="合价" width="120" align="right" prop="material_price_total">
                    <template #default="{ row }">
                        {{ formatMoney(row.material_price_total) }}
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="60" align="center">
                    <template #default="{ $index }">
                        <el-button link type="danger" :icon="Delete" @click="removeMaterial($index)"></el-button>
                    </template>
                </el-table-column>
             </el-table>

             <!-- Dispatch File Section -->
             <el-divider content-position="left">派工单文件</el-divider>
             <el-row :gutter="20">
                <el-col :span="24">
                    <el-upload
                        v-model:file-list="fileList"
                        action="#"
                        :http-request="handleUploadRequest"
                        :limit="1"
                        :on-exceed="handleExceed"
                        :on-remove="handleRemove"
                        :on-preview="handlePreview"
                        accept=".pdf"
                    >
                        <el-button type="primary" :icon="Upload">上传派工单</el-button>
                         <template #tip>
                          <div class="el-upload__tip">支持 PDF 文件，只能上传一个</div>
                        </template>
                    </el-upload>
                </el-col>
             </el-row>

             <el-divider />
             <div style="text-align: right; font-size: 18px;">
                总金额: <span style="color: #F56C6C; font-weight: bold; font-size: 24px;">¥ {{ formatMoney(grandTotal) }}</span>
             </div>

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
import { ref, reactive, computed, onMounted } from 'vue'
import { getZeroHourLaborList, createZeroHourLabor, updateZeroHourLabor, deleteZeroHourLabor, exportZeroHourLabor } from '@/api/zeroHourLabor'
import { getContracts } from '@/api/contractUpstream'
import { uploadFile } from '@/api/common'
import { formatMoney, getFileUrl } from '@/utils/common'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Document, Plus, Delete, Search, Refresh, Download, More } from '@element-plus/icons-vue'
import { useMobileDetection } from '@/composables/useContractList'

const { isMobile } = useMobileDetection()

const loading = ref(false)
const exporting = ref(false)
const list = ref([])
const total = ref(0)
const upstreamContracts = ref([])
const filterUpstreamContracts = ref([])
const loadingContracts = ref(false)
const fileList = ref([])

// Material Options - In real app fetch from DB, for now hardcoded commonly used ones or empty to start
const materialOptions = ref(['水泥', '沙子', '红砖', '铁丝', '钉子'])

const queryParams = reactive({
    page: 1,
    page_size: 20,
    attribution: '',
    dateRange: null,
    keyword: '',
    upstream_contract_id: null
})

const dialog = reactive({
    title: '',
    visible: false,
    isEdit: false
})

const formRef = ref(null)
// Updated Form Structure to support separate fields temporarily for UI, then merge on submit
const form = reactive({
    id: undefined,
    labor_date: new Date().toISOString().split('T')[0],
    attribution: 'PROJECT',
    upstream_contract_id: undefined,
    dispatch_unit: '',
    dispatch_file_path: '',
    dispatch_file_key: '',
    
    approval_status: '',
    feishu_instance_code: '',
    approval_pdf_path: '',
    
    // Skilled
    skilled_unit_price: 0,
    skilled_quantity: 0,
    
    // General
    general_unit_price: 0,
    general_quantity: 0,

    vehicle_unit_price: 0,
    vehicle_quantity: 0,
    vehicle_price_total: 0,
    
    // Materials List
    materials: [],
    
    total_amount: 0
})

const rules = {
    attribution: [{ required: true, message: '请选择归属', trigger: 'change' }],
    labor_date: [{ required: true, message: '请选择时间', trigger: 'change' }],
}

// Computed for realtime totals
const calcSkilledTotal = computed(() => Number((form.skilled_unit_price || 0) * (form.skilled_quantity || 0)))
const calcGeneralTotal = computed(() => Number((form.general_unit_price || 0) * (form.general_quantity || 0)))

const calcLaborTotal = computed(() => {
    return calcSkilledTotal.value + calcGeneralTotal.value
})
const calcVehicleTotal = computed(() => {
    return Number((form.vehicle_unit_price || 0) * (form.vehicle_quantity || 0))
})
const calcMaterialTotal = computed(() => {
    return form.materials.reduce((sum, item) => sum + (Number(item.material_price_total) || 0), 0)
})
const grandTotal = computed(() => {
    return Number(calcLaborTotal.value + calcVehicleTotal.value + calcMaterialTotal.value)
})

const addMaterial = () => {
    form.materials.push({
        material_name: '',
        material_unit: '',
        material_quantity: 0,
        material_unit_price: 0,
        material_price_total: 0
    })
}

const removeMaterial = (index) => {
    form.materials.splice(index, 1)
}

const getMaterialSummaries = (param) => {
    const { columns, data } = param
    const sums = []
    columns.forEach((column, index) => {
        if (index === 0) {
            sums[index] = '总计'
            return
        }
        if (column.property === 'material_price_total') {
            const values = data.map((item) => Number(item[column.property]))
            if (!values.every((value) => Number.isNaN(value))) {
                const total = values.reduce((prev, curr) => {
                    const value = Number(curr)
                    if (!Number.isNaN(value)) {
                        return prev + value
                    } else {
                        return prev
                    }
                }, 0)
                sums[index] = formatMoney(total)
            } else {
                sums[index] = 'N/A'
            }
        } else {
            sums[index] = ''
        }
    })
    return sums
}

const updateMaterialTotal = (row) => {
    row.material_price_total = Number((row.material_unit_price || 0) * (row.material_quantity || 0))
}

const getList = async () => {
    loading.value = true
    try {
        const params = {
            page: queryParams.page,
            page_size: queryParams.page_size,
            attribution: queryParams.attribution || undefined,
            keyword: queryParams.keyword || undefined,
            upstream_contract_id: queryParams.upstream_contract_id || undefined
        }
        if (queryParams.dateRange && queryParams.dateRange.length === 2) {
            params.start_date = queryParams.dateRange[0]
            params.end_date = queryParams.dateRange[1]
        }
        const res = await getZeroHourLaborList(params)
        list.value = res.items
        total.value = res.total
        
        // Dynamically add used material names to options to improve UX
        // Need to iterate nested materials if list returns them
        const usedMaterials = new Set()
        res.items.forEach(item => {
            if (item.materials && Array.isArray(item.materials)) {
                item.materials.forEach(m => {
                    if (m.material_name) usedMaterials.add(m.material_name)
                })
            } else if (item.material_name) {
                // legacy support for display if needed
                usedMaterials.add(item.material_name)
            }
        })
        
        usedMaterials.forEach(m => {
            if (!materialOptions.value.includes(m)) {
                materialOptions.value.push(m)
            }
        })
        
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
    queryParams.dateRange = null
    queryParams.keyword = ''
    queryParams.upstream_contract_id = null
    filterUpstreamContracts.value = []
    handleQuery()
}

const handleExport = async () => {
    exporting.value = true
    try {
        const params = {
            attribution: queryParams.attribution || undefined,
            keyword: queryParams.keyword || undefined,
            upstream_contract_id: queryParams.upstream_contract_id || undefined
        }
        if (queryParams.dateRange && queryParams.dateRange.length === 2) {
            params.start_date = queryParams.dateRange[0]
            params.end_date = queryParams.dateRange[1]
        }
        
        const blob = await exportZeroHourLabor(params)
        
        // Create download link
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `零星用工_${new Date().toISOString().slice(0,10)}.xlsx`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        ElMessage.success('导出成功')
    } catch (e) {
        ElMessage.error('导出失败')
    } finally {
        exporting.value = false
    }
}

const searchUpstreamContractsForFilter = async (query) => {
    if (query) {
        loadingContracts.value = true
        try {
            const res = await getContracts({ keyword: query, page: 1, page_size: 20 })
            filterUpstreamContracts.value = res.items
        } finally {
            loadingContracts.value = false
        }
    } else {
        filterUpstreamContracts.value = []
    }
}

const resetForm = () => {
    form.id = undefined
    form.labor_date = new Date().toISOString().split('T')[0]
    form.attribution = 'PROJECT'
    form.upstream_contract_id = undefined
    form.dispatch_unit = ''
    form.dispatch_file_path = ''

    form.approval_status = ''
    form.feishu_instance_code = ''
    form.approval_pdf_path = ''
    
    form.skilled_unit_price = 0
    form.skilled_quantity = 0
    form.general_unit_price = 0
    form.general_quantity = 0
    
    form.vehicle_unit_price = 0
    form.vehicle_quantity = 0
    form.vehicle_price_total = 0
    
    form.materials = []
    
    form.total_amount = 0
    
    fileList.value = []
}

const handleAdd = () => {
    resetForm()
    dialog.title = '新增零星用工'
    dialog.isEdit = false
    dialog.visible = true
}

const handleEdit = async (row) => {
    resetForm()
    Object.assign(form, row)
    
    // Support new fields if available, otherwise fall back to legacy
    if (row.skilled_unit_price !== undefined) {
        form.skilled_unit_price = Number(row.skilled_unit_price)
        form.skilled_quantity = Number(row.skilled_quantity)
    } else if (row.labor_type === 'SKILLED') {
        form.skilled_unit_price = Number(row.labor_unit_price)
        form.skilled_quantity = Number(row.labor_quantity)
    }
    
    if (row.general_unit_price !== undefined) {
        form.general_unit_price = Number(row.general_unit_price)
        form.general_quantity = Number(row.general_quantity)
    } else if (row.labor_type === 'GENERAL') {
        form.general_unit_price = Number(row.labor_unit_price)
        form.general_quantity = Number(row.labor_quantity)
    }

    form.vehicle_unit_price = Number(form.vehicle_unit_price)
    form.vehicle_quantity = Number(form.vehicle_quantity)
    
    // Populate materials
    if (row.materials && row.materials.length > 0) {
        form.materials = row.materials.map(m => ({
            ...m,
            material_unit_price: Number(m.material_unit_price),
            material_quantity: Number(m.material_quantity),
            material_price_total: Number(m.material_price_total)
        }))
    } else {
        form.materials = []
    }
    
    if (row.dispatch_file_path) {
        fileList.value = [{ name: '派工单', url: row.dispatch_file_path }]
    }
    
     if (row.upstream_contract_id) {
        if (row.upstream_contract) {
            upstreamContracts.value = [row.upstream_contract]
        }
    }
    
    dialog.title = '编辑零星用工'
    dialog.isEdit = true
    dialog.visible = true
}

const submitForm = async () => {
    if (!formRef.value) return
    
    // Calculate totals for both labor types
    const skilledTotal = (form.skilled_unit_price || 0) * (form.skilled_quantity || 0)
    const generalTotal = (form.general_unit_price || 0) * (form.general_quantity || 0)
    const laborTotal = skilledTotal + generalTotal
    
    // Prepare Submit Data
    const submitData = {
        ...form,
        // Skilled labor
        skilled_unit_price: form.skilled_unit_price || 0,
        skilled_quantity: form.skilled_quantity || 0,
        skilled_price_total: skilledTotal,
        
        // General labor
        general_unit_price: form.general_unit_price || 0,
        general_quantity: form.general_quantity || 0,
        general_price_total: generalTotal,
        
        // Legacy fields (for backward compatibility)
        labor_type: form.skilled_quantity > 0 ? 'SKILLED' : (form.general_quantity > 0 ? 'GENERAL' : 'NONE'),
        labor_unit_price: form.skilled_unit_price || form.general_unit_price || 0,
        labor_quantity: (form.skilled_quantity || 0) + (form.general_quantity || 0),
        labor_price_total: laborTotal,
        
        vehicle_price_total: calcVehicleTotal.value,
        total_amount: laborTotal + calcVehicleTotal.value + calcMaterialTotal.value,
        
        materials: form.materials
    }

    
    await formRef.value.validate(async (valid) => {
        if (valid) {
            if (dialog.isEdit) {
                await updateZeroHourLabor(form.id, submitData)
                ElMessage.success('更新成功')
            } else {
                await createZeroHourLabor(submitData)
                ElMessage.success('创建成功')
            }
            dialog.visible = false
            getList()
        }
    })
}

const handleDelete = (row) => {
    ElMessageBox.confirm('确定要删除吗?', '提示', { type: 'warning' }).then(async () => {
        await deleteZeroHourLabor(row.id)
        ElMessage.success('删除成功')
        getList()
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

const handleUploadRequest = async (option) => {
    try {
        const result = await uploadFile(option.file, 'expenses')
    form.dispatch_file_path = result.path
    if (result.key) form.dispatch_file_key = result.key
    fileList.value = [{ name: option.file.name, url: result.path }]
        ElMessage.success('上传成功')
    } catch (e) {
        ElMessage.error('上传失败')
    }
}

const handleExceed = () => {
    ElMessage.warning('只能上传一个文件')
}

const handleRemove = () => {
    form.dispatch_file_path = ''
    fileList.value = []
}

const handlePreview = (file) => {
     viewFile(file.url)
}

const viewFile = (path) => {
    if (path) {
        const url = getFileUrl(path)
        window.open(url, '_blank')
    }
}

const getApprovalStatusType = (status) => {
    switch (status) {
        case 'APPROVED': return 'success'
        case 'REJECTED': return 'danger'
        case 'PENDING': return 'warning'
        default: return 'info'
    }
}

const formatApprovalStatus = (status) => {
    switch (status) {
        case 'APPROVED': return '已通过'
        case 'REJECTED': return '已拒绝'
        case 'PENDING': return '审批中'
        case 'DRAFT': return '草稿'
        default: return status || '-'
    }
}

const getSummaries = (param) => {
    const { columns, data } = param
    const sums = []
    columns.forEach((column, index) => {
        if (index === 0) {
            sums[index] = '合计'
            return
        }
        if (['labor_price_total', 'vehicle_price_total', 'material_price_total', 'total_amount'].includes(column.property)) {
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
                sums[index] = ''
            }
        } else {
            sums[index] = ''
        }
    })
    return sums
}

onMounted(() => {
    getList()
})
</script>

<style scoped>
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>

<style scoped lang="scss">
.filter-container {
  margin-bottom: 20px;
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
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
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
    white-space: nowrap !important;
}
</style>
