<template>
  <div class="wh-home">
    <p class="wh-home__lead">选择一项库房作业。提交前会再次展示库房、货位和项目。</p>
    <div class="wh-home__grid">
      <router-link v-if="userStore.canPostWarehouseInbound" class="wh-action" to="/m/warehouse/scan">扫码</router-link>
      <router-link v-if="userStore.canPostWarehouseInbound" class="wh-action" to="/m/warehouse/inbound">入库</router-link>
      <router-link v-if="userStore.canPostWarehouseOutbound" class="wh-action" to="/m/warehouse/outbound">出库</router-link>
      <router-link v-if="userStore.canPostWarehouseTransfer" class="wh-action" to="/m/warehouse/transfer">调拨</router-link>
      <router-link v-if="userStore.canEnterWarehouseCount" class="wh-action" to="/m/warehouse/count">盘点</router-link>
      <router-link class="wh-action" to="/m/warehouse/inventory">查库存</router-link>
      <router-link class="wh-action" to="/m/warehouse/history">最近流水</router-link>
    </div>
  </div>
</template>

<script setup>
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
</script>

<style scoped lang="scss">
.wh-home {
  display: grid;
  gap: 16px;
}

.wh-home__lead {
  margin: 0;
  color: var(--text-secondary);
}

.wh-home__grid {
  display: grid;
  gap: 12px;
}

.wh-action {
  min-height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  background: hsl(var(--card));
  color: hsl(var(--foreground));
  text-decoration: none;
  font-weight: 700;
}

@media (min-width: 768px) {
  .wh-home__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
