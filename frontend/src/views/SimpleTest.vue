<template>
  <div class="simple-test">
    <h1>简单测试页面</h1>
    <p>如果您能看到这个页面，说明路由是正常的。</p>
    <el-button type="primary" @click="loadData">加载合同数据</el-button>
    <div v-if="loading">加载中...</div>
    <div v-else-if="error" style="color: red;">错误: {{ error }}</div>
    <div v-else-if="contracts.length > 0">
      <h2>成功加载 {{ contracts.length }} 条数据：</h2>
      <ul>
        <li v-for="c in contracts" :key="c.id">{{ c.contract_name }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { getContracts } from '@/api/contractUpstream'

const loading = ref(false)
const error = ref('')
const contracts = ref([])

const loadData = async () => {
  loading.value = true
  error.value = ''
  contracts.value = []
  
  try {
    const res = await getContracts({ page: 1, page_size: 5 })
    contracts.value = res.items
    console.log('加载成功:', res)
  } catch (e) {
    error.value = e.message || String(e)
    console.error('加载失败:', e)
  } finally {
    loading.value = false
  }
}
</script>
