<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <p class="eyebrow">财务与合同业务工作台</p>
        <h1 class="title">蓝海合同管理系统</h1>
        <p class="subtitle">稳定、安全、适合日常高频录入与审核</p>
      </div>
      
      <el-form 
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        label-position="top"
        @keyup.enter="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input 
            v-model="loginForm.username" 
            placeholder="用户名" 
            prefix-icon="User"
            size="large"
            autocomplete="username"
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="密码" 
            prefix-icon="Lock"
            show-password
            size="large"
            autocomplete="current-password"
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
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

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
</script>

<style scoped lang="scss">
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(31, 95, 139, 0.14), transparent 34%),
    linear-gradient(180deg, #eef3f7 0%, #f6f8fa 100%);
  
  .login-box {
    width: 100%;
    max-width: 440px;
    padding: 36px 32px 28px;
    background: rgba(255, 255, 255, 0.97);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-card);
    
    .login-header {
      margin-bottom: 28px;
      
      .eyebrow {
        margin: 0 0 10px;
        color: var(--brand-primary);
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.08em;
      }

      .title {
        font-size: 28px;
        line-height: 1.2;
        color: var(--text-primary);
        margin: 0 0 8px;
        font-weight: 700;
      }
      
      .subtitle {
        margin: 0;
        font-size: 14px;
        color: var(--text-secondary);
      }
    }
    
    .login-form {
      :deep(.el-form-item__label) {
        color: var(--text-secondary);
        font-weight: 600;
      }

      :deep(.el-input__wrapper) {
        min-height: 46px;
        border-radius: 10px;
        box-shadow: 0 0 0 1px var(--border-subtle) inset;
      }

      :deep(.el-input__wrapper.is-focus) {
        box-shadow: 0 0 0 1px var(--brand-primary) inset, var(--shadow-focus);
      }

      .login-button {
        width: 100%;
        min-height: 46px;
        background-color: var(--brand-primary);
        border-color: var(--brand-primary);
        font-weight: 600;
        letter-spacing: 0.16em;
        
        &:hover {
          background-color: var(--brand-primary-strong);
          border-color: var(--brand-primary-strong);
        }
      }
    }
  }

  @media (max-width: 768px) {
    .login-box {
      padding: 28px 20px 22px;
    }

    .login-header .title {
      font-size: 24px;
    }
  }
}
</style>
