<template>
  <div class="app-wrapper" :class="{ mobile: isMobile, openSidebar: !isCollapse }">
    <!-- Mobile Overlay -->
    <button
      v-if="isMobile && !isCollapse"
      type="button"
      class="drawer-bg"
      aria-label="关闭侧边栏"
      @click="closeSidebar"
    />

    <!-- Sidebar -->
    <div class="sidebar-container" :class="{ 'collapsed': isCollapse }">
      <div class="logo-wrapper">
        <img v-if="!isCollapse" :src="displayLogo" class="logo-img" alt="logo" />
        <el-icon v-else class="logo-icon"><Monitor /></el-icon>
        <transition name="fade">
          <div v-if="!isCollapse" class="logo-text-container">
            <span class="logo-text">{{ displayName }}</span>
            <span class="logo-text-sub">{{ displayNameLine2 }}</span>
          </div>
        </transition>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical"
        :background-color="variables.menuBg"
        :text-color="variables.menuText"
        :active-text-color="variables.menuActiveText"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
      >
        <!-- 首页概览 -->
        <el-menu-item v-if="userStore.canViewDashboard" index="/">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页概览</template>
        </el-menu-item>
        
        <!-- 上游合同 - 需要 view_upstream_* 权限 -->
        <el-menu-item v-if="userStore.canViewUpstreamContracts" index="/contracts/upstream">
          <el-icon><Document /></el-icon>
          <template #title>上游合同</template>
        </el-menu-item>
        
        <!-- 下游合同 - 需要 view_downstream_* 权限 -->
        <el-menu-item v-if="userStore.canViewDownstreamContracts" index="/contracts/downstream">
          <el-icon><DocumentCopy /></el-icon>
          <template #title>下游合同</template>
        </el-menu-item>
        
        <!-- 管理合同 - 需要 view_management_* 权限 -->
        <el-menu-item v-if="userStore.canViewManagementContracts" index="/contracts/management">
          <el-icon><FolderChecked /></el-icon>
          <template #title>管理合同</template>
        </el-menu-item>
        
        <!-- 无合同费用 - 需要 view_expenses 权限 -->
        <el-menu-item v-if="userStore.canViewExpenses" index="/expenses">
          <el-icon><Money /></el-icon>
          <template #title>无合同费用</template>
        </el-menu-item>

        <!-- 报表导出 -->
        <el-menu-item v-if="userStore.canViewReports" index="/reports">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>报表导出</template>
        </el-menu-item>
        

        
        <!-- 系统管理 - 仅管理员可见 -->
        <el-menu-item v-if="userStore.canManageUsers" index="/system">
          <el-icon><Setting /></el-icon>
          <template #title>系统管理</template>
        </el-menu-item>
        
        <!-- 审计日志 - 仅管理员可见 -->
        <el-menu-item v-if="userStore.isAdmin" index="/audit">
          <el-icon><Document /></el-icon>
          <template #title>审计日志</template>
        </el-menu-item>
      </el-menu>
      
      <div v-if="!isCollapse" class="sidebar-info">
        <span>{{ systemVersion }}</span>
      </div>
    </div>

    <!-- Main Container -->
    <div class="main-container" :class="{ 'collapsed': isCollapse }">
      <!-- Navbar -->
      <div class="navbar">
        <div class="left-panel">
          <!-- Mobile Back Button -->
          <!-- Hamburger (Visible on all devices) -->
          <button type="button" class="hamburger" aria-label="切换侧边栏" @click="toggleSidebar">
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
        
        <div class="right-panel">
          <el-dropdown trigger="click" @command="handleCommand">
            <button type="button" class="avatar-wrapper" aria-label="打开用户菜单">
              <el-avatar size="small" :icon="UserFilled" :style="{ backgroundColor: variables.primary }" />
              <span class="user-name">{{ userStore.user.full_name || userStore.user.username }}</span>
              <el-tag size="small" effect="plain" class="role-tag">{{ userStore.roleDisplay }}</el-tag>
              <el-icon><CaretBottom /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="changePassword">修改密码</el-dropdown-item>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- App Main -->
      <div class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>

    <!-- Change Password Dialog -->
    <el-dialog 
      title="修改密码" 
      v-model="changePwdVisible" 
      width="400px"
      :close-on-click-modal="false"
    >
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
        <el-button type="primary" @click="handleChangePassword" :loading="changingPwd">确定</el-button>
      </template>
    </el-dialog>

    <!-- Contract Query Bot (合同查询机器人) -->
    <ContractQueryBot />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox, ElMessage } from 'element-plus'
