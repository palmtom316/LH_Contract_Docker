<template>
  <button
    type="button"
    class="notification-bell inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-card text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
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
</style>
