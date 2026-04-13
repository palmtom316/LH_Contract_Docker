<template>
  <div class="shell" :class="{ mobile: isMobile }">
    <button
      v-if="isMobile && !isCollapse"
      class="shell-overlay"
      type="button"
      aria-label="关闭侧边栏"
      @click="closeSidebar"
    />

    <div class="shell-body">
      <aside class="sidebar" :class="{ collapsed: isCollapse }">
        <div class="brand" :class="{ 'brand--collapsed': isCollapse }">
          <div class="brand-mark">
            <img :src="displayLogo" class="brand-logo" alt="logo" />
          </div>
          <div v-if="!isCollapse" class="brand-text">
            <span>{{ displayName }}</span>
            <small>{{ displayNameLine2 || 'Contract Workspace' }}</small>
          </div>
        </div>

        <div class="sidebar-nav">
          <div class="sidebar-nav__group">
            <button
              v-for="item in primarySidebarItems"
              :key="item.index"
              type="button"
              class="sidebar-nav-item"
              :class="{ 'is-active': isRouteActive(item.index) }"
              :title="isCollapse ? item.label : ''"
              :aria-label="item.label"
              @click="navigateTo(item.index)"
            >
              <span class="sidebar-nav-item__icon">
                <el-icon><component :is="item.icon" /></el-icon>
              </span>
              <span v-if="!isCollapse" class="sidebar-nav-item__label">{{ item.label }}</span>
            </button>
          </div>

          <div v-if="secondarySidebarItems.length" class="sidebar-nav__group sidebar-nav__group--secondary">
            <button
              v-for="item in secondarySidebarItems"
              :key="item.index"
              type="button"
              class="sidebar-nav-item"
              :class="{ 'is-active': isRouteActive(item.index) }"
              :title="isCollapse ? item.label : ''"
              :aria-label="item.label"
              @click="navigateTo(item.index)"
            >
              <span class="sidebar-nav-item__icon">
                <el-icon><component :is="item.icon" /></el-icon>
              </span>
              <span v-if="!isCollapse" class="sidebar-nav-item__label">{{ item.label }}</span>
            </button>
          </div>
        </div>

        <div class="sidebar-footer" :class="{ 'sidebar-footer--collapsed': isCollapse }">
          <SidebarUserCard :compact="isCollapse" @change-password="openChangePasswordDialog" @logout="confirmLogout" />
          <small class="system-version">{{ systemVersion }}</small>
        </div>
      </aside>

      <div class="workspace">
        <main class="content" :class="{ collapsed: isCollapse }">
          <header class="topbar">
            <div class="topbar-left">
              <button type="button" class="menu-btn app-chrome-icon-button" aria-label="切换侧边栏" @click="toggleSidebar">
                <el-icon>
                  <Fold v-if="!isCollapse" />
                  <Expand v-else />
                </el-icon>
              </button>
              <div class="topbar-copy">
                <div class="topbar-copy__title">{{ route.meta.title }}</div>
              </div>
            </div>
            <AppTopbarActions :unread-count="unreadCount" />
          </header>

          <section class="app-main">
            <div class="app-main__frame">
              <router-view v-slot="{ Component }">
                <transition name="fade-transform" mode="out-in">
                  <component :is="Component" />
                </transition>
              </router-view>
            </div>
          </section>
        </main>
      </div>
    </div>

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

  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataAnalysis, Document, DocumentCopy, Expand, Fold, FolderChecked, HomeFilled, Money, Setting } from '@element-plus/icons-vue'
import pkg from '../../package.json'
import logoNew from '@/assets/logo_new.png'
import request from '@/utils/request'
import { useDevice } from '@/composables/useDevice'
import { useSystemStore } from '@/stores/system'
import { useUiStore } from '@/stores/ui'
import { useUserStore } from '@/stores/user'
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
  return items.filter(item => item.unread !== false).length
})
const displayLogo = computed(() => {
  if (!systemStore.config.system_logo) return logoNew
  return systemStore.config.system_logo.startsWith('http')
    ? systemStore.config.system_logo
    : (import.meta.env.VITE_API_BASE_URL?.replace(/\/api\/v1\/?$/, '') || '') + systemStore.config.system_logo
})
const displayName = computed(() => systemStore.config.system_name || '合同管理系统')
const displayNameLine2 = computed(() => systemStore.config.system_name_line_2 || '')

const allSidebarItems = computed(() => [
  userStore.canViewDashboard ? { index: '/', label: '首页概览', icon: HomeFilled, group: 'primary' } : null,
  userStore.canViewUpstreamContracts ? { index: '/contracts/upstream', label: '上游合同', icon: Document, group: 'primary' } : null,
  userStore.canViewDownstreamContracts ? { index: '/contracts/downstream', label: '下游合同', icon: DocumentCopy, group: 'primary' } : null,
  userStore.canViewManagementContracts ? { index: '/contracts/management', label: '管理合同', icon: FolderChecked, group: 'primary' } : null,
  userStore.canViewExpenses ? { index: '/expenses', label: '无合同费用', icon: Money, group: 'primary' } : null,
  userStore.canViewReports ? { index: '/reports', label: '报表导出', icon: DataAnalysis, group: 'secondary' } : null,
  userStore.canManageUsers ? { index: '/system', label: '系统管理', icon: Setting, group: 'secondary' } : null,
  userStore.isAdmin ? { index: '/audit', label: '审计日志', icon: Document, group: 'secondary' } : null
].filter(Boolean))

const primarySidebarItems = computed(() => allSidebarItems.value.filter(item => item.group === 'primary'))
const secondarySidebarItems = computed(() => allSidebarItems.value.filter(item => item.group === 'secondary'))

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

function isRouteActive(index) {
  if (index === '/') return route.path === '/'
  return route.path.startsWith(index)
}

