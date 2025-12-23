<template>
  <div class="app-container">
    <el-tabs v-model="activeTab" type="border-card" class="demo-tabs">
      <el-tab-pane label="普通费用报销" name="valuable">
        <OrdinaryExpenseList />
      </el-tab-pane>
      <el-tab-pane label="零星用工管理" name="zeroHourLabor">
        <ZeroHourLaborList />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import OrdinaryExpenseList from './OrdinaryExpenseList.vue'
import ZeroHourLaborList from './ZeroHourLaborList.vue'

const activeTab = ref('valuable')
</script>

<style scoped>
.app-container {
  padding: 20px;
}
</style>
