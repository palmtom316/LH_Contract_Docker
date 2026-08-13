<template>
  <div class="wh-list">
    <van-cell-group inset>
      <van-cell
        v-for="item in items"
        :key="item.id"
        :title="item.document_no"
        :label="`${item.occurred_on} ${item.material_code} ${item.material_name}`"
        :value="String(item.quantity_delta)"
      />
    </van-cell-group>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Cell as VanCell, CellGroup as VanCellGroup } from 'vant'
import { listLedger } from '@/api/warehouse'

const items = ref([])

onMounted(async () => {
  const res = await listLedger({ page_size: 30 })
  items.value = res.items || []
})
</script>
