<template>
  <div class="wh-list">
    <van-search v-model="keyword" placeholder="物资编码/名称" @search="load" />
    <van-cell-group inset>
      <van-cell
        v-for="item in items"
        :key="`${item.warehouse_id}-${item.location_id}-${item.project_id}-${item.material_id}`"
        :title="`${item.material_code} ${item.material_name}`"
        :label="`${item.warehouse_name} / ${item.location_name} / ${item.project_name}`"
        :value="`${item.quantity} ${item.material_unit || ''}`"
      />
    </van-cell-group>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Cell as VanCell, CellGroup as VanCellGroup, Search as VanSearch } from 'vant'
import { listStockBalances } from '@/api/warehouse'

const keyword = ref('')
const items = ref([])

async function load() {
  const res = await listStockBalances({ q: keyword.value || undefined, page_size: 50 })
  items.value = res.items || []
}

onMounted(load)
</script>

<style scoped>
.wh-list { display: grid; gap: 12px; }
</style>
