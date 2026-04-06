<template>
  <div class="login-shell">
    <div class="login-shell__panel">
      <section class="login-shell__brand">
        <p class="login-shell__eyebrow">财务与合同业务工作台</p>
        <h1 class="login-shell__title">蓝海合同管理系统</h1>
        <p class="login-shell__subtitle">稳定、安全、适合日常高频录入与审核</p>

        <div class="login-shell__highlights">
          <article class="login-shell__highlight">
            <span class="login-shell__highlight-label">Workspace</span>
            <strong>合同、费用、报表统一入口</strong>
          </article>
          <article class="login-shell__highlight">
            <span class="login-shell__highlight-label">Control</span>
            <strong>延续统一工作台的克制面板语言</strong>
          </article>
          <article class="login-shell__highlight">
            <span class="login-shell__highlight-label">Access</span>
            <strong>登录后直接进入完整业务工作台</strong>
          </article>
        </div>
      </section>

      <section class="login-shell__form">
        <div class="login-shell__form-copy">
          <p>Sign in</p>
          <h2>使用账号密码继续</h2>
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
  background:
    radial-gradient(circle at top left, var(--brand-primary-soft), transparent 34%),
    radial-gradient(circle at bottom right, color-mix(in srgb, var(--brand-accent) 12%, transparent), transparent 32%),
    linear-gradient(180deg, var(--surface-panel-muted) 0%, var(--surface-page) 100%);
}

.login-shell__panel {
  width: min(960px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(360px, 0.95fr);
  gap: 20px;
  padding: 20px;
  border: 1px solid var(--border-subtle);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: var(--shadow-frame);
  backdrop-filter: blur(18px);
}

.login-shell__brand,
.login-shell__form {
  border: 1px solid var(--border-subtle);
  border-radius: 24px;
  background: color-mix(in srgb, var(--surface-panel) 92%, transparent);
}

.login-shell__brand {
  display: grid;
  align-content: space-between;
  gap: 28px;
  padding: 32px;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--brand-primary) 12%, transparent), transparent 38%),
    linear-gradient(180deg, color-mix(in srgb, var(--surface-panel) 96%, transparent), color-mix(in srgb, var(--surface-panel-muted) 72%, var(--surface-panel) 28%));
}

.login-shell__eyebrow {
  margin: 0;
  color: var(--brand-primary);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.login-shell__title {
  margin: 0 0 10px;
  font-size: clamp(32px, 4vw, 42px);
  line-height: 1.06;
  color: var(--text-primary);
  font-weight: 700;
  letter-spacing: -0.03em;
}

.login-shell__subtitle {
  margin: 0;
  max-width: 34ch;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.login-shell__highlights {
  display: grid;
  gap: 12px;
}

.login-shell__highlight {
  display: grid;
  gap: 6px;
  padding: 16px 18px;
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface-panel) 88%, transparent);
}

.login-shell__highlight-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.login-shell__highlight strong {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
}

.login-shell__form {
  display: grid;
  align-content: center;
  gap: 24px;
  padding: 32px;
}

.login-shell__form-copy p {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.login-shell__form-copy h2 {
  margin: 0;
  font-size: 24px;
  line-height: 1.2;
  color: var(--text-primary);
}

.login-form :deep(.el-form-item__label) {
  color: var(--text-secondary);
  font-weight: 600;
}

.login-form :deep(.el-input__wrapper) {
  min-height: 46px;
  border-radius: 12px;
  box-shadow: 0 0 0 1px var(--border-subtle) inset;
  background: var(--surface-panel);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--brand-primary) inset, var(--shadow-focus);
}

.login-form .login-button {
  width: 100%;
  min-height: 46px;
  background-color: var(--text-primary);
  border-color: var(--text-primary);
  font-weight: 700;
  letter-spacing: 0.16em;
}

.login-form .login-button:hover {
  background-color: var(--brand-primary-strong);
  border-color: var(--brand-primary-strong);
}

@media (max-width: 900px) {
  .login-shell__panel {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .login-shell {
    padding: 16px;
  }

  .login-shell__panel {
    padding: 14px;
    border-radius: 24px;
  }

  .login-shell__brand,
  .login-shell__form {
    padding: 24px 20px;
    border-radius: 20px;
  }

  .login-shell__title {
    font-size: 30px;
  }
}
</style>
