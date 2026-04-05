<template>
  <div class="shell" :class="{ mobile: isMobile }">
    <button
      v-if="isMobile && !isCollapse"
      class="shell-overlay"
      type="button"
      aria-label="关闭侧边栏"
      @click="closeSidebar"
    />

    <aside class="sidebar" :class="{ collapsed: isCollapse }">
      <div class="brand">
        <img v-if="!isCollapse" :src="displayLogo" class="brand-logo" alt="logo" />
        <el-icon v-else class="brand-icon"><Monitor /></el-icon>
        <div v-if="!isCollapse" class="brand-text">
          <span>{{ displayName }}</span>
          <small>{{ displayNameLine2 }}</small>
        </div>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        class="sidebar-menu"
        router
      >
        <el-menu-item v-if="userStore.canViewDashboard" index="/">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页概览</template>
        </el-menu-item>
        <el-menu-item v-if="userStore.canViewUpstreamContracts" index="/contracts/upstream">
          <el-icon><Document /></el-icon>
          <template #title>上游合同</template>
        </el-menu-item>
        <el-menu-item v-if="userStore.canViewDownstreamContracts" index="/contracts/downstream">
          <el-icon><DocumentCopy /></el-icon>
          <template #title>下游合同</template>
        </el-menu-item>
        <el-menu-item v-if="userStore.canViewManagementContracts" index="/contracts/management">
          <el-icon><FolderChecked /></el-icon>
          <template #title>管理合同</template>
        </el-menu-item>
        <el-menu-item v-if="userStore.canViewExpenses" index="/expenses">
          <el-icon><Money /></el-icon>
          <template #title>无合同费用</template>
        </el-menu-item>
        <el-menu-item v-if="userStore.canViewReports" index="/reports">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>报表导出</template>
        </el-menu-item>
        <el-menu-item v-if="userStore.canManageUsers" index="/system">
          <el-icon><Setting /></el-icon>
          <template #title>系统管理</template>
        </el-menu-item>
        <el-menu-item v-if="userStore.isAdmin" index="/audit">
          <el-icon><Document /></el-icon>
          <template #title>审计日志</template>
        </el-menu-item>
      </el-menu>

      <div v-if="!isCollapse" class="sidebar-footer">
        <SidebarUserCard @change-password="openChangePasswordDialog" @logout="confirmLogout" />
        <small class="system-version">{{ systemVersion }}</small>
      </div>
    </aside>

    <main class="content" :class="{ collapsed: isCollapse }">
      <header class="topbar">
        <div class="topbar-left">
          <button type="button" class="menu-btn" aria-label="切换侧边栏" @click="toggleSidebar">
            <el-icon>
              <Fold v-if="!isCollapse" />
              <Expand v-else />
            </el-icon>
          </button>
          <el-breadcrumb separator="/" class="breadcrumb hidden-xs-only">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <AppTopbarActions :unread-count="unreadCount" @command="handleCommand" />
      </header>

      <section class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </section>
    </main>

    <el-drawer
      v-model="uiStore.notificationDrawerOpen"
      :size="isMobile ? '100%' : '420px'"
      direction="rtl"
      title="系统通知"
      append-to-body
      @close="uiStore.closeNotificationDrawer()"
    >
      <NotificationCenter />
    </el-drawer>

    <el-dialog title="修改密码" v-model="changePwdVisible" width="400px" :close-on-click-modal="false">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="100px">
        <el-form-item label="当前密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password placeholder="请输入当前密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="请输入新密码（至少6位）" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="pwdForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="changePwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="changingPwd" @click="handleChangePassword">确定</el-button>
      </template>
    </el-dialog>

    <ContractQueryBot />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataAnalysis, Document, DocumentCopy, Expand, Fold, FolderChecked, HomeFilled, Money, Monitor, Setting } from '@element-plus/icons-vue'
import pkg from '../../package.json'
import logoNew from '@/assets/logo_new.png'
import request from '@/utils/request'
import { useDevice } from '@/composables/useDevice'
import { useSystemStore } from '@/stores/system'
import { useUiStore } from '@/stores/ui'
import { useUserStore } from '@/stores/user'
import ContractQueryBot from '@/components/ContractQueryBot.vue'
import AppTopbarActions from '@/components/layout/AppTopbarActions.vue'
import SidebarUserCard from '@/components/layout/SidebarUserCard.vue'
import NotificationCenter from '@/views/notifications/NotificationCenter.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const systemStore = useSystemStore()
const uiStore = useUiStore()
const { isMobile } = useDevice()

const isCollapse = ref(false)
const systemVersion = ref(`Version ${pkg.version}`)
const changePwdVisible = ref(false)
const changingPwd = ref(false)
const pwdFormRef = ref(null)

