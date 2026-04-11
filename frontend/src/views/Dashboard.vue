<template>
  <div class="dashboard-shell">
    <AppWorkspacePanel panel-class="dashboard-tabs-panel">
      <el-tabs v-model="activeTab" class="home-tabs app-tabs--line">
        <el-tab-pane label="概览" name="overview" lazy>
          <div class="dashboard-tab-panel">
            <Overview />
          </div>
        </el-tab-pane>
        <el-tab-pane label="经营看板" name="business" lazy>
          <div class="dashboard-tab-panel">
            <Business />
          </div>
        </el-tab-pane>
      </el-tabs>
    </AppWorkspacePanel>
  </div>
</template>

<script setup>
import { defineAsyncComponent, ref } from 'vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'

const Overview = defineAsyncComponent(() => import('./home/Overview.vue'))
const Business = defineAsyncComponent(() => import('./home/Business.vue'))

const activeTab = ref('overview')
</script>

<style scoped lang="scss">
.dashboard-shell {
  display: grid;
  gap: var(--space-5);
  min-height: calc(100vh - 64px);
}

.dashboard-tabs-panel {
  gap: var(--space-4);
  padding: var(--space-5);
}

.home-tabs {
  min-height: calc(100vh - 240px);
}

.home-tabs :deep(.el-tabs__header) {
  margin-bottom: var(--space-4);
}

.home-tabs :deep(.el-tabs__content) {
  overflow: visible;
}

.dashboard-tab-panel {
  min-height: calc(100vh - 320px);
}

@media (max-width: 767px) {
  .dashboard-shell {
    gap: var(--space-4);
  }

  .dashboard-tabs-panel {
    padding: var(--space-3);
  }

  .home-tabs {
    min-height: auto;
  }
}
</style>
