<template>
  <div class="login-shell">
    <div class="login-shell__panel">
      <section class="login-shell__header">
        <div class="login-shell__system-copy">
          <h1 class="login-shell__title">{{ displayName }}</h1>
          <p class="login-shell__subtitle">{{ displayNameLine2 }}</p>
        </div>
      </section>

      <section class="login-shell__form">
        <div class="login-shell__form-copy">
          <h2>账号登录</h2>
          <p>输入用户名和密码后进入业务工作台。</p>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSystemStore } from '@/stores/system'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const systemStore = useSystemStore()
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

const displayName = computed(() => systemStore.config.system_name || '合同管理系统')
const displayNameLine2 = computed(() => systemStore.config.system_name_line_2 || 'Contract Workspace')

onMounted(() => {
  systemStore.fetchConfig()
})

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
  background: var(--surface-page-gradient);
}

.login-shell__panel {
  width: min(560px, 100%);
  display: grid;
  border: 1px solid hsl(var(--border));
  border-radius: calc(var(--radius-lg) + 2px);
  background: color-mix(in srgb, hsl(var(--card)) 94%, hsl(var(--muted)) 6%);
  box-shadow: var(--shadow-frame);
  overflow: hidden;
}

.login-shell__header,
.login-shell__form {
  display: grid;
  min-width: 0;
}

.login-shell__header {
  align-content: start;
  gap: 12px;
  padding: 28px 32px 24px;
  border-bottom: 1px solid hsl(var(--border));
  background: color-mix(in srgb, hsl(var(--muted)) 82%, hsl(var(--card)) 18%);
}

.login-shell__system-copy {
  display: grid;
  gap: 6px;
}

.login-shell__title {
  margin: 0;
  font-size: clamp(28px, 3vw, 34px);
  line-height: 1.08;
  color: hsl(var(--foreground));
  font-weight: 700;
  letter-spacing: -0.03em;
}

.login-shell__subtitle {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: hsl(var(--muted-foreground));
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.login-shell__form {
  display: grid;
  align-content: center;
  gap: 20px;
  padding: 28px 32px 32px;
}

.login-shell__form-copy h2 {
  margin: 0;
  font-size: 20px;
  line-height: 1.2;
  color: hsl(var(--foreground));
}

.login-shell__form-copy p {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: hsl(var(--muted-foreground));
}

.login-form :deep(.el-form-item__label) {
  color: hsl(var(--muted-foreground));
  font-weight: 600;
}

.login-form :deep(.el-input__wrapper) {
  min-height: 40px;
  border-radius: 10px;
  box-shadow: 0 0 0 1px hsl(var(--border)) inset;
  background: hsl(var(--background));
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px hsl(var(--ring)) inset, var(--shadow-focus);
}

.login-form .login-button {
  width: 100%;
  min-height: 40px;
  background-color: hsl(var(--primary));
  border-color: hsl(var(--primary));
  font-weight: 700;
  letter-spacing: 0.08em;
}

.login-form .login-button:hover {
  background-color: hsl(var(--primary) / 0.92);
  border-color: hsl(var(--primary) / 0.92);
}

@media (max-width: 768px) {
  .login-shell {
    padding: 16px;
  }

  .login-shell__header,
  .login-shell__form {
    padding: 24px 20px;
  }

  .login-shell__title {
    font-size: 30px;
  }
}
</style>
