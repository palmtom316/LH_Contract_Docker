<template>
  <div class="login-shell">
    <div class="login-shell__panel">
      <section class="login-shell__brand">
        <h1 class="login-shell__title">合同管理系统</h1>
        <p class="login-shell__subtitle">登录到企业工作台</p>
      </section>

      <section class="login-shell__form">
        <div class="login-shell__form-copy">
          <h2>账号登录</h2>
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
      </section>
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
.login-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: hsl(var(--background));
}

.login-shell__panel {
  width: min(920px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 420px);
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  background: hsl(var(--card));
  box-shadow: var(--shadow-frame);
  overflow: hidden;
}

.login-shell__brand,
.login-shell__form {
  min-width: 0;
}

.login-shell__brand {
  display: grid;
  align-content: end;
  gap: 12px;
  padding: 36px;
  border-right: 1px solid hsl(var(--border));
  background: hsl(var(--muted));
}

.login-shell__title {
  margin: 0;
  font-size: clamp(28px, 3.5vw, 40px);
  line-height: 1.02;
  color: hsl(var(--foreground));
  font-weight: 700;
  letter-spacing: -0.03em;
}

.login-shell__subtitle {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: hsl(var(--muted-foreground));
}

.login-shell__form {
  display: grid;
  align-content: center;
  gap: 20px;
  padding: 36px;
}

.login-shell__form-copy h2 {
  margin: 0;
  font-size: 20px;
  line-height: 1.2;
  color: hsl(var(--foreground));
}

.login-form :deep(.el-form-item__label) {
  color: hsl(var(--muted-foreground));
  font-weight: 600;
}

.login-form :deep(.el-input__wrapper) {
  min-height: 36px;
  border-radius: 10px;
  box-shadow: 0 0 0 1px hsl(var(--border)) inset;
  background: hsl(var(--background));
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px hsl(var(--ring)) inset, var(--shadow-focus);
}

.login-form .login-button {
  width: 100%;
  min-height: 36px;
  background-color: hsl(var(--primary));
  border-color: hsl(var(--primary));
  font-weight: 700;
  letter-spacing: 0.08em;
}

.login-form .login-button:hover {
  background-color: hsl(var(--primary) / 0.92);
  border-color: hsl(var(--primary) / 0.92);
}

@media (max-width: 900px) {
  .login-shell__panel {
    grid-template-columns: 1fr;
  }

  .login-shell__brand {
    border-right: 0;
    border-bottom: 1px solid hsl(var(--border));
    align-content: start;
  }
}

@media (max-width: 768px) {
  .login-shell {
    padding: 16px;
  }

  .login-shell__brand,
  .login-shell__form {
    padding: 24px 20px;
  }

  .login-shell__title {
    font-size: 30px;
  }
}
</style>
