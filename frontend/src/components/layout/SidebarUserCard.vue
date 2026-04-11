<template>
  <section class="sidebar-user-card">
    <el-dropdown trigger="click" placement="top-start" class="user-menu" @visible-change="handleVisibleChange">
      <button
        type="button"
        class="user-menu__trigger"
        :class="{
          'user-menu__trigger--compact': compact,
          'is-open': dropdownVisible
        }"
      >
        <span class="user-menu__icon">
          <el-avatar :icon="UserFilled" :size="compact ? 30 : 28" />
        </span>
        <span v-if="!compact" class="user-copy">
          <strong class="user-name">{{ displayName }}</strong>
          <small class="user-meta">{{ displayMeta }}</small>
        </span>
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
import { computed, ref } from 'vue'
import { UserFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

defineEmits(['change-password', 'logout'])
defineProps({
  compact: {
    type: Boolean,
    default: false
  }
})

const userStore = useUserStore()
const dropdownVisible = ref(false)
const displayName = computed(() => userStore.user.full_name || userStore.user.username || '未命名用户')
const displayMeta = computed(() => userStore.user.email || userStore.user.username || '系统账户')

function handleVisibleChange(visible) {
  dropdownVisible.value = visible
}
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
  min-height: 40px;
  padding: 4px 10px;
  border: 0;
  border-radius: 14px;
  background: transparent;
  color: hsl(var(--muted-foreground));
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  text-align: left;
  cursor: pointer;
  transition: background-color 160ms ease, color 160ms ease, transform 160ms ease;
}

.user-menu__trigger:hover,
.user-menu__trigger.is-open {
  background: var(--surface-sidebar-hover);
  color: hsl(var(--foreground));
  transform: translateY(-1px);
}

.user-menu__trigger.is-open {
  box-shadow: inset 0 0 0 1px hsl(var(--border));
}

.user-menu__icon {
  width: 32px;
  height: 32px;
  border-radius: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: transparent;
  transition: background-color 160ms ease, color 160ms ease;
}

.user-menu__trigger:hover .user-menu__icon,
.user-menu__trigger.is-open .user-menu__icon {
  background: var(--surface-panel);
  box-shadow: 0 10px 18px hsl(var(--primary) / 0.08);
}

.user-menu__icon :deep(.el-avatar) {
  width: 28px;
  height: 28px;
  background: color-mix(in srgb, hsl(var(--muted)) 78%, hsl(var(--card)) 22%);
  color: hsl(var(--muted-foreground));
}

.user-copy {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.user-menu__trigger--compact {
  width: 44px;
  min-height: 44px;
  padding: 0;
  justify-content: center;
  border-radius: 14px;
}

.user-menu__trigger--compact .user-menu__icon {
  width: 36px;
  height: 36px;
}

.user-menu__trigger--compact .user-menu__icon :deep(.el-avatar) {
  width: 30px;
  height: 30px;
}

.user-name {
  display: block;
  color: hsl(var(--foreground));
  font-size: 13px;
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-meta {
  display: block;
  color: hsl(var(--muted-foreground));
  font-size: 11px;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.danger-item) {
  color: var(--status-danger);
}
</style>
