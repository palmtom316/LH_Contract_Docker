<template>
  <div class="app-container">
    <!-- Search Bar -->
    <el-card class="filter-container" shadow="never">
      <el-form :inline="true" :model="queryParams" class="demo-form-inline">
        <el-form-item label="关键词">
          <el-input v-model="queryParams.keyword" placeholder="费用说明/收款方/编号" clearable @keyup.enter="handleQuery" />
        </el-form-item>
        <el-form-item label="费用分类">
          <el-select v-model="queryParams.category" placeholder="费用分类" clearable style="width: 140px">
            <el-option label="工资" value="工资" />
            <el-option label="奖金" value="奖金" />
            <el-option label="培训费" value="培训费" />
            <el-option label="资质费" value="资质费" />
            <el-option label="办公费" value="办公费" />
            <el-option label="餐饮费" value="餐饮费" />
            <el-option label="房屋租赁" value="房屋租赁" />
            <el-option label="交通费" value="交通费" />
            <el-option label="车辆使用费" value="车辆使用费" />
            <el-option label="其他租赁" value="其他租赁" />
            <el-option label="水电费" value="水电费" />
            <el-option label="业务费" value="业务费" />
            <el-option label="住宿费" value="住宿费" />
            <el-option label="通讯费" value="通讯费" />
            <el-option label="投标费" value="投标费" />
            <el-option label="中介费" value="中介费" />
            <el-option label="其他费用" value="其他费用" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
          <el-button icon="Refresh" @click="resetQuery">重置</el-button>
          <el-button type="success" icon="Plus" @click="handleAdd">记一笔</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Table -->
    <el-card class="table-container" shadow="always">
      <el-table 
        v-loading="loading" 
        :data="expenseList" 
        style="width: 100%" 
        border
        highlight-current-row
      >
        <el-table-column prop="expense_code" label="编号" width="140" fixed />
        <el-table-column prop="expense_date" label="日期" width="120" sortable />
        <el-table-column prop="category" label="费用分类" width="100">
          <template #default="scope">
            <el-tag effect="plain">{{ scope.row.category }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
        <el-table-column prop="payee_name" label="收款方" min-width="150" show-overflow-tooltip />
        <el-table-column label="费用文件" width="100" align="center">
          <template #default="scope">
            <el-link v-if="scope.row.file_path" type="primary" :href="scope.row.file_path" target="_blank">查看</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="140" align="right">
          <template #default="scope">
             ¥ {{ Number(scope.row.amount).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag 
              :type="scope.row.status === '已审核' ? 'success' : (scope.row.status === '已驳回' ? 'danger' : 'warning')"
            >
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-button link type="primary" size="small" @click="handleEdit(scope.row)" :disabled="scope.row.status === '已审核'">编辑</el-button>

            <el-popconfirm title="确定删除吗?" @confirm="handleDelete(scope.row)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
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

    <!-- Dialog -->
    <el-dialog
      :title="dialog.title"
      v-model="dialog.visible"
      width="600px"
      append-to-body
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
             <el-form-item label="费用编号" prop="expense_code">
              <el-input v-model="form.expense_code" placeholder="系统自动生成" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="费用日期" prop="expense_date">
              <el-date-picker 
                v-model="form.expense_date" 
                type="date" 
                placeholder="选择日期" 
                style="width: 100%" 
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="费用分类" prop="category">
              <el-select v-model="form.category" placeholder="请选择" style="width: 100%">
            <el-option label="工资" value="工资" />
            <el-option label="奖金" value="奖金" />
            <el-option label="培训费" value="培训费" />
            <el-option label="资质费" value="资质费" />
            <el-option label="办公费" value="办公费" />
            <el-option label="餐饮费" value="餐饮费" />
            <el-option label="房屋租赁" value="房屋租赁" />
            <el-option label="交通费" value="交通费" />
            <el-option label="车辆使用费" value="车辆使用费" />
            <el-option label="其他租赁" value="其他租赁" />
            <el-option label="水电费" value="水电费" />
            <el-option label="业务费" value="业务费" />
            <el-option label="住宿费" value="住宿费" />
            <el-option label="通讯费" value="通讯费" />
            <el-option label="投标费" value="投标费" />
            <el-option label="中介费" value="中介费" />
            <el-option label="其他费用" value="其他费用" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="金额" prop="amount">
          <el-input-number 
            v-model="form.amount" 
            :precision="2" 
            :step="100" 
            :min="0" 
            :controls="false"
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
            accept=".pdf"
          >
            <el-button type="primary">点击上传</el-button>
            <template #tip>
              <div class="el-upload__tip">只能上传 PDF 文件</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="收款方" prop="payee_name">
          <el-input v-model="form.payee_name" />
        </el-form-item>

        <el-form-item label="付款方式" prop="payment_method">
          <el-select v-model="form.payment_method" style="width: 100%">
            <el-option label="银行转账" value="银行转账" />
            <el-option label="现金" value="现金" />
            <el-option label="微信/支付宝" value="网络支付" />
            <el-option label="支票" value="支票" />
          </el-select>
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
import { ref, reactive, onMounted } from 'vue'
import { getExpenses, createExpense, updateExpense, deleteExpense, approveExpense } from '@/api/expense'
import { uploadFile } from '@/api/common'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const total = ref(0)
const expenseList = ref([])
const fileList = ref([])

const queryParams = reactive({
  page: 1,
  page_size: 10,
  keyword: '',
  category: '',
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
  expense_code: '',
  category: '',
  amount: 0,
  tax_amount: 0,
  expense_date: '',
  payee_name: '',
  payment_method: '',
  description: '',
  file_path: '',
  status: '待审核'
})

const rules = {
  expense_code: [{ required: true, message: '请输入编号', trigger: 'blur' }],
  category: [{ required: true, message: '请选择费用分类', trigger: 'change' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }],
  expense_date: [{ required: true, message: '请选择日期', trigger: 'change' }]
}

const getList = async () => {
  loading.value = true
  try {
    const res = await getExpenses(queryParams)
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
  queryParams.keyword = ''
  queryParams.category = ''
  queryParams.status = ''
  handleQuery()
}

// Form handling
const resetForm = () => {
  form.id = undefined
  form.expense_code = 'FY' + new Date().getTime().toString().substr(-8) // Generate simple code
  form.category = ''
  form.amount = 0
  form.tax_amount = 0
  form.expense_date = new Date().toISOString().split('T')[0]
  form.payee_name = ''
  form.payment_method = ''
  form.description = ''
  form.file_path = ''
  fileList.value = []
  form.status = '待审核'
}

const handleAdd = () => {
  resetForm()
  dialog.title = '新建费用记录'
  dialog.isEdit = false
  dialog.visible = true
}

const handleEdit = (row) => {
  resetForm()
  Object.assign(form, row)
  fileList.value = row.file_path ? [{ name: '费用文件', url: row.file_path }] : []
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

const handleDelete = async (row) => {
  await deleteExpense(row.id)
  ElMessage.success('删除成功')
  getList()
}

const handleApprove = async (row, approved) => {
  await approveExpense(row.id, approved)
  ElMessage.success(approved ? '审核通过' : '已驳回')
  getList()
}

const handleUploadRequest = async (option) => {
  try {
    const res = await uploadFile(option.file)
    form.file_path = res.path
    fileList.value = [{ name: option.file.name, url: res.path }]
    ElMessage.success('上传成功')
  } catch (e) {
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

onMounted(() => {
  getList()
})
</script>

<style scoped>
.filter-container {
  margin-bottom: 20px;
}
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
