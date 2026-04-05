<template>
  <div class="notification-center-page app-container">
    <el-card shadow="never" class="notification-center-card">
      <template #header>
        <div class="notification-center-header">
          <div>
            <h2>系统通知</h2>
            <p>查看系统提醒、合同到期提醒与关键审计事件</p>
          </div>
          <el-segmented v-model="activeFilter" :options="filterOptions" />
        </div>
      </template>

      <el-skeleton v-if="loading" :rows="4" animated />
      <div v-else-if="filteredNotifications.length" class="notification-list">
        <article v-for="item in filteredNotifications" :key="item.id" class="notification-item">
          <div class="notification-item__title">{{ item.title }}</div>
          <div class="notification-item__meta">{{ item.subtitle }} · {{ formatTime(item.createdAt) }}</div>
        </article>
      </div>
      <el-empty v-else description="当前没有新的系统提醒。" />
    </el-card>
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

function formatTime(value) {
  if (!value) return '时间未知'
  return dayjs(value).format('YYYY-MM-DD HH:mm')
}

onMounted(async () => {
  loading.value = true
  try {
    await systemStore.fetchNotifications()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.notification-center-page {
  padding: 20px;
}

.notification-center-card {
  border-radius: 12px;
}

.notification-center-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.notification-center-header h2 {
  margin: 0;
  font-size: 22px;
  line-height: 1.3;
}

.notification-center-header p {
  margin: 4px 0 0;
  color: #64748b;
}

.notification-list {
  display: grid;
  gap: 12px;
}

.notification-item {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px 16px;
  background: #fff;
}

.notification-item__title {
  font-weight: 600;
  color: #0f172a;
}

.notification-item__meta {
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
}

@media (max-width: 768px) {
  .notification-center-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
