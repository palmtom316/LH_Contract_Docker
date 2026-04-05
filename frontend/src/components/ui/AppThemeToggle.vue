<template>
  <button
    type="button"
    class="theme-toggle"
    :aria-label="isDark ? '切换为浅色模式' : '切换为深色模式'"
    @click="uiStore.toggleTheme()"
  >
    <el-icon>
      <Sunny v-if="isDark" />
      <Moon v-else />
    </el-icon>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { Moon, Sunny } from '@element-plus/icons-vue'
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()
const isDark = computed(() => uiStore.theme === 'dark')
</script>

<style scoped lang="scss">
.theme-toggle {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
  background: var(--surface-panel);
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: color 0.2s ease, border-color 0.2s ease, background-color 0.2s ease;

  &:hover {
    color: var(--text-primary);
    border-color: var(--border-strong);
    background: var(--surface-panel-muted);
  }
}
</style>
