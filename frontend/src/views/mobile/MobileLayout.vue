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
      <van-tabbar-item to="/m/expenses" icon="gold-coin-o">费用</van-tabbar-item>
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
  const rootTabs = ['/m/contracts', '/m/expenses', '/m/reports', '/m/profile'];
  return !rootTabs.includes(route.path.replace(/\/$/, ''));
});

const onClickLeft = () => {
  if (showBack.value) {
    router.back();
  }
};
</script>

<style scoped>
.mobile-layout {
  min-height: 100vh;
  background-color: var(--surface-page);
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
  box-shadow: 0 -4px 16px rgba(15, 23, 42, 0.08);
}

:deep(.van-nav-bar__content) {
  background-color: rgba(255, 255, 255, 0.98);
}

:deep(.van-nav-bar) {
  border-bottom: 1px solid var(--border-subtle);
}

:deep(.van-nav-bar__title) {
  color: var(--text-primary);
  font-weight: 600;
}

:deep(.van-tabbar) {
  border-top: 1px solid var(--border-subtle);
}

:deep(.van-tabbar-item--active) {
  color: var(--brand-primary);
}
</style>
