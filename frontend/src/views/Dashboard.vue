<template>
  <div class="app-container">
    <el-tabs v-model="activeTab" type="border-card" class="home-tabs">
      <el-tab-pane label="概览" name="overview">
        <Overview />
      </el-tab-pane>
      <el-tab-pane label="经营看板" name="business">
        <Business />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Overview from './home/Overview.vue'
import Business from './home/Business.vue'

const activeTab = ref('overview')
</script>

<style scoped>
.app-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 84px);
}
.home-tabs {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  min-height: 80vh;
}
</style>
