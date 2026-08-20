<template>
  <div class="warehouse-location">
    <van-cell-group inset>
      <van-cell title="货位" :value="location?.name || '加载中'" />
      <van-cell title="编码" :value="location?.code || '-'" />
      <van-cell title="库房" :value="location?.warehouse_name || String(location?.warehouse_id || '-')" />
    </van-cell-group>
    <van-button block type="primary" @click="goInbound">扫货位后继续入库</van-button>
    <van-button block plain type="primary" @click="goInventory">查看库存</van-button>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button as VanButton, Cell as VanCell, CellGroup as VanCellGroup } from 'vant'
import { getLocation } from '@/api/warehouse'

const route = useRoute()
const router = useRouter()
const location = ref(null)

async function load() {
  const id = Number(route.params.id)
  location.value = await getLocation(id)
}

function goInbound() {
  router.push({ path: '/m/warehouse/inbound', query: { location_id: route.params.id } })
}

function goInventory() {
  router.push({ path: '/m/warehouse/inventory', query: { location_id: route.params.id } })
}

onMounted(load)
</script>

<style scoped>
.warehouse-location { display: grid; gap: 12px; }
</style>
