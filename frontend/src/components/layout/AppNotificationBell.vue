<template>
  <button
    type="button"
    class="notification-bell app-chrome-icon-button"
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
