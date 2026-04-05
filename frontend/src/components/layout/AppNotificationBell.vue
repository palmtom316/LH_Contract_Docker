<template>
  <button
    type="button"
    class="notification-bell"
    :aria-label="ariaLabel"
    @click="uiStore.openNotificationDrawer()"
  >
    <el-badge :value="badgeValue" :hidden="unreadCount <= 0">
      <el-icon><Bell /></el-icon>
    </el-badge>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { useUiStore } from '@/stores/ui'

const props = defineProps({
  unreadCount: {
    type: Number,
    default: 0
  }
})

const uiStore = useUiStore()
const badgeValue = computed(() => (props.unreadCount > 99 ? '99+' : props.unreadCount))
const ariaLabel = computed(() => {
  if (props.unreadCount > 0) {
    return `打开通知抽屉，当前有 ${badgeValue.value} 条未读通知`
  }
  return '打开通知抽屉，当前没有未读通知'
})
</script>

<style scoped lang="scss">
.notification-bell {
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
