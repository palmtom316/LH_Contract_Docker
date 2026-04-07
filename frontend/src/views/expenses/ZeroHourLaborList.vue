<template>
  <div class="zero-hour-page">
    <AppWorkspacePanel panel-class="zero-hour-panel zero-hour-panel--filters">
      <AppSectionCard class="zero-hour-card-shell">
      <AppFilterBar inline-actions>
        <AppRangeField
          v-model="dateRange"
          class="filter-control--time"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
        />
        <el-select v-model="queryParams.attribution" placeholder="用工归属" clearable>
          <el-option label="公司用工" value="COMPANY" />
          <el-option label="项目用工" value="PROJECT" />
        </el-select>
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
              <span class="contract-option-meta">{{ buildUpstreamOptionMeta(item) }}</span>
            </div>
          </el-option>
        </el-select>
        <el-input v-model="queryParams.keyword" class="filter-control--search" placeholder="派工单位 / 材料名称" clearable @keyup.enter="handleQuery" />
        <template #actions>
        <el-button type="primary" :icon="Search" @click="handleQuery">搜索</el-button>
        <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
        <el-button v-if="!isMobile" type="primary" plain :icon="Plus" @click="handleAdd">新增用工</el-button>
        <el-button v-if="!isMobile" :icon="Download" @click="handleExport" :loading="exporting">导出</el-button>
        <el-dropdown v-if="isMobile" trigger="click" class="action-item">
          <el-button :icon="More" circle />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleAdd"><el-icon><Plus /></el-icon> 新增用工</el-dropdown-item>
              <el-dropdown-item @click="handleExport"><el-icon><Download /></el-icon> 导出 Excel</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        </template>
      </AppFilterBar>
      </AppSectionCard>
    </AppWorkspacePanel>

    <AppWorkspacePanel panel-class="zero-hour-panel zero-hour-panel--results">
      <AppSectionCard v-if="isMobile" class="zero-hour-card-shell">
      <template #header>用工列表</template>
      <AppEmptyState
        v-if="!loading && !list.length"
        title="暂无零星用工记录"
      />
      <div v-else class="labor-card-list">
        <article v-for="row in list" :key="row.id" class="labor-card">
          <div class="labor-card__header">
            <div>
              <div class="labor-card__title">{{ row.dispatch_unit || '未填写派工单位' }}</div>
              <div class="labor-card__date">{{ row.labor_date || '-' }}</div>
            </div>
            <el-tag :type="row.attribution === 'PROJECT' ? 'warning' : 'info'" effect="plain">
              {{ row.attribution === 'PROJECT' ? '项目用工' : '公司用工' }}
            </el-tag>
          </div>
          <div class="labor-card__body">
            <div class="labor-field">
              <span class="labor-field__label">上游合同</span>
              <span class="labor-field__value">{{ row.upstream_contract ? row.upstream_contract.contract_name : '-' }}</span>
            </div>
            <div class="labor-field">
              <span class="labor-field__label">审批状态</span>
              <span class="labor-field__value">{{ formatApprovalStatus(row.approval_status) }}</span>
            </div>
            <div class="labor-field">
              <span class="labor-field__label">总金额</span>
              <span class="labor-field__value labor-field__value--amount">¥ {{ formatMoney(row.total_amount) }}</span>
            </div>
          </div>
          <div class="labor-card__footer">
            <div class="labor-card__links">
              <el-button v-if="row.dispatch_file_path" link type="primary" size="small" :icon="Document" @click="viewFile(row.dispatch_file_path)">派工单</el-button>
              <el-button v-if="row.approval_pdf_path" link type="primary" size="small" :icon="Document" @click="viewFile(row.approval_pdf_path)">审批单</el-button>
            </div>
            <div class="labor-card__links">
              <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
            </div>
          </div>
        </article>

        <div class="pagination-container pagination-container--mobile">
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

      <AppSectionCard v-else class="zero-hour-card-shell">
      <template #header>用工列表</template>
      <AppDataTable>
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
                <span v-else class="cell-placeholder">-</span>
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
                <span v-else class="cell-placeholder">-</span>
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
                <span class="table-amount-strong">¥ {{ formatMoney(row.total_amount) }}</span>
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
      </AppDataTable>
      </AppSectionCard>
    </AppWorkspacePanel>

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
            <div v-if="form.approval_status && form.approval_status !== 'DRAFT'" class="approval-strip">
                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item label="审批状态" class="approval-strip__item">
                             <el-tag :type="getApprovalStatusType(form.approval_status)">
                                {{ formatApprovalStatus(form.approval_status) }}
                            </el-tag>
                        </el-form-item>
                    </el-col>
                    <el-col :span="12">
                        <el-form-item label="审批单" class="approval-strip__item">
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
                        <el-button :icon="Document" @click="viewFile(form.approval_pdf_path)" v-if="form.approval_pdf_path" />
                        <span v-else>可选</span>
                    </template>
                </el-input>
            </el-form-item>

            <div v-if="form.attribution === 'PROJECT'" class="dialog-subsection">
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
            <div class="cost-block">
                <el-row :gutter="20" align="middle">
                    <el-col :span="4">
                        <div class="cost-block__title">技工</div>
                    </el-col>
                     <el-col :span="6">
                        <el-form-item label="单价" label-width="50px" class="cost-block__item">
                            <el-input-number v-model="form.skilled_unit_price" :min="0" :precision="2" :controls="false" style="width: 100%" placeholder="技工单价" />
                        </el-form-item>
                    </el-col>
                    <el-col :span="6">
                        <el-form-item label="数量" label-width="50px" class="cost-block__item">
                            <el-input-number v-model="form.skilled_quantity" :min="0" :precision="2" :controls="false" style="width: 100%" placeholder="技工数量" />
                        </el-form-item>
                    </el-col>
                    <el-col :span="6">
                        <div class="cost-block__summary">合计: ¥ {{ formatMoney(calcSkilledTotal) }}</div>
                    </el-col>
                </el-row>
            </div>
            
             <!-- General Labor (Use specific fields for general) -->
            <div class="cost-block">
                <el-row :gutter="20" align="middle">
                    <el-col :span="4">
                        <div class="cost-block__title">普工</div>
                    </el-col>
                     <el-col :span="6">
                        <el-form-item label="单价" label-width="50px" class="cost-block__item">
                            <el-input-number v-model="form.general_unit_price" :min="0" :precision="2" :controls="false" style="width: 100%" placeholder="普工单价" />
                        </el-form-item>
                    </el-col>
                    <el-col :span="6">
                        <el-form-item label="数量" label-width="50px" class="cost-block__item">
                            <el-input-number v-model="form.general_quantity" :min="0" :precision="2" :controls="false" style="width: 100%" placeholder="普工数量" />
                        </el-form-item>
                    </el-col>
                    <el-col :span="6">
                        <div class="cost-block__summary">合计: ¥ {{ formatMoney(calcGeneralTotal) }}</div>
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
                        <span class="vehicle-total">{{ formatMoney(calcVehicleTotal) }}</span>
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
                          <div class="el-upload__tip">仅支持一个 PDF</div>
                        </template>
                    </el-upload>
                </el-col>
             </el-row>

             <el-divider />
             <div class="grand-total">
                总金额: <span class="grand-total__amount">¥ {{ formatMoney(grandTotal) }}</span>
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
import AppSectionCard from '@/components/ui/AppSectionCard.vue'
import AppFilterBar from '@/components/ui/AppFilterBar.vue'
import AppDataTable from '@/components/ui/AppDataTable.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import AppRangeField from '@/components/ui/AppRangeField.vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'

