<template>
  <button
    type="button"
    class="notification-bell app-chrome-icon-button"
    :class="{ 'notification-bell--has-unread': unreadCount > 0 }"
    :aria-label="ariaLabel"
    @click="uiStore.openNotificationDrawer()"
  >
    <el-badge :value="badgeValue" :hidden="unreadCount <= 0">
      <span class="notification-bell__glyph" aria-hidden="true">
        <svg viewBox="0 0 20 20" fill="none">
          <path d="M10 3.1a3.9 3.9 0 0 0-3.9 3.9v1.38c0 .95-.28 1.88-.8 2.67l-.86 1.31a.95.95 0 0 0 .8 1.47h9.52a.95.95 0 0 0 .8-1.47l-.86-1.31a4.83 4.83 0 0 1-.8-2.67V7a3.9 3.9 0 0 0-3.9-3.9Z" />
          <path d="M8.05 15.08a2.07 2.07 0 0 0 3.9 0" />
          <path d="M10 2v1.1" />
        </svg>
      </span>
    </el-badge>
  </button>
</template>

<script setup>
import { computed } from 'vue'
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

.notification-bell__glyph {
  display: grid;
  place-items: center;
  width: 18px;
  height: 18px;

  svg {
    width: 18px;
    height: 18px;
    stroke: color-mix(in srgb, var(--text-primary) 88%, var(--brand-primary-strong) 12%);
    stroke-width: 1.45;
    stroke-linecap: round;
    stroke-linejoin: round;
  }
}

.notification-bell--has-unread :deep(.el-badge__content) {
  box-shadow: 0 0 0 3px hsl(var(--card) / 0.95);
  animation: notification-pulse 3.2s ease-out infinite;
}

@keyframes notification-pulse {
  0%, 100% {
    transform: scale(1);
  }

  18% {
    transform: scale(1.04);
  }

  32% {
    transform: scale(1);
  }
}
</style>
