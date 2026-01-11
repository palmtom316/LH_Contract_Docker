<template>
  <div class="mobile-layout">
    <!-- Main Content -->
    <div class="mobile-content">
      <router-view />
    </div>

    <!-- Bottom Navigation -->
    <van-tabbar v-model="activeTab" route safe-area-inset-bottom>
      <van-tabbar-item to="/m/contracts" icon="orders-o">合同</van-tabbar-item>
      <van-tabbar-item to="/m/reports" icon="chart-trending-o">报表</van-tabbar-item>
      <van-tabbar-item to="/m/profile" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Tabbar as VanTabbar, TabbarItem as VanTabbarItem } from 'vant';

const activeTab = ref(0);
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
}

/* Safe area for iOS */
.van-tabbar {
  padding-bottom: env(safe-area-inset-bottom);
}
</style>
