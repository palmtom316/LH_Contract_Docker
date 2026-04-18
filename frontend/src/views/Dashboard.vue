<template>
  <div class="dashboard-shell">
    <el-tabs v-model="activeTab" class="home-tabs app-tabs--line">
      <el-tab-pane label="概览" name="overview" lazy>
        <Overview />
      </el-tab-pane>
      <el-tab-pane label="经营看板" name="business" lazy>
        <Business />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { defineAsyncComponent, ref } from 'vue'

const Overview = defineAsyncComponent(() => import('./home/Overview.vue'))
const Business = defineAsyncComponent(() => import('./home/Business.vue'))

const activeTab = ref('overview')
</script>

<style scoped lang="scss">
.dashboard-shell {
  display: grid;
  gap: var(--space-4);
}

.home-tabs :deep(.el-tabs__header) {
  margin-bottom: var(--space-4);
}

.home-tabs :deep(.el-tabs__content) {
  overflow: visible;
}
</style>
