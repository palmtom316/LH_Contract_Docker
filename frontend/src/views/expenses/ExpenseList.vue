<template>
  <div class="expense-overview">
    <AppPageHeader
      title="费用管理"
      description="统一管理普通费用报销与零星用工，使用同一套浅深色主题、卡片层级与响应式交互规范。"
    />

    <AppSectionCard>
      <template #header>费用模块</template>
      <el-tabs v-model="activeTab" class="app-tabs expense-overview__tabs">
        <el-tab-pane label="普通费用报销" name="valuable">
          <OrdinaryExpenseList />
        </el-tab-pane>
        <el-tab-pane label="零星用工管理" name="zeroHourLabor">
          <ZeroHourLaborList />
        </el-tab-pane>
      </el-tabs>
    </AppSectionCard>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppPageHeader from '@/components/layout/AppPageHeader.vue'
import AppSectionCard from '@/components/ui/AppSectionCard.vue'
import OrdinaryExpenseList from './OrdinaryExpenseList.vue'
import ZeroHourLaborList from './ZeroHourLaborList.vue'

const activeTab = ref('valuable')
</script>

<style scoped lang="scss">
.expense-overview {
  display: grid;
  gap: 20px;
}

.expense-overview__tabs :deep(.el-tabs__content) {
  padding-top: 20px;
}

.expense-overview__tabs :deep(.el-tab-pane) {
  min-width: 0;
}
</style>
