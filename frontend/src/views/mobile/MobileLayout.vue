<template>
  <div class="mobile-shell">
    <div class="mobile-shell__frame">
      <header class="mobile-topbar">
        <button type="button" class="menu-trigger" aria-label="打开菜单" @click="drawerOpen = true">
          <van-icon name="wap-nav" />
        </button>
        <div class="mobile-topbar__copy">
          <span class="mobile-topbar__eyebrow">Workspace</span>
          <h1 class="mobile-title">{{ pageTitle }}</h1>
        </div>
        <AppTopbarActions :unread-count="unreadCount" />
      </header>

      <main class="mobile-content">
        <router-view />
      </main>
    </div>

    <van-tabbar v-model="activeTab" route safe-area-inset-bottom class="mobile-tabbar">
      <van-tabbar-item to="/m/contracts" icon="orders-o">合同</van-tabbar-item>
      <van-tabbar-item to="/m/expenses" icon="gold-coin-o">费用</van-tabbar-item>
      <van-tabbar-item to="/m/reports" icon="chart-trending-o">报表</van-tabbar-item>
      <van-tabbar-item v-if="userStore.canManageUsers" to="/m/profile" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>

    <van-popup v-model:show="drawerOpen" position="left" class="menu-drawer" :style="{ width: drawerWidth, height: '100%' }">
      <nav class="drawer-nav">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="drawer-link"
          @click="drawerOpen = false"
        >
          {{ item.label }}
        </router-link>
      </nav>
      <div class="drawer-user">
        <SidebarUserCard @change-password="openChangePasswordDialog" @logout="confirmLogout" />
      </div>
    </van-popup>

    <van-popup
      v-model:show="uiStore.notificationDrawerOpen"
      position="right"
      class="notification-popup"
      :style="{ width: '100%', height: '100%' }"
    >
      <NotificationCenter />
    </van-popup>

    <el-dialog title="修改密码" v-model="changePwdVisible" :width="dialogWidth" :close-on-click-modal="false">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="88px">
        <el-form-item label="当前密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="pwdForm.confirm_password" type="password" show-password />
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
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Icon as VanIcon, Popup as VanPopup, Tabbar as VanTabbar, TabbarItem as VanTabbarItem } from 'vant'
import request from '@/utils/request'
import { useSystemStore } from '@/stores/system'
import { useUiStore } from '@/stores/ui'
import { useUserStore } from '@/stores/user'
import { useDevice } from '@/composables/useDevice'
import AppTopbarActions from '@/components/layout/AppTopbarActions.vue'
import NotificationCenter from '@/views/notifications/NotificationCenter.vue'
import SidebarUserCard from '@/components/layout/SidebarUserCard.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const systemStore = useSystemStore()
const uiStore = useUiStore()
const { isTablet, isLandscape, screenWidth } = useDevice()

const activeTab = ref(0)
const drawerOpen = ref(false)
const changePwdVisible = ref(false)
const changingPwd = ref(false)
const pwdFormRef = ref(null)

const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const pageTitle = computed(() => route.meta.title || '合同管理')
const drawerWidth = computed(() => {
  if (screenWidth.value <= 480) return '100%'
  if (isTablet.value && isLandscape.value) return '360px'
  if (isTablet.value) return '420px'
  return '84%'
})
const dialogWidth = computed(() => {
  if (screenWidth.value <= 480) return '100%'
  if (isTablet.value) return '560px'
  return '92%'
})
const unreadCount = computed(() => {
  const items = systemStore.notifications || []
  return items.filter(item => item.unread !== false).length
})
const menuItems = computed(() => {
  const items = []
  if (userStore.canViewUpstreamContracts) items.push({ path: '/m/contracts', label: '合同列表' })
  if (userStore.canViewExpenses) items.push({ path: '/m/expenses', label: '无合同费用' })
  if (userStore.canViewReports) items.push({ path: '/m/reports', label: '报表导出' })
  if (userStore.canManageUsers) items.push({ path: '/m/profile', label: '系统管理' })
  return items
})

watch(() => uiStore.notificationDrawerOpen, async (open) => {
  if (open && !systemStore.notifications.length) {
    try {
      await systemStore.fetchNotifications()
    } catch {
      // NotificationCenter renders the load error.
    }
  }
})

function openChangePasswordDialog() {
  pwdForm.old_password = ''
  pwdForm.new_password = ''
  pwdForm.confirm_password = ''
  drawerOpen.value = false
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
  drawerOpen.value = false
  ElMessageBox.confirm('确定要退出登录吗?', '提示', { type: 'warning' })
    .then(async () => {
      await userStore.logout()
      router.push('/login')
    })
    .catch(() => {})
}

</script>

<style scoped lang="scss">
.mobile-shell {
  min-height: 100vh;
  background: var(--surface-page);
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 12px 0;
}

.mobile-shell__frame {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-rows: auto 1fr;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  background: hsl(var(--card));
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.mobile-topbar {
  min-height: 62px;
  border-bottom: 1px solid hsl(var(--border));
  background: hsl(var(--card));
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr) auto;
  align-items: start;
  gap: 10px;
  padding: 12px 12px 10px;
  position: sticky;
  top: 0;
  z-index: 20;
}

.menu-trigger {
  width: 40px;
  height: 40px;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  background: hsl(var(--card));
  color: var(--text-secondary);
}

.mobile-topbar__copy {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.mobile-topbar__eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.mobile-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-content {
  flex: 1;
  min-height: 0;
  padding: 14px 14px calc(80px + env(safe-area-inset-bottom));
  overflow-x: hidden;
  overflow-y: auto;
}

.mobile-tabbar {
  z-index: 1000;
  margin-bottom: env(safe-area-inset-bottom);
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  background: hsl(var(--card));
  box-shadow: var(--shadow-soft);
  overflow: hidden;
}

.menu-drawer {
  background: hsl(var(--card));
  display: flex;
  flex-direction: column;
}

.drawer-nav {
  padding: 18px 14px;
  display: grid;
  gap: 8px;
  flex: 1;
}

.drawer-link {
  border-radius: var(--radius);
  padding: 10px 12px;
  color: hsl(var(--foreground));
  text-decoration: none;
  background: hsl(var(--muted));
}

.drawer-user {
  padding: 12px;
}

.notification-popup {
  background: var(--surface-page);
}

:deep(.topbar-actions) {
  gap: 6px;
}

.mobile-topbar :deep(.app-chrome-icon-button) {
  width: 40px;
  height: 40px;
  border-radius: var(--radius);
}

@media (min-width: 768px) {
  .mobile-shell {
    padding: 16px 16px 0;
  }

  .mobile-shell__frame {
    width: 100%;
    max-width: 960px;
    margin: 0 auto;
  }

  .mobile-content {
    padding: 18px 18px calc(88px + env(safe-area-inset-bottom));
  }
}

@media (max-width: 480px) {
  .mobile-shell {
    gap: 0;
    padding: 0;
  }

  .mobile-shell__frame {
    border: 0;
    border-radius: 0;
    box-shadow: none;
  }

  .mobile-topbar {
    padding: calc(10px + env(safe-area-inset-top)) 12px 10px;
  }

  .mobile-topbar__eyebrow {
    display: none;
  }

  .mobile-content {
    padding: 12px 12px calc(78px + env(safe-area-inset-bottom));
  }

  .mobile-tabbar {
    border-right: 0;
    border-bottom: 0;
    border-left: 0;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    margin-bottom: 0;
  }
}
</style>
