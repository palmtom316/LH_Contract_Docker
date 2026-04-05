<template>
  <div class="expense-overview">
    <AppSectionCard>
      <el-tabs v-model="activeTab" class="app-tabs--line expense-overview__tabs">
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

.expense-overview__tabs :deep(.el-tab-pane) {
  min-width: 0;
}
</style>
