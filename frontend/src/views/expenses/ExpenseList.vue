<template>
  <div class="expense-page-shell">
    <AppPageHeader
      class="expense-page-header"
      eyebrow="Expenses"
      title="费用管理"
      description="查看普通费用报销与零星用工记录，保留原有筛选、导出和维护能力。"
    />

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
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
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
  padding-top: 20px;
}

.expense-page-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.expense-page-tabs :deep(.el-tabs__nav-wrap) {
  padding: 4px;
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  background: var(--workspace-panel-muted);
}

.expense-page-tabs :deep(.el-tab-pane) {
  min-width: 0;
}

.expense-page-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.expense-page-tabs :deep(.el-tabs__item) {
  height: 40px;
  padding: 0 16px;
  border-radius: 10px;
  color: var(--text-secondary);
  font-weight: 600;
}

.expense-page-tabs :deep(.el-tabs__item.is-active) {
  color: var(--text-primary);
  background: var(--surface-panel);
}
</style>