const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const unreadCount = computed(() => {
  const items = systemStore.notifications || []
  const unread = items.filter(item => item.read === false).length
  return unread > 0 ? unread : items.length
})
const activeMenu = computed(() => route.path)
const displayLogo = computed(() => {
  if (systemStore.config.system_logo) {
    return systemStore.config.system_logo.startsWith('http')
      ? systemStore.config.system_logo
      : (import.meta.env.VITE_API_BASE_URL?.replace(/\/api\/v1\/?$/, '') || '') + systemStore.config.system_logo
  }
  return logoNew
})
const displayName = computed(() => systemStore.config.system_name || '蓝海合同管理')
const displayNameLine2 = computed(() => systemStore.config.system_name_line_2 || '')

watch(isMobile, (mobile) => {
  isCollapse.value = mobile
}, { immediate: true })

watch(() => uiStore.notificationDrawerOpen, async (open) => {
  if (open && !systemStore.notifications.length) {
    try {
      await systemStore.fetchNotifications()
    } catch {
      // Errors are rendered by NotificationCenter.
    }
  }
})

watch(route, () => {
  if (isMobile.value && !isCollapse.value) isCollapse.value = true
})

function toggleSidebar() {
  isCollapse.value = !isCollapse.value
}

function closeSidebar() {
  isCollapse.value = true
}

function openChangePasswordDialog() {
  pwdForm.old_password = ''
  pwdForm.new_password = ''
  pwdForm.confirm_password = ''
  changePwdVisible.value = true
}

function validateConfirmPwd(rule, value, callback) {
  if (value !== pwdForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
    return
  }
  callback()
}

const pwdRules = {
  old_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度6-100个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPwd, trigger: 'blur' }
  ]
}

async function handleChangePassword() {
  if (!pwdFormRef.value) return
  await pwdFormRef.value.validate(async (valid) => {
    if (!valid) return
    changingPwd.value = true
    try {
      await request({
        url: '/auth/change-password',
        method: 'post',
        data: { old_password: pwdForm.old_password, new_password: pwdForm.new_password }
      })
      ElMessage.success('密码修改成功')
      changePwdVisible.value = false
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '密码修改失败')
    } finally {
      changingPwd.value = false
    }
  })
}

function confirmLogout() {
  ElMessageBox.confirm('确定要退出登录吗?', '提示', { type: 'warning' }).then(async () => {
    await userStore.logout()
    router.push('/login')
  })
}

function handleCommand(command) {
  if (command === 'logout') {
    confirmLogout()
    return
  }
  if (command === 'changePassword') {
    openChangePasswordDialog()
    return
  }
  if (command === 'profile') {
    router.push('/system')
  }
}

onMounted(() => {
  systemStore.fetchConfig()
})
</script>

<style scoped lang="scss">
.shell {
  display: flex;
  width: 100%;
  min-height: 100vh;
  background: var(--surface-page);
}

.shell-overlay {
  position: fixed;
  inset: 0;
  border: 0;
  background: rgba(2, 6, 23, 0.45);
  z-index: 40;
}

.sidebar {
  width: 260px;
  min-height: 100vh;
  background: var(--surface-sidebar);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  z-index: 41;
}

.sidebar.collapsed {
  width: 70px;
}

.brand {
  padding: 16px 14px;
  min-height: 68px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-logo {
  width: 34px;
  height: 34px;
  object-fit: cover;
  border-radius: 8px;
}

.brand-icon {
  color: var(--text-inverse);
  font-size: 22px;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  color: var(--text-inverse);
  font-weight: 600;
}

.brand-text small {
  font-size: 11px;
  color: rgba(248, 250, 252, 0.68);
}

.sidebar-menu {
  border-right: 0;
  background: transparent;
  flex: 1;
}

.sidebar-footer {
  padding: 12px;
}

.system-version {
  display: block;
  margin-top: 8px;
  color: rgba(248, 250, 252, 0.55);
  font-size: 11px;
}

.content {
  flex: 1;
  min-width: 0;
}

.topbar {
  height: 64px;
  padding: 0 18px;
  border-bottom: 1px solid var(--border-subtle);
  background: var(--surface-panel);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.menu-btn {
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: var(--surface-panel);
  color: var(--text-secondary);
  cursor: pointer;
}

.app-main {
  min-height: calc(100vh - 64px);
}

:deep(.el-menu) {
  background: transparent !important;
}

:deep(.el-menu-item) {
  color: rgba(248, 250, 252, 0.78);
}

:deep(.el-menu-item:hover) {
  background: rgba(148, 163, 184, 0.18) !important;
}

:deep(.el-menu-item.is-active) {
  color: var(--text-inverse) !important;
  background: rgba(148, 163, 184, 0.28) !important;
}

@media (max-width: 767px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    transform: translateX(0);
  }

  .sidebar.collapsed {
    transform: translateX(-100%);
    width: 260px;
  }

  .topbar {
    padding: 0 12px;
  }

  .breadcrumb {
    display: none;
  }
}
</style>
