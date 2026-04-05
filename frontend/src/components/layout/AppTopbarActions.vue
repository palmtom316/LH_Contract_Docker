<template>
  <div class="topbar-actions">
    <AppThemeToggle />
    <AppNotificationBell :unread-count="unreadCount" />
  </div>
</template>

<script setup>
import AppNotificationBell from './AppNotificationBell.vue'
import AppThemeToggle from '@/components/ui/AppThemeToggle.vue'

defineProps({
  unreadCount: {
    type: Number,
    default: 0
  }
})
</script>

<style scoped lang="scss">
.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
