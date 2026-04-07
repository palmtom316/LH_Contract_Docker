<template>
  <button
    type="button"
    class="notification-bell app-chrome-icon-button"
    :class="{ 'notification-bell--has-unread': unreadCount > 0 }"
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
  cursor: pointer;
}

.notification-bell--has-unread :deep(.el-badge__content) {
  box-shadow: 0 0 0 3px hsl(var(--card) / 0.95);
  animation: notification-pulse 2.4s ease-out infinite;
}

@keyframes notification-pulse {
  0%, 100% {
    transform: scale(1);
  }

  20% {
    transform: scale(1.08);
  }

  40% {
    transform: scale(1);
  }
}
</style>
