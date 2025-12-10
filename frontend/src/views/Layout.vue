<template>
  <div class="app-wrapper" :class="{ mobile: isMobile, openSidebar: !isCollapse }">
    <!-- Mobile Overlay -->
    <div v-if="isMobile && !isCollapse" class="drawer-bg" @click="closeSidebar" />

    <!-- Sidebar -->
    <div class="sidebar-container" :class="{ 'collapsed': isCollapse }">
      <div class="logo-wrapper">
        <el-icon class="logo-icon"><Monitor /></el-icon>
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
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页概览</template>
        </el-menu-item>
        
        <el-menu-item index="/contracts/upstream">
          <el-icon><Document /></el-icon>
          <template #title>上游合同</template>
        </el-menu-item>
        
        <el-menu-item index="/contracts/downstream">
          <el-icon><DocumentCopy /></el-icon>
          <template #title>下游合同</template>
        </el-menu-item>
        
        <el-menu-item index="/contracts/management">
          <el-icon><FolderChecked /></el-icon>
          <template #title>管理合同</template>
        </el-menu-item>
        
        <el-menu-item index="/expenses">
          <el-icon><Money /></el-icon>
          <template #title>费用管理</template>
        </el-menu-item>
        
        <el-menu-item index="/reports">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>报表统计</template>
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
              <el-icon><CaretBottom /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)
const isMobile = ref(false)

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
  }
}

watch(route, () => {
  if (isMobile.value && !isCollapse.value) {
    isCollapse.value = true
  }
})

onMounted(() => {
  resizeHandler()
  window.addEventListener('resize', resizeHandler)
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
    
    .logo-icon {
      font-size: 24px;
      margin-right: 8px;
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
