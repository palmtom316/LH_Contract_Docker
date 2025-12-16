<template>
  <div class="app-wrapper" :class="{ mobile: isMobile, openSidebar: !isCollapse }">
    <!-- Mobile Overlay -->
    <div v-if="isMobile && !isCollapse" class="drawer-bg" @click="closeSidebar" />

    <!-- Sidebar -->
    <div class="sidebar-container" :class="{ 'collapsed': isCollapse }">
      <div class="logo-wrapper">
        <img v-if="!isCollapse" :src="logoUrl" class="logo-img" alt="logo" />
        <el-icon v-else class="logo-icon"><Monitor /></el-icon>
        <transition name="fade">
          <span v-if="!isCollapse" class="logo-text">蓝海合同管理</span>
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
        <!-- 首页概览 - 需要 view_dashboard 权限 -->
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
        
        <!-- 报表统计 - 需要 view_reports 权限 -->
        <el-menu-item v-if="userStore.canViewReports" index="/reports">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>报表统计</template>
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
    </div>

    <!-- Main Container -->
    <div class="main-container" :class="{ 'collapsed': isCollapse }">
      <!-- Navbar -->
      <div class="navbar">
        <div class="left-panel">
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox, ElMessage } from 'element-plus'
import request from '@/utils/request'
import logoNew from '@/assets/logo_new.png'
import { getLogo } from '@/api/system'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)
const isMobile = ref(false)
const logoUrl = ref(logoNew)

const variables = {
  menuBg: '#001529',
  menuText: 'rgba(255, 255, 255, 0.65)',
  menuActiveText: '#1890FF',
  primary: '#1890FF'
}

const activeMenu = computed(() => route.path)

const checkIsMobile = () => {
  const rect = document.body.getBoundingClientRect()
  return rect.width - 1 < 992
}

const resizeHandler = () => {
  if (!document.hidden) {
    const mobile = checkIsMobile()
    isMobile.value = mobile
    if (mobile) {
      isCollapse.value = true
    } else {
      isCollapse.value = false
    }
  }
}

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
  resizeHandler()
  window.addEventListener('resize', resizeHandler)
  
  // Load logo
  getLogo().then(res => {
     if (res.path) {
        const baseUrl = import.meta.env.VITE_API_BASE_URL ? import.meta.env.VITE_API_BASE_URL.replace(/\/api\/v1\/?$/, '') : 'http://localhost:8000' 
        logoUrl.value = baseUrl + res.path + '?t=' + new Date().getTime()
     }
  }).catch(e => console.error("Logo load err", e))
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeHandler)
})
</script>

<style scoped lang="scss">
.app-wrapper {
  display: flex;
  width: 100%;
  height: 100vh;
  position: relative;
  
  &.mobile.openSidebar {
    position: fixed;
    top: 0;
  }
}

.drawer-bg {
  background: #000;
  opacity: 0.3;
  width: 100%;
  top: 0;
  height: 100%;
  position: absolute;
  z-index: 999;
}

.sidebar-container {
  width: var(--sidebar-width);
  height: 100%;
  background-color: #001529;
  transition: width 0.3s;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  z-index: 1001;
  overflow: hidden;
  
  &.collapsed {
    width: 64px;
    
    .logo-text {
      display: none;
    }
  }
  
  .logo-wrapper {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-weight: bold;
    font-size: 18px;
    background-color: #002140;
    white-space: nowrap;
    overflow: hidden;
    
    .logo-img {
      width: 25px; // Adjust based on preference
      height: 25px;
      margin-right: 12px;
    }

    .logo-icon {
      font-size: 24px;
      margin-right: 12px;
      color: #fff;
    }
  }
  
  .el-menu-vertical {
    border-right: none;
    flex: 1;
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  transition: margin-left 0.3s;
  position: relative;
  
  .navbar {
    height: var(--header-height);
    background: #fff;
    box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
    
    .left-panel {
      display: flex;
      align-items: center;
      
      .hamburger {
        font-size: 20px;
        cursor: pointer;
        margin-right: 20px;
        color: var(--color-text-main);
        
        &:hover {
          color: var(--color-primary);
        }
      }
    }
    
    .right-panel {
      .avatar-wrapper {
        display: flex;
        align-items: center;
        cursor: pointer;
        
        .user-name {
          margin: 0 8px;
          font-size: 14px;
          color: var(--color-text-main);
        }
      }
    }
  }
  
  .app-main {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    background-color: var(--color-bg);
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
    transition: transform 0.3s;
    
    &.collapsed { // Actually closed in mobile context if we map collapsed to closed
       // Logic handled by transform
    }
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
  transition: all 0.3s;
}
.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}
.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
