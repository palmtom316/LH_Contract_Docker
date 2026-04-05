<template>
  <div class="mobile-shell">
    <header class="mobile-topbar">
      <button type="button" class="menu-trigger" aria-label="打开菜单" @click="drawerOpen = true">
        <van-icon name="wap-nav" />
      </button>
      <h1 class="mobile-title">{{ pageTitle }}</h1>
      <AppTopbarActions :unread-count="unreadCount" />
    </header>

    <main class="mobile-content">
      <router-view />
    </main>

    <van-tabbar v-model="activeTab" route safe-area-inset-bottom class="mobile-tabbar">
      <van-tabbar-item to="/m/contracts" icon="orders-o">合同</van-tabbar-item>
      <van-tabbar-item to="/m/expenses" icon="gold-coin-o">费用</van-tabbar-item>
      <van-tabbar-item to="/m/reports" icon="chart-trending-o">报表</van-tabbar-item>
      <van-tabbar-item to="/m/profile" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>

    <van-popup v-model:show="drawerOpen" position="left" class="menu-drawer" :style="{ width: '84%', height: '100%' }">
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

    <el-dialog title="修改密码" v-model="changePwdVisible" width="92%" :close-on-click-modal="false">
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
import AppTopbarActions from '@/components/layout/AppTopbarActions.vue'
import NotificationCenter from '@/views/notifications/NotificationCenter.vue'
import SidebarUserCard from '@/components/layout/SidebarUserCard.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const systemStore = useSystemStore()
const uiStore = useUiStore()

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

const pageTitle = computed(() => route.meta.title || '蓝海合同')
const unreadCount = computed(() => {
  const items = systemStore.notifications || []
  const unread = items.filter(item => item.read === false).length
  return unread > 0 ? unread : items.length
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
  ElMessageBox.confirm('确定要退出登录吗?', '提示', { type: 'warning' }).then(async () => {
    await userStore.logout()
    router.push('/login')
  })
}

</script>

<style scoped lang="scss">
.mobile-shell {
  min-height: 100vh;
  background: var(--surface-page);
  display: flex;
  flex-direction: column;
}

.mobile-topbar {
  height: 56px;
  border-bottom: 1px solid var(--border-subtle);
  background: var(--surface-panel);
  display: grid;
  grid-template-columns: 36px 1fr auto;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  position: sticky;
  top: 0;
  z-index: 20;
}

.menu-trigger {
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: var(--surface-panel);
  color: var(--text-secondary);
}

.mobile-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-content {
  flex: 1;
  padding-bottom: 50px;
  overflow-x: hidden;
}

.mobile-tabbar {
  z-index: 1000;
  box-shadow: 0 -4px 16px rgba(15, 23, 42, 0.08);
}

.menu-drawer {
  background: var(--surface-sidebar);
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
  border-radius: 10px;
  padding: 10px 12px;
  color: rgba(248, 250, 252, 0.82);
  text-decoration: none;
  background: rgba(148, 163, 184, 0.12);
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

:deep(.topbar-actions .user-menu-trigger) {
  width: 36px;
  padding: 0;
  justify-content: center;
}
</style>
