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
  border: 1px solid color-mix(in srgb, var(--workspace-panel-border) 84%, var(--brand-primary-soft) 16%);
  border-radius: 16px;
  background: color-mix(in srgb, var(--surface-panel) 90%, transparent);
  box-shadow: 0 12px 24px hsl(var(--primary) / 0.06);
  backdrop-filter: blur(14px);
}
</style>
