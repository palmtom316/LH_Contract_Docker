<template>
  <div class="mobile-layout">
    <!-- Top Navigation Bar -->
    <van-nav-bar
      v-if="showNavBar"
      :title="pageTitle"
      :left-text="showBack ? '返回' : ''"
      :left-arrow="showBack"
      fixed
      placeholder
      @click-left="onClickLeft"
    />

    <!-- Main Content -->
    <div class="mobile-content">
      <router-view />
    </div>

    <!-- Bottom Navigation -->
    <van-tabbar v-model="activeTab" route safe-area-inset-bottom class="mobile-tabbar">
      <van-tabbar-item to="/m/contracts" icon="orders-o">合同</van-tabbar-item>
      <van-tabbar-item to="/m/reports" icon="chart-trending-o">报表</van-tabbar-item>
      <van-tabbar-item to="/m/profile" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { 
  Tabbar as VanTabbar, 
  TabbarItem as VanTabbarItem,
  NavBar as VanNavBar 
} from 'vant';

const route = useRoute();
const router = useRouter();
const activeTab = ref(0);

const pageTitle = computed(() => route.meta.title as string || '蓝海合同');

// Show NavBar on relevant pages (Reports, Profile)
// potentially hide on Contracts if it has its own search bar
const showNavBar = computed(() => {
  // Always show navbar for consistency, or customize:
  // return route.path !== '/m/contracts'; 
  return true;
});

// Show Back button everywhere (User requirement)
const showBack = computed(() => {
  return true;
});

const onClickLeft = () => {
  if (showBack.value) {
    // Check if we are on the "Home" page
    if (route.path.replace(/\/$/, '') === '/m/contracts') {
       // User functionality: "Return to where I came from" (e.g. Login or PC view)
       router.back();
    } else {
       // On other tabs, go to Home "Contracts"
       router.push('/m/contracts');
    }
  }
};
</script>

<style scoped>
.mobile-layout {
  min-height: 100vh;
  background-color: #f7f8fa;
  display: flex;
  flex-direction: column;
}

.mobile-content {
  flex: 1;
  padding-bottom: 50px; /* Space for tabbar */
  overflow-x: hidden; /* Prevent horizontal scroll from PC components */
}

.mobile-tabbar {
  z-index: 1000;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
}

:deep(.van-nav-bar__content) {
  background-color: #fff;
}
</style>
