<template>
  <div style="padding: 20px; font-family: monospace;">
    <h1>API 连接测试</h1>
    <el-button @click="testAPI" type="primary">测试 API 连接</el-button>
    <el-button @click="testRouter" type="success">测试路由跳转</el-button>
    <div v-if="result" style="margin-top: 20px; white-space: pre-wrap;">{{ result }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/utils/request'

const router = useRouter()
const result = ref('')

const testAPI = async () => {
  result.value = '测试中...\n'
  
  try {
    result.value += '1. 检查 token...\n'
    const token = localStorage.getItem('token')
    if (!token) {
      result.value += '❌ 未找到 token\n'
      return
    }
    result.value += `✓ token 存在: ${token.substring(0, 20)}...\n`
    
    result.value += '\n2. 调用上游合同 API...\n'
    const data = await request({
      url: '/contracts/upstream/',
      method: 'get',
      params: { page: 1, page_size: 1 }
    })
    result.value += `✓ API 调用成功!\n`
    result.value += `  总数: ${data.total}\n`
    result.value += `  返回: ${data.items.length} 条数据\n`
    if (data.items.length > 0) {
      result.value += `  第一条: ${data.items[0].contract_name}\n`
    }
  } catch (e) {
    result.value += `❌ 错误: ${e.message}\n`
    result.value += `  详情: ${JSON.stringify(e.response?.data || e, null, 2)}\n`
  }
}

const testRouter = () => {
  result.value = '尝试跳转到上游合同页面...\n'
  router.push('/contracts/upstream')
}
</script>
