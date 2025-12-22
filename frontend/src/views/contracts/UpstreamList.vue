<template>
  <div class="app-container">
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <!-- Tab 1: Contract Management -->
      <el-tab-pane label="合同管理" name="management">
        <!-- Search Bar -->
        <el-card class="filter-container" shadow="never">
          <el-form :inline="true" :model="queryParams" class="demo-form-inline">
            <el-form-item label="关键词">
              <el-input v-model="queryParams.keyword" placeholder="合同序号/编号/名称/甲方" clearable @keyup.enter="handleQuery" />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="queryParams.status" placeholder="合同状态" clearable style="width: 120px">
                <el-option label="执行中" value="执行中" />
                <el-option label="已完工" value="已完工" />
                <el-option label="已结算" value="已结算" />
                <el-option label="质保到期" value="质保到期" />
                <el-option label="合同终止" value="合同终止" />
                <el-option label="合同中止" value="合同中止" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
              <el-button icon="Refresh" @click="resetQuery">重置</el-button>
              <el-button type="warning" icon="Download" @click="handleExport">导出Excel</el-button>
              <el-dropdown @command="handleImportCommand" style="margin-left: 10px;" v-if="userStore.canManageUpstreamContracts">
                <el-button type="info" icon="Upload">
                  导入Excel<el-icon class="el-icon--right"><arrow-down /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="template">下载导入模板</el-dropdown-item>
                    <el-dropdown-item command="import">选择Excel文件导入</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-button v-if="userStore.canManageUpstreamContracts" type="success" icon="Plus" @click="handleAdd" style="margin-left: 10px;">新建合同</el-button>
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
            show-summary
            :summary-method="getSummaries"
            class="custom-footer-table"
            :footer-cell-style="footerCellStyle"
          >
            <el-table-column prop="serial_number" label="合同序号" width="100" align="center" fixed="left" />
            <el-table-column prop="contract_code" label="合同编号" min-width="140" show-overflow-tooltip />
            <el-table-column prop="contract_name" label="合同名称" min-width="220">
              <template #default="scope">
                <div :style="{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.5', maxHeight: '4.5em', overflow: 'hidden' }">{{ scope.row.contract_name }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="party_a_name" label="甲方单位" min-width="180">
              <template #default="scope">
                <div :style="{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.5', maxHeight: '4.5em', overflow: 'hidden' }">{{ scope.row.party_a_name }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="party_b_name" label="乙方单位" min-width="180">
              <template #default="scope">
                <div :style="{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.5', maxHeight: '4.5em', overflow: 'hidden' }">{{ scope.row.party_b_name }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="contract_amount" label="签约金额" width="140" align="right">
              <template #default="scope">
                ¥ {{ formatMoney(scope.row.contract_amount) }}
              </template>
            </el-table-column>
            <el-table-column prop="total_receivable" label="应收款" width="120" align="right">
              <template #default="scope">
                <span v-if="scope.row.total_receivable">¥ {{ formatMoney(scope.row.total_receivable) }}</span>
                <span v-else class="text-gray">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="total_invoiced" label="挂账" width="120" align="right">
              <template #default="scope">
                <span v-if="scope.row.total_invoiced">¥ {{ formatMoney(scope.row.total_invoiced) }}</span>
                <span v-else class="text-gray">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="total_received" label="回款" width="120" align="right">
              <template #default="scope">
                <span v-if="scope.row.total_received">¥ {{ formatMoney(scope.row.total_received) }}</span>
                <span v-else class="text-gray">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="total_settlement" label="结算" width="120" align="right">
              <template #default="scope">
                <span v-if="scope.row.total_settlement">¥ {{ formatMoney(scope.row.total_settlement) }}</span>
                <span v-else class="text-gray">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="sign_date" label="签约时间" width="120" align="center" />
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="company_category" label="公司合同分类" width="130" align="center" show-overflow-tooltip />
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
                <span v-else class="text-gray">-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="190" fixed="right">
              <template #default="scope">
                <el-button v-if="userStore.canManageUpstreamContracts" link type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
                <el-button link type="primary" size="small" @click="handleDetail(scope.row)">详情</el-button>
                <el-button v-if="userStore.canManageUpstreamContracts" link type="danger" size="small" @click="handleDelete(scope.row)">删除</el-button>
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
                <span class="label">甲方:</span>
                <span class="value">{{ item.party_a_name }}</span>
              </div>
              <div class="info-row">
                <span class="label">合同金额:</span>
                <span class="value amount">¥ {{ formatMoney(item.contract_amount) }}</span>
              </div>
              <div class="info-row">
                <span class="label">签订日期:</span>
                <span class="value">{{ item.sign_date }}</span>
              </div>
            </div>
            <div class="card-footer">
               <el-button 
                v-if="item.contract_file_path" 
                size="small" 
                type="warning" 
                icon="Document" 
                circle
                @click="handlePreview(item.contract_file_path)"
              />
              <el-button v-if="userStore.canManageUpstreamContracts" size="small" type="primary" @click="handleEdit(item)">编辑</el-button>
              <el-button size="small" @click="handleDetail(item)">详情</el-button>
              <el-button v-if="userStore.canManageUpstreamContracts" size="small" type="danger" @click="handleDelete(item)">删除</el-button>
            </div>
          </el-card>

          <!-- Mobile Pagination -->
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
      </el-tab-pane>

      <!-- Tab 2: Basic Information List -->
      <el-tab-pane label="上游合同基本信息" name="basic_info">
        <!-- Search Bar -->
        <el-card class="filter-container" shadow="never">
          <el-form :inline="true" :model="queryParams" class="demo-form-inline">
            <el-form-item label="关键词">
              <el-input v-model="queryParams.keyword" placeholder="合同序号/编号/名称/甲方" clearable @keyup.enter="handleQuery" />
            </el-form-item>
            <el-form-item label="签约日期">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                unlink-panels
                @change="handleQuery"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
              <el-button icon="Refresh" @click="resetQuery">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Table View -->
        <el-card class="table-container" shadow="always">
          <el-table 
            v-loading="loading" 
            :data="contractList" 
            style="width: 100%" 
            border
            highlight-current-row
            class="custom-footer-table"
          >
            <el-table-column prop="serial_number" label="合同序号" width="100" align="center" fixed="left" />
            <el-table-column prop="contract_code" label="合同编号" min-width="140" show-overflow-tooltip />
            <el-table-column prop="contract_name" label="合同名称" min-width="220" show-overflow-tooltip>
              <template #default="scope">
                <div :style="{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.5', maxHeight: '4.5em', overflow: 'hidden' }">{{ scope.row.contract_name }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="party_a_name" label="合同甲方单位" min-width="200" show-overflow-tooltip>
              <template #default="scope">
                <div :style="{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.5', maxHeight: '4.5em', overflow: 'hidden' }">{{ scope.row.party_a_name }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="contract_amount" label="签约金额" width="140" align="right">
              <template #default="scope">
                ¥ {{ formatMoney(scope.row.contract_amount) }}
              </template>
            </el-table-column>
             <el-table-column prop="total_settlement" label="结算金额" width="140" align="right">
              <template #default="scope">
                <span v-if="scope.row.total_settlement">¥ {{ formatMoney(scope.row.total_settlement) }}</span>
                <span v-else class="text-gray">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="sign_date" label="签约时间" width="120" align="center" />
            <el-table-column prop="completion_date" label="完工时间" width="120" align="center" />
            
            <el-table-column label="合同文件" width="120" align="center">
              <template #default="scope">
                 <el-button v-if="scope.row.contract_file_path" link type="primary" icon="Document" @click="openPdfInNewTab(scope.row.contract_file_path)">查看</el-button>
                 <span v-else class="text-gray">-</span>
              </template>
            </el-table-column>
            
            <el-table-column label="开工报告" width="120" align="center">
              <template #default="scope">
                 <el-button v-if="scope.row.start_report_path" link type="primary" icon="Document" @click="openPdfInNewTab(scope.row.start_report_path)">查看</el-button>
                 <span v-else class="text-gray">-</span>
              </template>
            </el-table-column>
            
            <el-table-column label="竣工报告" width="120" align="center">
              <template #default="scope">
                 <el-button v-if="scope.row.completion_report_path" link type="primary" icon="Document" @click="openPdfInNewTab(scope.row.completion_report_path)">查看</el-button>
                 <span v-else class="text-gray">-</span>
              </template>
            </el-table-column>
            
             <el-table-column label="结算审核文件" width="140" align="center">
              <template #default="scope">
                 <el-button v-if="scope.row.audit_report_path" link type="primary" icon="Document" @click="openPdfInNewTab(scope.row.audit_report_path)">查看</el-button>
                 <span v-else class="text-gray">-</span>
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
      </el-tab-pane>
    </el-tabs>

    <!-- Edit/Create Dialog -->
    <el-dialog
      :title="dialog.title"
      v-model="dialog.visible"
      width="850px"
      :fullscreen="isMobile"
      append-to-body
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
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
            <el-form-item label="签约日期" prop="sign_date">
              <SmartDateInput 
                v-model="form.sign_date" 
                style="width: 100%" 
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
             <el-form-item label="合同编号" prop="contract_code">
              <el-input v-model="form.contract_code" placeholder="请输入编号" />
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="dialog.isEdit">
            <el-form-item label="合同状态" prop="status">
              <el-select v-model="form.status" placeholder="请选择状态" style="width: 100%">
                <el-option label="执行中" value="执行中" />
                <el-option label="已完工" value="已完工" />
                <el-option label="已结算" value="已结算" />
                <el-option label="质保到期" value="质保到期" />
                <el-option label="合同终止" value="合同终止" />
                <el-option label="合同中止" value="合同中止" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="合同名称" prop="contract_name">
              <el-input v-model="form.contract_name" placeholder="请输入合同名称" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="甲方单位" prop="party_a_name">
              <SmartAutocomplete v-model="form.party_a_name" placeholder="输入甲方名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="乙方单位" prop="party_b_name">
              <SmartAutocomplete v-model="form.party_b_name" placeholder="请输入乙方名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="签约金额" prop="contract_amount">
              <FormulaInput 
                v-model="form.contract_amount" 
                placeholder="支持公式计算"
                show-icon
                style="width: 100%" 
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计价模式" prop="pricing_mode">
              <DictSelect v-model="form.pricing_mode" category="pricing_mode" placeholder="请选择" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="合同类别" prop="category">
              <DictSelect v-model="form.category" category="contract_category" placeholder="请选择" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="公司合同分类" prop="company_category">
              <DictSelect v-model="form.company_category" category="project_category" placeholder="请选择" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="管理模式" prop="management_mode">
              <DictSelect v-model="form.management_mode" category="management_mode" placeholder="请选择" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
             <el-form-item label="负责人" prop="responsible_person">
              <el-input v-model="form.responsible_person" placeholder="请输入负责人姓名" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- File Upload -->
        <el-form-item label="合同文件" prop="contract_file_path">
          <el-upload
            class="upload-demo"
            action="#"
            :http-request="handleUploadRequest"
            :limit="1"
            :on-remove="handleRemoveFile"
            :file-list="fileList"
            accept=".pdf"
          >
            <template #trigger>
              <el-button type="primary">选择文件 (PDF)</el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                支持PDF文件
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialog.visible = false">取 消</el-button>
          <el-button type="primary" @click="submitForm" :loading="uploading">确 定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- PDF Viewer Dialog -->
    <el-dialog 
      v-model="pdfDialog.visible" 
      title="合同附件预览" 
      fullscreen 
      destroy-on-close
      append-to-body
    >
      <PdfViewer :source="pdfDialog.url" />
    </el-dialog>

    <!-- Hidden file input for import -->
    <input 
      ref="importFileInput"
      type="file" 
      accept=".xlsx,.xls" 
      style="display: none;"
      @change="handleImportFileChange"
    />

    <!-- Import Result Dialog -->
    <el-dialog
      v-model="importResult.visible"
      title="导入结果"
      width="500px"
      append-to-body
    >
      <div class="import-result">
        <el-result v-if="importResult.success_count > 0 && importResult.error_count === 0" icon="success" title="导入成功">
          <template #sub-title>
            <p>成功导入 {{ importResult.success_count }} 条合同记录</p>
          </template>
        </el-result>
        <el-result v-else-if="importResult.success_count === 0 && importResult.error_count > 0" icon="error" title="导入失败">
          <template #sub-title>
            <p>全部 {{ importResult.error_count }} 条记录导入失败</p>
          </template>
        </el-result>
        <el-result v-else icon="warning" title="部分导入成功">
          <template #sub-title>
            <p>成功: {{ importResult.success_count }} 条，失败: {{ importResult.error_count }} 条</p>
          </template>
        </el-result>
        
        <div v-if="importResult.errors && importResult.errors.length > 0" class="error-list">
          <el-divider>错误详情</el-divider>
          <el-table :data="importResult.errors" max-height="200" size="small">
            <el-table-column prop="row" label="行号" width="80" />
            <el-table-column prop="error" label="错误信息" show-overflow-tooltip />
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="importResult.visible = false">确 定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { getContracts, createContract, updateContract, deleteContract, exportContracts, downloadImportTemplate, importContracts, getNextSerialNumber } from '@/api/contractUpstream'
import { uploadFile } from '@/api/common'
import { getFileUrl } from '@/utils/common'
import { downloadExcel } from '@/utils/download'
import { useContractList, useTableSummary, useMobileDetection } from '@/composables/useContractList'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import SmartAutocomplete from '@/components/SmartAutocomplete.vue'
import PdfViewer from '@/components/PdfViewer.vue'
import DictSelect from '@/components/DictSelect.vue'
import SmartDateInput from '@/components/SmartDateInput.vue'
import FormulaInput from '@/components/FormulaInput.vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const { getSummaries, footerCellStyle } = useTableSummary()
const { isMobile, checkIsMobile } = useMobileDetection()

const {
  loading,
  list: contractList,
  total,
  queryParams,
  getList: fetchList,
  handleQuery,
  resetQuery: baseResetQuery,
  handleDelete,
  handleExport,
  formatMoney,
  getStatusType
} = useContractList({
  api: { getContracts, deleteContract, exportContracts },
  contractType: '上游合同',
  exportPrefix: '上游合同列表'
})

const activeTab = ref('management')
const dateRange = ref([])

const dialog = reactive({
  title: '',
  visible: false,
  isEdit: false
})

const pdfDialog = reactive({
  visible: false,
  url: ''
})

// Import functionality
const importResult = reactive({
  visible: false,
  success_count: 0,
  error_count: 0,
  errors: []
})
const importFileInput = ref(null)
const importLoading = ref(false)
const uploading = ref(false)

const formRef = ref(null)
const fileList = ref([])
const originalId = ref(null)

const form = reactive({
  serial_number: undefined,
  id: undefined,  // Keep ID for internal tracking if needed
  contract_code: '',
  contract_name: '',
  party_a_name: '',
  party_b_name: '',
  party_a_contact: '',
  party_a_phone: '',
  contract_amount: 0,
  sign_date: '',
  start_date: '',
  end_date: '',
  category: '',
  company_category: '', // 公司合同分类
  pricing_mode: '',     // 计价模式
  management_mode: '',  // 管理模式
  responsible_person: '', // 负责人
  notes: '',
  status: '执行中',
  contract_file_path: ''
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
  contract_code: [{ required: true, message: '请输入合同编号', trigger: 'blur' }],
  contract_name: [{ required: true, message: '请输入合同名称', trigger: 'blur' }],
  party_a_name: [{ required: true, message: '请输入甲方名称', trigger: 'blur' }],
  party_b_name: [{ required: true, message: '请输入乙方名称', trigger: 'blur' }],
  contract_amount: [{ required: true, message: '请输入合同金额', trigger: 'blur' }]
}

// Check if mobile
const handleResize = () => {
  checkIsMobile()
}

const getList = () => {
  // Sync date range
  if (activeTab.value === 'basic_info' && dateRange.value && dateRange.value.length === 2) {
    queryParams.start_date = dateRange.value[0]
    queryParams.end_date = dateRange.value[1]
  } else {
    queryParams.start_date = undefined
    queryParams.end_date = undefined
  }
  fetchList()
}

const handleTabChange = () => {
  queryParams.page = 1
  queryParams.keyword = ''
  queryParams.status = ''
  dateRange.value = []
  getList()
}

const resetQuery = () => {
  dateRange.value = []
  baseResetQuery()
}


// File Upload Logic
const handleUploadRequest = async (option) => {
  uploading.value = true
  try {
    const serial = form.serial_number || '000'
    const customName = `${serial}_${option.file.name}`
    
    const res = await uploadFile(option.file, {
      subdir: 'upstream/contract',
      custom_filename: customName
    })
    
    console.log('Upload response:', res)
    if (res && res.path) {
      form.contract_file_path = res.path
      console.log('File path set to:', form.contract_file_path)
      // Update file list to display the name
      fileList.value = [{
        name: option.file.name,
        url: res.path
      }]
      ElMessage.success('上传成功')
    } else {
      throw new Error('上传返回路径为空')
    }
  } catch (e) {
    ElMessage.error('上传失败')
    option.onError(e)
  } finally {
    uploading.value = false
  }
}

const handleRemoveFile = () => {
  form.contract_file_path = ''
  fileList.value = []
}

// PDF Preview
const handlePreview = (path) => {
  if (!path) return
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
  pdfDialog.url = path 
  pdfDialog.visible = true
}

// Open PDF in new tab
// Open PDF in new tab
const openPdfInNewTab = (path) => {
  if (!path) return
  window.open(getFileUrl(path), '_blank')
}

// Form handling
const resetForm = () => {
  form.serial_number = undefined
  form.id = undefined
  form.contract_code = ''
  form.contract_name = ''
  form.party_a_name = ''
  form.party_b_name = ''
  form.party_a_contact = ''
  form.party_a_phone = ''
  form.contract_amount = 0
  form.sign_date = new Date().toISOString().split('T')[0]
  form.start_date = ''
  form.end_date = ''
  form.category = ''
  form.company_category = ''
  form.pricing_mode = ''
  form.management_mode = ''
  form.responsible_person = ''
  form.notes = ''
  form.status = '执行中'
  form.contract_file_path = ''
  fileList.value = []
}

const handleAdd = async () => {
  resetForm()
  dialog.title = '新建上游合同'
  dialog.isEdit = false
  dialog.visible = true
  
  // Auto-fetch next serial number
  try {
    const res = await getNextSerialNumber()
    if (res && res.serial_number) {
      form.serial_number = res.serial_number
    }
  } catch (e) {
    console.error('Failed to get next serial number:', e)
  }
}

const handleEdit = (row) => {
  resetForm()
  Object.assign(form, row)
  originalId.value = row.id
  
  if (row.contract_file_path) {
    // Use contract name as display name instead of UUID filename
    const displayName = row.contract_name ? `${row.contract_name}.pdf` : '合同文件.pdf'
    fileList.value = [{
      name: displayName,
      url: row.contract_file_path
    }]
  }
  
  dialog.title = '编辑合同'
  dialog.isEdit = true
  dialog.visible = true
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      // Sanitize data: convert empty strings to null for optional API fields
      const dataToSubmit = { ...form }
      if (!dataToSubmit.start_date) dataToSubmit.start_date = null
      if (!dataToSubmit.end_date) dataToSubmit.end_date = null
      if (!dataToSubmit.category) dataToSubmit.category = null
      if (!dataToSubmit.company_category) dataToSubmit.company_category = null
      if (!dataToSubmit.pricing_mode) dataToSubmit.pricing_mode = null
      if (!dataToSubmit.management_mode) dataToSubmit.management_mode = null
      if (!dataToSubmit.responsible_person) dataToSubmit.responsible_person = null
      if (!dataToSubmit.notes) dataToSubmit.notes = null
      if (!dataToSubmit.party_a_contact) dataToSubmit.party_a_contact = null
      if (!dataToSubmit.party_a_phone) dataToSubmit.party_a_phone = null
      if (!dataToSubmit.contract_file_path) dataToSubmit.contract_file_path = null
      
      // Debug: Log the contract_file_path value
      console.log('Submitting contract with file path:', dataToSubmit.contract_file_path)
      
      try {
        if (dialog.isEdit) {
            // Use the original ID for the URL, because the new ID might be different
            await updateContract(originalId.value, dataToSubmit)
            ElMessage.success('更新成功')
        } else {
            await createContract(dataToSubmit)
            ElMessage.success('创建成功')
        }
        dialog.visible = false
        getList()
      } catch (error) {
        console.error('Submit error:', error)
      }
    }
  })
}


const router = useRouter() // Ensure router is imported or available

const handleDetail = (row) => {
  router.push({ name: 'UpstreamDetail', params: { id: row.id } })
}


// Import functionality
const handleImportCommand = (command) => {
  if (command === 'template') {
    handleDownloadTemplate()
  } else if (command === 'import') {
    importFileInput.value?.click()
  }
}

const handleDownloadTemplate = async () => {
  try {
    ElMessage.info('正在下载模板...')
    console.log('Starting template download...')
    const res = await downloadImportTemplate()
    console.log('Template download response:', res)
    downloadExcel(res, '上游合同导入模板.xlsx')
    ElMessage.success('模板下载成功')
  } catch (e) {
    console.error('Template download error details:', e)
    ElMessage.error('模板下载失败: ' + (e.message || '未知错误'))
  }
}

const handleImportFileChange = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  
  // Reset file input for next use
  event.target.value = ''
  
  try {
    importLoading.value = true
    ElMessage.info('正在导入数据...')
    
    const result = await importContracts(file)
    
    // Show result dialog
    importResult.success_count = result.success_count || 0
    importResult.error_count = result.error_count || 0
    importResult.errors = result.errors || []
    importResult.visible = true
    
    // Refresh list if any successful imports
    if (result.success_count > 0) {
      getList()
    }
  } catch (e) {
    ElMessage.error('导入失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    importLoading.value = false
  }
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

:deep(.amount-input-right .el-input__inner) {
  text-align: right;
}

/* Summary Row Styling removed in favor of footer-cell-style prop */

/* Multi-line cell display for long text */
.multi-line-cell {
  white-space: normal;
  word-break: break-word;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 3; /* Max 3 lines */
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.text-gray {
  color: #c0c4cc;
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

/* Multi-line cell display - Force Element Plus table to allow text wrapping */
.custom-footer-table td .cell {
  overflow: visible !important;
  text-overflow: unset !important;
  white-space: normal !important;
}

.custom-footer-table .el-table__row {
  height: auto !important;
}

.custom-footer-table td.el-table__cell {
  height: auto !important;
  vertical-align: top !important;
}

.multi-line-cell {
  white-space: normal !important;
  word-break: break-word !important;
  word-wrap: break-word !important;
  line-height: 1.5 !important;
  max-height: 4.5em !important; /* Approx 3 lines */
  overflow: hidden !important;
  display: block !important;
}
</style>
