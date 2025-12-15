<template>
  <div class="test-page">
    <h1>Contract Page Test</h1>
    <el-button @click="testImports">Test Imports</el-button>
    <div v-if="result">{{ result }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const result = ref('')

const testImports = async () => {
  try {
    // Test download utils
    const downloadModule = await import('@/utils/download')
    result.value = 'Download module loaded: ' + Object.keys(downloadModule).join(', ')
  } catch (e) {
    result.value = 'Error: ' + e.message
  }
}
</script>
