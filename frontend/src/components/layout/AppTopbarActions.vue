<template>
  <div class="topbar-actions">
    <button
      v-if="showContractQuery"
      type="button"
      class="contract-query-trigger"
      :class="{ 'is-open': isContractQueryOpen }"
      aria-label="打开合同查询助手"
      @click="$emit('open-contract-query')"
    >
      <span class="contract-query-trigger__icon" aria-hidden="true">
        <el-icon><Search /></el-icon>
      </span>
      <span class="contract-query-trigger__label">合同查询</span>
      <span class="contract-query-trigger__hint">Ctrl + K</span>
    </button>
    <AppThemeToggle />
    <AppNotificationBell :unread-count="unreadCount" />
  </div>
</template>

<script setup>
import { Search } from '@element-plus/icons-vue'
import AppNotificationBell from './AppNotificationBell.vue'
import AppThemeToggle from '@/components/ui/AppThemeToggle.vue'

defineProps({
  unreadCount: {
    type: Number,
    default: 0
  },
  showContractQuery: {
    type: Boolean,
    default: false
  },
  isContractQueryOpen: {
    type: Boolean,
    default: false
  }
})

defineEmits(['open-contract-query'])
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

.contract-query-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 12px 0 10px;
  border: 1px solid var(--workspace-panel-border);
  border-radius: var(--radius);
  background: var(--surface-panel);
  box-shadow: var(--shadow-soft);
  color: hsl(var(--foreground));
  cursor: pointer;
  transition: background-color 180ms ease, border-color 180ms ease, box-shadow 180ms ease, color 180ms ease, transform 180ms ease;
}

.contract-query-trigger__icon {
  width: 20px;
  height: 20px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--brand-primary-soft);
  color: var(--brand-primary-strong);
  flex-shrink: 0;
}

.contract-query-trigger__label {
  font-size: 13px;
  font-weight: 600;
  line-height: 1;
  letter-spacing: 0;
}

.contract-query-trigger__hint {
  margin-left: 2px;
  padding-left: 8px;
  border-left: 1px solid hsl(var(--border));
  font-size: 11px;
  font-weight: 600;
  color: hsl(var(--muted-foreground));
  line-height: 1;
  letter-spacing: 0;
}

.contract-query-trigger:hover,
.contract-query-trigger.is-open {
  background: var(--surface-sidebar-hover);
  border-color: hsl(var(--primary) / 0.5);
  color: hsl(var(--foreground));
  transform: translateY(-1px);
}

.contract-query-trigger:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

@media (max-width: 1100px) {
  .contract-query-trigger__hint {
    display: none;
  }
}

@media (max-width: 767px) {
  .contract-query-trigger {
    display: none;
  }
}
</style>
