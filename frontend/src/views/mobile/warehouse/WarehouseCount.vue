<template>
  <div class="wh-form">
    <van-cell-group inset>
      <van-field :model-value="warehouseLabel" label="库房" readonly is-link @click="showWarehouse = true" />
      <van-field v-model="countedOn" label="盘点日期" readonly />
      <div class="wh-form__submit">
        <van-button block type="primary" :loading="creating" @click="create">创建账面快照</van-button>
      </div>
    </van-cell-group>
    <van-cell-group v-if="current" inset>
      <van-cell :title="current.count_no" :label="current.status" />
      <van-field
        v-for="line in current.lines"
        :key="line.id"
        v-model="line.counted_quantity"
        type="number"
        :label="line.material_code"
        :placeholder="`账面 ${line.book_quantity}`"
      />
      <div class="wh-form__submit">
        <van-button block type="success" @click="save">保存实盘</van-button>
      </div>
    </van-cell-group>
    <van-action-sheet v-model:show="showWarehouse" :actions="warehouseActions" @select="action => { warehouseId = action.value; showWarehouse = false }" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { showSuccessToast } from 'vant'
import { ActionSheet as VanActionSheet, Button as VanButton, Cell as VanCell, CellGroup as VanCellGroup, Field as VanField } from 'vant'
import { createCount, getMyWarehouseScopes, updateCountLines } from '@/api/warehouse'

const warehouses = ref([])
const warehouseId = ref(null)
const countedOn = ref(new Date().toISOString().slice(0, 10))
const current = ref(null)
const creating = ref(false)
const showWarehouse = ref(false)

getMyWarehouseScopes().then((rows) => {
  warehouses.value = rows
  const def = rows.find(item => item.is_default) || rows[0]
  warehouseId.value = def?.warehouse_id || def?.id || null
})

const warehouseLabel = computed(() => warehouses.value.find(item => (item.warehouse_id || item.id) === warehouseId.value)?.warehouse_name || warehouses.value.find(item => (item.warehouse_id || item.id) === warehouseId.value)?.name || '')
const warehouseActions = computed(() => warehouses.value.map(item => ({ name: item.warehouse_name || item.name, value: item.warehouse_id || item.id })))

async function create() {
  creating.value = true
  try {
    current.value = await createCount({ warehouse_id: warehouseId.value, counted_on: countedOn.value })
    showSuccessToast('已生成账面快照')
  } finally {
    creating.value = false
  }
}

async function save() {
  await updateCountLines(current.value.id, {
    lines: current.value.lines.map(line => ({
      id: line.id,
      counted_quantity: String(line.counted_quantity ?? line.book_quantity)
    }))
  })
  showSuccessToast('实盘已保存，等待库房管理员确认')
}
</script>

<style scoped>
.wh-form { display: grid; gap: 16px; }
.wh-form__submit { padding: 12px; }
.wh-form__submit :deep(.van-button) { min-height: 44px; }
</style>
