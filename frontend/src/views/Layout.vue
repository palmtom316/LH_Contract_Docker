<template>
  <div class="app-wrapper" :class="{ mobile: isMobile, openSidebar: !isCollapse }">
    <!-- Mobile Overlay -->
    <div v-if="isMobile && !isCollapse" class="drawer-bg" @click="closeSidebar" />

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
        <span>Version {{ version }}</span>
      </div>
    </div>

    <!-- Main Container -->
    <div class="main-container" :class="{ 'collapsed': isCollapse }">
      <!-- Navbar -->
      <div class="navbar">
        <div class="left-panel">
          <!-- Mobile Back Button -->
          <!-- Hamburger (Visible on all devices) -->
          <el-icon class="hamburger" @click="toggleSidebar">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>

          <el-breadcrumb separator="/" class="breadcrumb hidden-xs-only">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="right-panel">
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="avatar-wrapper">
              <el-avatar size="small" :icon="'UserFilled'" :style="{ backgroundColor: variables.primary }" />
              <span class="user-name">{{ userStore.user.full_name || userStore.user.username }}</span>
              <el-tag size="small" type="info" style="margin-left: 8px;">{{ userStore.roleDisplay }}</el-tag>
              <el-icon><CaretBottom /></el-icon>
            </div>
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
import { Fold, Expand, Monitor, HomeFilled, Document, DocumentCopy, FolderChecked, Money, DataAnalysis, Setting, UserFilled, CaretBottom, ArrowLeft } from '@element-plus/icons-vue'

const systemVersion = ref('Version 1.5.3')

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
  menuBg: '#001529',
  menuText: 'rgba(255, 255, 255, 0.65)',
  menuActiveText: '#1890FF',
  primary: '#1890FF'
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
    }).then(() => {
      userStore.logout()
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
  background-color: #f0f2f5;
  
  &.mobile.openSidebar {
    position: fixed;
    top: 0;
  }
}

.drawer-bg {
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
  width: 100%;
  top: 0;
  height: 100%;
  position: absolute;
  z-index: 999;
  transition: all 0.3s;
}

/* Sidebar Modernization */
.sidebar-container {
  width: var(--sidebar-width);
  height: 100%;
  background: linear-gradient(180deg, #001529 0%, #00284d 100%);
  transition: width 0.3s cubic-bezier(0.25, 0.8, 0.5, 1);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  z-index: 1001;
  overflow: hidden;
  box-shadow: 4px 0 15px rgba(0, 0, 0, 0.1);
  
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
    color: #fff;
    font-weight: bold;
    font-size: 16px;
    background: rgba(255, 255, 255, 0.05); /* Glass effect */
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
      color: #409EFF; /* Accent color */
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
        opacity: 0.6;
        margin-top: 2px;
        font-family: 'Helvetica Neue', Arial, sans-serif;
      }
    }
  }
  
  .el-menu-vertical {
    border-right: none;
    flex: 1;
    
    :deep(.el-menu-item) {
       &:hover {
         background-color: rgba(255, 255, 255, 0.05) !important;
       }
       &.is-active {
         background: linear-gradient(90deg, #1890FF 0%, rgba(24, 144, 255, 0.1) 100%) !important;
         border-right: 3px solid #1890FF;
       }
    }
  }

  .sidebar-info {
    height: 40px;
    display: flex;
    justify-content: center;
    align-items: center;
    color: rgba(255, 255, 255, 0.3);
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
  background-color: #f5f7fa;
  
  .navbar {
    height: var(--header-height);
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
    position: sticky;
    top: 0;
    z-index: 1000;
    transition: all 0.3s;
    
    &:hover {
        background: #fff;
        box-shadow: 0 4px 25px rgba(0, 0, 0, 0.05);
    }
    
    .left-panel {
      display: flex;
      align-items: center;
      
      .hamburger {
        font-size: 22px;
        cursor: pointer;
        margin-right: 20px;
        color: #606266;
        transition: color 0.3s;
        
        &:hover {
          color: #409EFF;
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
        padding: 5px 10px;
        border-radius: 20px;
        transition: background-color 0.3s;
        
        &:hover {
            background-color: #f5f7fa;
        }
        
        .user-name {
          margin: 0 8px;
          font-size: 14px;
          color: #303133;
          font-weight: 500;
        }
      }
    }
  }
  
  .app-main {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    background-color: transparent;
    /* Optional: Add a subtle texture or gradient to the main user area if desired, 
       but typically 'clean' means solid color */
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
