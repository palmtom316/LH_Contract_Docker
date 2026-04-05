<template>
  <div class="dashboard-shell">
    <el-tabs v-model="activeTab" class="home-tabs">
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
  padding: var(--space-6);
  min-height: calc(100vh - 64px);
  background: var(--surface-page);
}

.home-tabs {
  min-height: calc(100vh - 112px);
  padding: var(--space-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: color-mix(in srgb, var(--surface-panel) 88%, transparent);
  box-shadow: var(--shadow-soft);
}

:deep(.el-tabs__header) {
  margin: 0 0 var(--space-4);
}

:deep(.el-tabs__nav-wrap::after) {
  background: var(--border-subtle);
}

:deep(.el-tabs__item) {
  height: 40px;
  padding: 0 16px;
  border-radius: 999px;
  color: var(--text-secondary);
}

:deep(.el-tabs__item.is-active) {
  color: var(--brand-primary-strong);
  background: var(--brand-primary-soft);
}

:deep(.el-tabs__active-bar) {
  display: none;
}

:deep(.el-tab-pane) {
  min-height: calc(100vh - 196px);
}

@media (max-width: 767px) {
  .dashboard-shell {
    padding: var(--space-4);
  }

  .home-tabs {
    padding: var(--space-2);
    min-height: auto;
  }

  :deep(.el-tabs__item) {
    padding: 0 12px;
    font-size: 13px;
  }
}
</style>
