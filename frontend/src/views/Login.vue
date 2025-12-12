<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h3 class="title">蓝海合同管理系统 (Debug Mode)</h3>
        <p>Lanhai Contract Management System</p>
      </div>
      
      <el-form 
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input 
            v-model="loginForm.username" 
            placeholder="用户名" 
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="密码" 
            prefix-icon="Lock"
            show-password
            size="large"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            :loading="loading" 
            class="login-button" 
            @click="handleLogin"
            size="large"
          >
            登 录
          </el-button>
        </el-form-item>
        
        <div class="login-footer">
          <!-- Temporary helper for demo -->
          <el-button link type="info" @click="handleInitAdmin" size="small">
            初始化管理员
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { initAdmin } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref(null)

const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await userStore.login(loginForm)
        ElMessage.success('登录成功')
        await router.push('/')
      } catch (error) {
        // Error handled in interceptor
      } finally {
        loading.value = false
      }
    }
  })
}

const handleInitAdmin = async () => {
  try {
    const res = await initAdmin()
    ElMessage.success(res.message)
    loginForm.username = res.username
    loginForm.password = res.default_password
  } catch (error) {
    // Error handled in interceptor
  }
}
</script>

<style scoped lang="scss">
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-image: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  
  .login-box {
    width: 100%;
    max-width: 420px;
    padding: 40px;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 12px;
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
    
    .login-header {
      text-align: center;
      margin-bottom: 30px;
      
      h1 {
        font-size: 24px;
        color: #16213e;
        margin-bottom: 5px;
        font-weight: 600;
      }
      
      p {
        font-size: 12px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
      }
    }
    
    .login-form {
      .login-button {
        width: 100%;
        background-color: #0f3460;
        border-color: #0f3460;
        font-weight: 600;
        letter-spacing: 2px;
        
        &:hover {
          background-color: #e94560;
          border-color: #e94560;
        }
      }
    }
    
    .login-footer {
      display: flex;
      justify-content: center;
      margin-top: 10px;
    }
  }
}
</style>
