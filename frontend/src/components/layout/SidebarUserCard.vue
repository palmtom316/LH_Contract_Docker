<template>
  <section class="sidebar-user-card">
    <div class="user-head">
      <el-avatar :icon="UserFilled" :size="36" />
      <div class="user-meta">
        <strong class="user-name">{{ displayName }}</strong>
        <span class="user-role">{{ userStore.roleDisplay || '成员' }}</span>
      </div>
    </div>
    <div class="user-actions">
      <button type="button" class="action-btn" @click="$emit('change-password')">修改密码</button>
      <button type="button" class="action-btn danger" @click="$emit('logout')">退出登录</button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { UserFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

defineEmits(['change-password', 'logout'])

const userStore = useUserStore()
const displayName = computed(() => userStore.user.full_name || userStore.user.username || '未命名用户')
</script>

<style scoped lang="scss">
.sidebar-user-card {
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.25);
  border: 1px solid rgba(148, 163, 184, 0.18);
  padding: 12px;
}

.user-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-meta {
  min-width: 0;
}

.user-name {
  display: block;
  color: var(--text-inverse);
  font-size: 13px;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-role {
  display: block;
  font-size: 12px;
  color: rgba(248, 250, 252, 0.72);
}

.user-actions {
  margin-top: 10px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.action-btn {
  border: 0;
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.12);
  color: var(--text-inverse);
  font-size: 12px;
  line-height: 30px;
  cursor: pointer;
}

.action-btn.danger {
  background: rgba(239, 68, 68, 0.24);
}
</style>
