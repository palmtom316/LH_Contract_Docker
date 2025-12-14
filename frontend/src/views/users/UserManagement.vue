<template>
  <div class="app-container">
    <el-card class="filter-container" shadow="never">
      <el-row :gutter="20" justify="space-between">
        <el-col :span="16">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索用户名/姓名/邮箱"
            clearable
            style="width: 300px"
            @keyup.enter="fetchUsers"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" @click="fetchUsers" style="margin-left: 10px">搜索</el-button>
        </el-col>
        <el-col :span="8" style="text-align: right">
          <el-button type="success" icon="Plus" @click="handleAdd">新建用户</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="always">
      <el-table v-loading="loading" :data="userList" border style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="full_name" label="姓名" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="role_display" label="角色" width="120" align="center">
          <template #default="scope">
            <el-tag :type="getRoleTagType(scope.row.role)">{{ scope.row.role_display || scope.row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
              {{ scope.row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="180" align="center">
          <template #default="scope">
            {{ formatDateTime(scope.row.last_login) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-button link type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button link type="warning" size="small" @click="handleResetPassword(scope.row)">重置密码</el-button>
            <el-button 
              link 
              :type="scope.row.is_active ? 'danger' : 'success'" 
              size="small" 
              @click="handleToggleStatus(scope.row)"
            >
              {{ scope.row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button 
              link 
              type="danger" 
              size="small" 
              @click="handleDelete(scope.row)"
              :disabled="scope.row.is_superuser"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create/Edit User Dialog -->
    <el-dialog 
      :title="dialogTitle" 
      v-model="dialogVisible" 
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="form.full_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" placeholder="请选择角色" style="width: 100%">
            <el-option 
              v-for="role in roleOptions" 
              :key="role.value" 
              :label="role.label" 
              :value="role.value" 
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!isEdit" label="初始密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入初始密码（至少6位）" />
        </el-form-item>
        <el-form-item v-if="isEdit" label="账号状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- Reset Password Dialog -->
    <el-dialog 
      title="重置密码" 
      v-model="resetPwdVisible" 
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-width="100px">
        <el-form-item label="用户">
          <el-input :value="resetForm.username" disabled />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="resetForm.new_password" type="password" show-password placeholder="请输入新密码（至少6位）" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="resetForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPwdVisible = false">取消</el-button>
        <el-button type="primary" @click="handleResetSubmit" :loading="resetting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import request from '@/utils/request'

const loading = ref(false)
const userList = ref([])
const searchKeyword = ref('')

// Dialog state
const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

// Reset password dialog
const resetPwdVisible = ref(false)
const resetting = ref(false)
const resetFormRef = ref(null)

// Role options
const roleOptions = ref([
  { value: 'ADMIN', label: '管理员' },
  { value: 'COMPANY_LEADER', label: '公司领导' },
  { value: 'CONTRACT_MANAGER', label: '合同管理' },
  { value: 'FINANCE', label: '财务部' },
  { value: 'ENGINEERING', label: '工程部' },
  { value: 'AUDIT', label: '审计部' },
  { value: 'BIDDING', label: '投标部' },
  { value: 'GENERAL_AFFAIRS', label: '综合部' },
])

// Form data
const form = reactive({
  id: null,
  username: '',
  full_name: '',
  email: '',
  role: 'BIDDING',
  password: '',
  is_active: true
})

const resetForm = reactive({
  user_id: null,
  username: '',
  new_password: '',
  confirm_password: ''
})

// Validation rules
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度3-50个字符', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入初始密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度6-100个字符', trigger: 'blur' }
  ]
}

const validateConfirmPwd = (rule, value, callback) => {
  if (value !== resetForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const resetRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度6-100个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPwd, trigger: 'blur' }
  ]
}

// Fetch users
const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await request({
      url: '/users/',
      method: 'get'
    })
    userList.value = res
  } catch (e) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// Get role tag type
const getRoleTagType = (role) => {
  const typeMap = {
    'ADMIN': 'danger',
    'COMPANY_LEADER': 'warning',
    'CONTRACT_MANAGER': 'success',
    'FINANCE': 'primary',
    'ENGINEERING': '',
    'AUDIT': 'info',
    'BIDDING': 'info',
    'GENERAL_AFFAIRS': ''
  }
  return typeMap[role] || ''
}

// Format datetime
const formatDateTime = (dt) => {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN')
}

// Reset form
const resetFormData = () => {
  form.id = null
  form.username = ''
  form.full_name = ''
  form.email = ''
  form.role = 'BIDDING'
  form.password = ''
  form.is_active = true
}

// Add user
const handleAdd = () => {
  resetFormData()
  isEdit.value = false
  dialogTitle.value = '新建用户'
  dialogVisible.value = true
}

// Edit user
const handleEdit = (row) => {
  resetFormData()
  form.id = row.id
  form.username = row.username
  form.full_name = row.full_name
  form.email = row.email
  form.role = row.role
  form.is_active = row.is_active
  isEdit.value = true
  dialogTitle.value = '编辑用户'
  dialogVisible.value = true
}

// Submit form
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (isEdit.value) {
        // Update user
        await request({
          url: `/users/${form.id}`,
          method: 'put',
          data: {
            email: form.email || null,
            full_name: form.full_name || null,
            role: form.role,
            is_active: form.is_active
          }
        })
        ElMessage.success('用户更新成功')
      } else {
        // Create user
        await request({
          url: '/users/',
          method: 'post',
          data: {
            username: form.username,
            email: form.email || null,
            full_name: form.full_name || null,
            role: form.role,
            password: form.password
          }
        })
        ElMessage.success('用户创建成功')
      }
      dialogVisible.value = false
      fetchUsers()
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// Reset password
const handleResetPassword = (row) => {
  resetForm.user_id = row.id
  resetForm.username = row.username
  resetForm.new_password = ''
  resetForm.confirm_password = ''
  resetPwdVisible.value = true
}

const handleResetSubmit = async () => {
  if (!resetFormRef.value) return
  
  await resetFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    resetting.value = true
    try {
      await request({
        url: `/users/${resetForm.user_id}/reset-password`,
        method: 'post',
        data: {
          new_password: resetForm.new_password
        }
      })
      ElMessage.success('密码重置成功')
      resetPwdVisible.value = false
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '密码重置失败')
    } finally {
      resetting.value = false
    }
  })
}

// Toggle user status
const handleToggleStatus = async (row) => {
  const action = row.is_active ? '禁用' : '启用'
  
  try {
    await ElMessageBox.confirm(`确定要${action}用户 "${row.username}" 吗?`, '提示', {
      type: 'warning'
    })
    
    await request({
      url: `/users/${row.id}`,
      method: 'put',
      data: {
        is_active: !row.is_active
      }
    })
    ElMessage.success(`用户已${action}`)
    fetchUsers()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    }
  }
}

// Delete user
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除用户 "${row.username}" 吗？此操作不可恢复！`, '警告', {
      type: 'error',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
    })
    
    await request({
      url: `/users/${row.id}`,
      method: 'delete'
    })
    ElMessage.success('用户已删除')
    fetchUsers()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped lang="scss">
.filter-container {
  margin-bottom: 20px;
}
</style>
