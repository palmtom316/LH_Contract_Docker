<template>
  <div class="notification-center-page app-container">
    <section class="notification-center-shell">
      <header class="notification-center-header">
        <span class="notification-center-header__eyebrow">消息中心</span>
        <h2>系统通知</h2>
      </header>

      <section class="notification-center-toolbar">
        <el-segmented v-model="activeFilter" :options="filterOptions" />
      </section>

      <el-skeleton v-if="loading" :rows="4" animated />
      <el-empty
        v-else-if="loadError"
        description="通知加载失败，请稍后重试。"
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
      <el-empty v-else description="当前没有新的系统提醒。" />
    </section>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onMounted, ref } from 'vue'
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
.notification-center-page {
  padding: 0;
}

.notification-center-shell {
  display: grid;
  gap: 18px;
  padding: 20px;
  border: 1px solid var(--border-subtle);
  border-radius: 20px;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--brand-primary) 10%, transparent) 0, transparent 36%),
    linear-gradient(180deg, var(--surface-panel), color-mix(in srgb, var(--surface-panel) 88%, var(--surface-panel-muted) 12%));
  box-shadow: var(--shadow-soft);
}

.notification-center-header {
  display: grid;
  gap: 10px;
  padding: 4px 2px 0;
}

.notification-center-header__eyebrow {
  display: inline-flex;
  min-height: 24px;
  align-items: center;
  padding: 0 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--brand-primary) 12%, var(--surface-panel) 88%);
  color: var(--brand-primary-strong);
  font-size: 12px;
  font-weight: 700;
}

.notification-center-header h2 {
  margin: 0;
  font-size: clamp(22px, 3vw, 30px);
  line-height: 1.2;
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
  border-radius: 16px;
  padding: 16px 18px;
  background: color-mix(in srgb, var(--surface-panel) 94%, var(--brand-primary) 6%);
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
    padding: 16px;
    border-radius: 16px;
  }

  .notification-center-header h2 {
    font-size: 24px;
  }

  .notification-item__top {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }
}
</style>
