<template>
  <el-tooltip content="合同查询" placement="bottom" :show-after="120">
    <button
      type="button"
      class="app-chrome-icon-button contract-query-entry"
      data-testid="contract-query-entry"
      aria-label="打开合同查询"
      @click="$emit('open')"
    >
      <el-icon><DataAnalysis /></el-icon>
      <span class="contract-query-entry__sr">合同查询</span>
    </button>
  </el-tooltip>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { DataAnalysis } from '@element-plus/icons-vue'

const emit = defineEmits(['open'])

function handleHotkey(event) {
  const key = String(event.key || '').toLowerCase()
  if (key !== 'k') return
  if (!event.ctrlKey && !event.metaKey) return
  if (event.altKey || event.shiftKey) return

  event.preventDefault()
  emit('open')
}

onMounted(() => {
  window.addEventListener('keydown', handleHotkey)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleHotkey)
})
</script>

<style scoped lang="scss">
.contract-query-entry {
  position: relative;
}

.contract-query-entry__sr {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
