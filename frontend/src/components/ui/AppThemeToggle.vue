<template>
  <button
    type="button"
    class="theme-toggle inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-card text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
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
  cursor: pointer;
}
</style>