const { isMobile } = useMobileDetection()

const loading = ref(false)
const exporting = ref(false)
const list = ref([])
const total = ref(0)
const upstreamContracts = ref([])
const filterUpstreamContracts = ref([])
const loadingContracts = ref(false)
const fileList = ref([])
const dateRange = ref([])

// Material Options - In real app fetch from DB, for now hardcoded commonly used ones or empty to start
const materialOptions = ref(['水泥', '沙子', '红砖', '铁丝', '钉子'])

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

const queryParams = reactive({
    page: 1,
    page_size: 20,
    attribution: '',
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
        const [startDate, endDate] = dateRange.value || []
        if (startDate) params.start_date = startDate
        if (endDate) params.end_date = endDate
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
    dateRange.value = []
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
        const [startDate, endDate] = dateRange.value || []
        if (startDate) params.start_date = startDate
        if (endDate) params.end_date = endDate
        
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

<style scoped lang="scss">
.zero-hour-page {
  display: grid;
  gap: var(--workspace-shell-gap);
}

.zero-hour-panel {
  gap: 0;
}

.zero-hour-card-shell {
  border: 0;
  background: transparent;
  box-shadow: none;
  border-radius: 0;
}

.zero-hour-card-shell :deep(.el-card__header) {
  padding: 0 0 16px;
}

.zero-hour-card-shell :deep(.el-card__body) {
  padding: 0;
}

.zero-hour-panel :deep(.el-table td.el-table__cell),
.zero-hour-panel :deep(.el-table th.el-table__cell) {
  padding-top: 14px;
  padding-bottom: 14px;
}

.pagination-container {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.pagination-container--mobile {
  justify-content: center;
}

.labor-card-list {
  display: grid;
  gap: 14px;
}

.labor-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  background: var(--surface-panel);
  box-shadow: none;
}

.labor-card__header,
.labor-card__footer,
.labor-field {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.labor-card__title {
  font-weight: 700;
  color: var(--text-primary);
}

.labor-card__date {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-muted);
}

.labor-card__body {
  display: grid;
  gap: 10px;
}

.labor-field__label {
  min-width: 56px;
  color: var(--text-muted);
}

.labor-field__value {
  flex: 1;
  text-align: right;
  color: var(--text-secondary);
  word-break: break-word;
}

.labor-field__value--amount,
.table-amount-strong {
  color: var(--status-danger);
  font-weight: 700;
}

.labor-card__links {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 8px;
}

.contract-option-meta,
.cell-placeholder {
  color: var(--text-muted);
}

.contract-option-meta {
  font-size: 12px;
}

.approval-strip {
  margin-bottom: 18px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid var(--border-subtle);
  background: color-mix(in srgb, var(--surface-panel-muted) 76%, var(--surface-panel) 24%);
}

.approval-strip__item {
  margin-bottom: 0;
}

.dialog-subsection {
  margin-bottom: 18px;
  padding: 12px;
  border-radius: 12px;
  background: var(--surface-panel-muted);
}

.cost-block {
  margin-bottom: 10px;
  padding: 12px;
  border: 1px dashed var(--border-strong);
  border-radius: 12px;
  background: var(--surface-panel);
}

.cost-block__title {
  font-weight: 700;
  text-align: center;
  color: var(--text-primary);
}

.cost-block__item {
  margin-bottom: 0;
}

.cost-block__summary,
.vehicle-total,
.grand-total {
  font-weight: 700;
  color: var(--text-primary);
}

.cost-block__summary {
  text-align: right;
}

.grand-total {
  font-size: 18px;
  text-align: right;
}

.grand-total__amount {
  font-size: 24px;
  color: var(--status-danger);
}

.action-item {
  display: inline-flex;
}

@media (max-width: 767px) {
  .labor-card__header,
  .labor-card__footer,
  .labor-field {
    flex-direction: column;
  }

  .labor-field__value {
    text-align: left;
  }
}
</style>
