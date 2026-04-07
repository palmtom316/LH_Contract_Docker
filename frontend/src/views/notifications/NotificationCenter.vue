<template>
  <div class="notification-center-shell">
    <AppPageHeader
      class="notification-center-header"
      title="系统通知"
    />

    <AppWorkspacePanel panel-class="notification-center-panel">
      <section class="notification-center-toolbar">
        <el-segmented v-model="activeFilter" :options="filterOptions" />
      </section>

      <el-skeleton v-if="loading" :rows="4" animated />
      <el-empty
        v-else-if="loadError"
        description="通知加载失败"
      >
        <el-button type="primary" @click="loadNotifications">重试</el-button>
      </el-empty>
      <div v-else-if="filteredNotifications.length" class="notification-list">
        <article v-for="item in filteredNotifications" :key="item.id" class="notification-item">
          <div class="notification-item__top">
            <div class="notification-item__title">{{ item.title }}</div>
            <span class="notification-item__time">{{ formatTime(item.createdAt) }}</span>
          </div>
          <div class="notification-item__meta">{{ item.subtitle }}</div>
        </article>
      </div>
      <el-empty v-else description="暂无通知" />
    </AppWorkspacePanel>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onMounted, ref } from 'vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'
import { useSystemStore } from '@/stores/system'

const systemStore = useSystemStore()
const loading = ref(false)
const activeFilter = ref('all')

const filterOptions = [
  { label: '全部', value: 'all' },
  { label: '合同到期', value: 'contract_expiry' },
  { label: '审计事件', value: 'audit' },
  { label: '其他', value: 'general' }
]

const filteredNotifications = computed(() => {
  const items = systemStore.notifications || []
  if (activeFilter.value === 'all') return items
  return items.filter(item => item.type === activeFilter.value)
})
const loadError = computed(() => systemStore.notificationsError)

function formatTime(value) {
  if (!value) return '时间未知'
  return dayjs(value).format('YYYY-MM-DD HH:mm')
}

async function loadNotifications() {
  loading.value = true
  try {
    await systemStore.fetchNotifications()
  } catch (error) {
    // store keeps error state for UI rendering
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadNotifications()
})
</script>

<style scoped>
.notification-center-shell {
  display: grid;
  gap: var(--space-5);
}

.notification-center-panel {
  gap: 18px;
}

.notification-center-header {
  margin-bottom: 0;
}

.notification-center-toolbar {
  display: flex;
  justify-content: flex-start;
}

.notification-list {
  display: grid;
  gap: 14px;
}

.notification-item {
  display: grid;
  gap: 8px;
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 14px 16px;
  background: var(--surface-panel);
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.notification-item:hover {
  background: color-mix(in srgb, var(--surface-panel-muted) 72%, var(--surface-panel) 28%);
}

.notification-item__top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 14px;
}

.notification-item__title {
  font-weight: 600;
  color: var(--text-primary);
}

.notification-item__meta {
  color: var(--text-secondary);
  font-size: 13px;
}

.notification-item__time {
  flex-shrink: 0;
  color: var(--text-muted);
  font-size: 12px;
}

@media (max-width: 768px) {
  .notification-center-shell {
    gap: var(--space-4);
  }

  .notification-item__top {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }
}
</style>
