<template>
  <div class="expense-page-shell">
    <AppWorkspacePanel panel-class="expense-page-panel">
      <el-tabs v-model="activeTab" class="app-tabs--line expense-page-tabs">
        <el-tab-pane label="普通费用报销" name="valuable">
          <OrdinaryExpenseList />
        </el-tab-pane>
        <el-tab-pane label="零星用工管理" name="zeroHourLabor">
          <ZeroHourLaborList />
        </el-tab-pane>
      </el-tabs>
    </AppWorkspacePanel>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'
import OrdinaryExpenseList from './OrdinaryExpenseList.vue'
import ZeroHourLaborList from './ZeroHourLaborList.vue'

const activeTab = ref('valuable')
</script>

<style scoped lang="scss">
.expense-page-shell {
  display: grid;
  gap: var(--workspace-shell-gap);
}

.expense-page-panel {
  padding-top: 4px;
}

.expense-page-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
}

.expense-page-tabs :deep(.el-tab-pane) {
  min-width: 0;
}
</style>
