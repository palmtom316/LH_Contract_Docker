<template>
  <section class="sidebar-user-card">
    <el-dropdown trigger="click" placement="top-start" class="user-menu">
      <button type="button" class="user-menu__trigger">
        <el-avatar :icon="UserFilled" :size="34" />
        <strong class="user-name">{{ displayName }}</strong>
      </button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item @click="$emit('change-password')">修改密码</el-dropdown-item>
          <el-dropdown-item class="danger-item" @click="$emit('logout')">退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
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
  padding: 0;
}

.user-menu {
  display: block;
}

.user-menu__trigger {
  width: 100%;
  border: 0;
  background: transparent;
  padding: 0 2px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  cursor: pointer;
  min-height: 36px;
}

.user-name {
  display: block;
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.danger-item) {
  color: var(--status-danger);
}
</style>
