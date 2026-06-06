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
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'
import OrdinaryExpenseList from './OrdinaryExpenseList.vue'
import ZeroHourLaborList from './ZeroHourLaborList.vue'

const allowedTabs = ['valuable', 'zeroHourLabor']
const route = useRoute()
const router = useRouter()

const normalizeTab = (value) => {
  if (Array.isArray(value)) {
    return value[0]
  }
  return value
}

const getInitialTab = () => {
  const tabFromQuery = normalizeTab(route.query.tab)
  return allowedTabs.includes(tabFromQuery) ? tabFromQuery : 'valuable'
}

const activeTab = ref(getInitialTab())

watch(
  () => normalizeTab(route.query.tab),
  (tab) => {
    if (tab && allowedTabs.includes(tab) && tab !== activeTab.value) {
      activeTab.value = tab
    }
  }
)

watch(
  activeTab,
  (tab) => {
    if (!tab || tab === normalizeTab(route.query.tab)) {
      return
    }
    router.replace({
      query: {
        ...route.query,
        tab
      }
    })
  }
)
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
