<template>
  <nav class="warehouse-nav" aria-label="库房管理">
    <router-link
      v-for="item in items"
      :key="item.to"
      :to="item.to"
      class="warehouse-nav__link"
      :class="{ 'is-active': isActive(item.to) }"
    >
      {{ item.label }}
    </router-link>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()

const items = computed(() => {
  const list = [
    { to: '/warehouse/overview', label: '库存总览' },
    { to: '/warehouse/inventory', label: '库存查询' },
    { to: '/warehouse/materials', label: '物资档案' },
    { to: '/warehouse/warehouses', label: '库房与货位' },
    { to: '/warehouse/projects', label: '项目档案' },
    { to: '/warehouse/opening', label: '期初材料录入' },
    { to: '/warehouse/inbounds', label: '入库单' },
    { to: '/warehouse/outbounds', label: '出库单' },
    { to: '/warehouse/transfers', label: '调拨单' },
    { to: '/warehouse/counts', label: '盘点' },
    { to: '/warehouse/ledger', label: '流水与报表' }
  ]
  return userStore.canViewWarehouseInventory ? list : []
})

function isActive(path) {
  return route.path === path
}
</script>

<style scoped lang="scss">
.warehouse-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.warehouse-nav__link {
  min-height: 36px;
  padding: 6px 12px;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  color: var(--text-secondary);
  text-decoration: none;
  background: hsl(var(--card));
}

.warehouse-nav__link.is-active {
  color: hsl(var(--foreground));
  border-color: var(--brand-primary, hsl(var(--primary)));
  background: color-mix(in srgb, var(--brand-primary-soft, hsl(var(--muted))) 70%, hsl(var(--card)) 30%);
}
</style>