import request from '@/utils/request'
import { useSystemStore } from '@/stores/system'
import logoNew from '@/assets/logo_new.png'
import ContractQueryBot from '@/components/ContractQueryBot.vue'
import { useDevice } from '@/composables/useDevice'
import pkg from '../../package.json'
import { Fold, Expand, Monitor, HomeFilled, Document, DocumentCopy, FolderChecked, Money, DataAnalysis, Setting, UserFilled, CaretBottom } from '@element-plus/icons-vue'

const systemVersion = ref(`Version ${pkg.version}`)

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const systemStore = useSystemStore()

const isCollapse = ref(false)
// isMobile is now imported from useDevice
// Fallback logic handled in template or computed
const displayLogo = computed(() => {
    if (systemStore.config.system_logo) {
         // If it's a relative path starting with /, prepend URL if needed?
         // Store usually stores relative path "/uploads...".
         // We might need to handle full URL if frontend is separate info.
         return systemStore.config.system_logo.startsWith('http') 
            ? systemStore.config.system_logo 
            : (import.meta.env.VITE_API_BASE_URL?.replace(/\/api\/v1\/?$/, '') || '') + systemStore.config.system_logo
    }
    return logoNew
})
const displayName = computed(() => systemStore.config.system_name || '蓝海合同管理')
const displayNameLine2 = computed(() => systemStore.config.system_name_line_2 || '')

const variables = {
  menuBg: 'var(--surface-sidebar)',
  menuText: 'rgba(248, 250, 252, 0.76)',
  menuActiveText: 'var(--text-inverse)',
  primary: 'var(--brand-primary)'
}

const activeMenu = computed(() => route.path)

const { isMobile } = useDevice()

// Auto-collapse sidebar on mobile
watch(isMobile, (val) => {
  if (val) {
    isCollapse.value = true
  } else {
    isCollapse.value = false
  }
}, { immediate: true })

const toggleSidebar = () => {
    isCollapse.value = !isCollapse.value
}

const closeSidebar = () => {
  isCollapse.value = true
}

const handleCommand = (command) => {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗?', '提示', {
      type: 'warning'
    }).then(async () => {
      await userStore.logout()
      router.push('/login')
    })
  } else if (command === 'changePassword') {
    openChangePasswordDialog()
  }
}

// Change Password
const changePwdVisible = ref(false)
const changingPwd = ref(false)
const pwdFormRef = ref(null)

const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const validateConfirmPwd = (rule, value, callback) => {
  if (value !== pwdForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const pwdRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度6-100个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPwd, trigger: 'blur' }
  ]
}

const openChangePasswordDialog = () => {
  pwdForm.old_password = ''
  pwdForm.new_password = ''
  pwdForm.confirm_password = ''
  changePwdVisible.value = true
}

const handleChangePassword = async () => {
  if (!pwdFormRef.value) return
  
  await pwdFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    changingPwd.value = true
    try {
      await request({
        url: '/auth/change-password',
        method: 'post',
        data: {
          old_password: pwdForm.old_password,
          new_password: pwdForm.new_password
        }
      })
      ElMessage.success('密码修改成功')
      changePwdVisible.value = false
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '密码修改失败')
    } finally {
      changingPwd.value = false
    }
  })
}

watch(route, () => {
  if (isMobile.value && !isCollapse.value) {
    isCollapse.value = true
  }
})

onMounted(() => {
  // Load system config
  systemStore.fetchConfig()
})

onBeforeUnmount(() => {
  // Cleanup if needed
})
</script>

<style scoped lang="scss">
/* Modern Layout Styles */
.app-wrapper {
  display: flex;
  width: 100%;
  height: 100vh;
  position: relative;
  background-color: var(--surface-page);
  
  &.mobile.openSidebar {
    position: fixed;
    top: 0;
  }
}

.drawer-bg {
  background: var(--surface-overlay);
  backdrop-filter: blur(2px);
  width: 100%;
  top: 0;
  height: 100%;
  position: absolute;
  z-index: 999;
  transition: all 0.3s;
  border: 0;
  padding: 0;
}

