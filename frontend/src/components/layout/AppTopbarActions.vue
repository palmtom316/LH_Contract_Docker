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
  gap: 6px;
  padding: 4px;
  border: 1px solid color-mix(in srgb, var(--workspace-panel-border) 88%, var(--brand-primary-soft) 12%);
  border-radius: 999px;
  background: color-mix(in srgb, var(--surface-panel) 96%, var(--muted) 4%);
  box-shadow: none;
}
</style>