function navigateTo(index) {
  if (!isRouteActive(index)) {
    router.push(index)
  }
  if (isMobile.value) {
    closeSidebar()
  }
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
  ElMessageBox.confirm('确定要退出登录吗?', '提示', { type: 'warning' })
    .then(async () => {
      await userStore.logout()
      router.push('/login')
    })
    .catch(() => {})
}

onMounted(() => {
  systemStore.fetchConfig()
})
</script>

<style scoped lang="scss">
.shell {
  min-height: 100vh;
  width: 100%;
  background: var(--surface-page-gradient);
  position: relative;
}

.shell-body {
  width: 100%;
  min-height: 100vh;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
}

.shell-overlay {
  position: fixed;
  inset: 0;
  border: 0;
  background: rgba(2, 6, 23, 0.35);
  z-index: 40;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--surface-sidebar);
  padding: 0 12px 12px;
  border-right: 1px solid hsl(var(--border));
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar.collapsed {
  width: 88px;
}

.brand {
  padding: 0 8px;
  min-height: var(--shell-header-band-height, var(--header-height));
  display: flex;
  align-items: center;
  gap: 14px;
  border-bottom: 1px solid hsl(var(--border));
  margin-bottom: 12px;
}

.brand--collapsed {
  justify-content: center;
  padding-inline: 0;
}

.brand-mark {
  width: 42px;
  height: 42px;
  border-radius: var(--radius);
  border: 1px solid hsl(var(--border));
  background: var(--surface-sidebar-accent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--shadow-soft);
}

.brand-logo {
  width: 28px;
  height: 28px;
  object-fit: cover;
  border-radius: 8px;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  color: hsl(var(--foreground));
  font-weight: 600;
  gap: 2px;
}

.brand-text span {
  font-size: 15px;
  letter-spacing: -0.015em;
  color: hsl(var(--foreground));
}

.brand-text small {
  font-size: 11px;
  color: hsl(var(--muted-foreground));
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.sidebar-nav {
  flex: 1;
  display: grid;
  gap: 18px;
  align-content: start;
  min-height: 0;
  padding: 4px 0 6px;
}

.sidebar-nav__group {
  display: grid;
  gap: 2px;
}

.sidebar-nav__group--secondary {
  padding-top: 8px;
  border-top: 1px solid hsl(var(--border));
}

.sidebar-nav-item {
  width: 100%;
  min-height: 40px;
  padding: 4px 10px;
  border: 1px solid transparent;
  border-radius: var(--radius);
  background: transparent;
  color: hsl(var(--muted-foreground));
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
  cursor: pointer;
  transition: background-color 160ms ease, border-color 160ms ease, color 160ms ease;
}

.sidebar-nav-item:hover {
  background: var(--surface-sidebar-hover);
  border-color: hsl(var(--border));
  color: hsl(var(--foreground));
}

.sidebar-nav-item.is-active {
  background: var(--surface-sidebar-active);
  border-color: hsl(var(--border));
  color: hsl(var(--foreground));
  box-shadow: none;
}

.sidebar-nav-item__icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: transparent;
  transition: background-color 160ms ease, color 160ms ease;
}

.sidebar-nav-item:hover .sidebar-nav-item__icon,
.sidebar-nav-item.is-active .sidebar-nav-item__icon {
  background: var(--surface-sidebar-accent);
  color: var(--brand-primary-strong);
}

.sidebar-nav-item__label {
  min-width: 0;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
}

.sidebar-footer {
  margin-top: auto;
  padding: 14px 6px 0;
  border-top: 1px solid hsl(var(--border));
  position: sticky;
  bottom: 0;
  background: var(--surface-sidebar);
  display: grid;
  gap: 12px;
}

.sidebar-footer--collapsed {
  justify-items: center;
}

.system-version {
  display: block;
  color: hsl(var(--muted-foreground));
  font-size: 11px;
  text-align: center;
}

.workspace {
  flex: 1;
  display: flex;
  min-width: 0;
  background: transparent;
}

.content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: transparent;
}

.topbar {
  min-height: var(--shell-header-band-height, var(--header-height));
  padding: 0 20px;
  border-bottom: 1px solid hsl(var(--border));
  background: var(--surface-topbar);
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
  flex-shrink: 0;
}

.topbar-copy {
  min-width: 0;
}

.topbar-copy__title {
  color: hsl(var(--foreground));
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.app-main {
  flex: 1;
  padding: 0;
  margin: 0;
  min-width: 0;
}

.app-main__frame {
  min-height: 100%;
  max-width: var(--workspace-max-width);
  margin: 0 auto;
  padding: 20px;
  background: color-mix(in srgb, hsl(var(--card)) 94%, hsl(var(--muted)) 6%);
  border: 1px solid var(--workspace-panel-border);
  border-radius: calc(var(--radius-lg) + 2px);
  box-shadow: var(--shadow-frame);
}

@media (max-width: 1100px) {
  .shell {
    min-height: 100vh;
  }

  .shell-body {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: 41;
    transition: transform 0.3s ease;
  }

  .sidebar.collapsed {
    transform: translateX(-110%);
  }

  .topbar {
    padding: 0 16px;
  }
}

@media (max-width: 767px) {
  .shell {
    padding: 0;
  }

  .topbar {
    position: sticky;
    top: 0;
    z-index: 20;
  }

  .app-main {
    padding-bottom: 0;
  }

  .app-main__frame {
    padding: 16px;
  }
}

.sidebar.collapsed .sidebar-nav-item {
  width: 44px;
  min-height: 44px;
  padding: 0;
  justify-content: center;
  border-radius: var(--radius);
}

.sidebar.collapsed .sidebar-nav-item__icon {
  width: 36px;
  height: 36px;
}
</style>
