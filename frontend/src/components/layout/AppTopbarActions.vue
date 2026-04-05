<template>
  <div class="topbar-actions">
    <AppThemeToggle />
    <AppNotificationBell :unread-count="unreadCount" />
    <el-dropdown trigger="click" @command="$emit('command', $event)">
      <button type="button" class="user-menu-trigger" aria-label="打开用户菜单">
        <el-avatar :size="28" :icon="UserFilled" />
        <el-icon><CaretBottom /></el-icon>
      </button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="changePassword">修改密码</el-dropdown-item>
          <el-dropdown-item command="profile">个人信息</el-dropdown-item>
          <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
import { CaretBottom, UserFilled } from '@element-plus/icons-vue'
import AppNotificationBell from './AppNotificationBell.vue'
import AppThemeToggle from '@/components/ui/AppThemeToggle.vue'

defineProps({
  unreadCount: {
    type: Number,
    default: 0
  }
})

defineEmits(['command'])
</script>

<style scoped lang="scss">
.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-menu-trigger {
  height: 36px;
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
  background: var(--surface-panel);
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 8px;
  cursor: pointer;
}
</style>