/* Sidebar Modernization */
.sidebar-container {
  width: var(--sidebar-width);
  height: 100%;
  background: var(--surface-sidebar);
  transition: width 0.3s cubic-bezier(0.25, 0.8, 0.5, 1);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  z-index: 1001;
  overflow: hidden;
  box-shadow: 4px 0 18px rgba(15, 23, 42, 0.08);
  
  &.collapsed {
    width: 64px;
    
    .logo-text {
      display: none;
    }
  }
  
  .logo-wrapper {
    height: 70px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-inverse);
    font-weight: bold;
    font-size: 16px;
    background: rgba(255, 255, 255, 0.04);
    white-space: nowrap;
    overflow: hidden;
    padding: 0 10px;
    
    .logo-img {
      width: 40px; 
      height: 40px;
      margin-right: 12px;
      object-fit: contain;
      filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
    }

    .logo-icon {
      font-size: 24px;
      margin-right: 12px;
      color: #8bc0df;
    }

    .logo-text-container {
      display: flex;
      flex-direction: column;
      justify-content: center;
      line-height: 1.2;
      align-items: flex-start;

      .logo-text {
        font-size: 16px;
        letter-spacing: 1px;
      }
      
      .logo-text-sub {
        font-size: 12px;
        font-weight: normal;
        opacity: 0.72;
        margin-top: 2px;
        font-family: var(--font-family-base);
      }
    }
  }
  
  .el-menu-vertical {
    border-right: none;
    flex: 1;
    
    :deep(.el-menu-item) {
       &:hover {
         background-color: var(--surface-sidebar-hover) !important;
       }
       &.is-active {
         background: var(--surface-sidebar-active) !important;
         border-right: 3px solid #8bc0df;
       }
    }
  }

  .sidebar-info {
    height: 40px;
    display: flex;
    justify-content: center;
    align-items: center;
    color: rgba(248, 250, 252, 0.45);
    font-size: 10px;
    background: transparent;
    letter-spacing: 1px;
    border-top: 1px solid rgba(255,255,255,0.05);
  }
}

/* Main Container & Navbar */
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  transition: margin-left 0.3s;
  position: relative;
    background-color: var(--surface-page);
  
  .navbar {
    height: var(--header-height);
    background: rgba(255, 255, 255, 0.96);
    backdrop-filter: blur(8px);
    box-shadow: 0 2px 12px rgba(15, 23, 42, 0.05);
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
    position: sticky;
    top: 0;
    z-index: 1000;
    transition: all 0.3s;
    
    .left-panel {
      display: flex;
      align-items: center;
      
      .hamburger {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        margin-right: 20px;
        color: var(--text-secondary);
        background: transparent;
        border: 1px solid transparent;
        border-radius: 10px;
        cursor: pointer;
        transition: color 0.2s, background-color 0.2s, border-color 0.2s;
        
        &:hover {
          color: var(--brand-primary);
          background-color: var(--brand-primary-soft);
          border-color: var(--border-subtle);
        }
      }

      .mobile-nav-back {
        display: flex;
        align-items: center;
        padding: 8px;
        margin-right: 10px;
        cursor: pointer;
        color: #606266;
        border-radius: 4px;

        .back-text {
          font-size: 16px;
          margin-left: 4px;
          font-weight: 500;
        }

        &:active {
          background-color: #f5f7fa;
        }
      }
      
      .breadcrumb {
          font-size: 14px;
          line-height: normal;
      }
    }
    
    .right-panel {
      .avatar-wrapper {
        display: flex;
        align-items: center;
        cursor: pointer;
        padding: 6px 10px;
        border-radius: 20px;
        transition: background-color 0.2s, border-color 0.2s;
        border: 1px solid transparent;
        background: transparent;
        
        &:hover {
            background-color: var(--surface-panel-muted);
            border-color: var(--border-subtle);
        }
        
        .user-name {
          margin: 0 8px;
          font-size: 14px;
          color: var(--text-primary);
          font-weight: 500;
        }

        .role-tag {
          margin-left: 8px;
          border-color: var(--border-subtle);
          color: var(--text-secondary);
          background: var(--surface-panel);
        }
      }
    }
  }
  
  .app-main {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    background-color: transparent;
  }
}

/* Mobile specific overrides */
.mobile {
  .sidebar-container {
    position: fixed;
    top: 0;
    left: 0;
    height: 100%;
    width: var(--sidebar-width) !important;
    transform: translate3d(-100%, 0, 0);
    transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.5, 1);
    box-shadow: 2px 0 8px rgba(0,0,0,0.15);
  }
  
  &.openSidebar {
    .sidebar-container {
      transform: translate3d(0, 0, 0);
    }
  }
  
  .main-container {
    margin-left: 0 !important;
  }
}

/* Utils */
.hidden-xs-only {
  @media only screen and (max-width: 767px) {
    display: none;
  }
}

.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.5, 1);
}
.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}
.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
