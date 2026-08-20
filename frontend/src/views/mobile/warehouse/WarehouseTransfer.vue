<template>
  <div class="wh-form">
    <van-form @submit="submit">
      <van-cell-group inset>
        <van-field v-model="materialKeyword" label="物资" placeholder="搜索物资" @update:model-value="searchMaterials" />
        <van-cell v-for="item in materials" :key="item.id" :title="`${item.code} ${item.name}`" :label="item.unit || ''" clickable @click="selectMaterial(item)" />
        <van-field :model-value="selectedUnit" label="单位" readonly />
        <van-field v-model="form.quantity" label="数量" placeholder="支持 +-*/" />
        <van-field :model-value="sourceWarehouseLabel" label="调出库房" readonly is-link @click="picking = 'source_warehouse'" />
        <van-field :model-value="sourceLocationLabel" label="调出货位" readonly is-link @click="picking = 'source_location'" />
        <van-field :model-value="sourceProjectLabel" label="调出项目" readonly is-link @click="picking = 'source_project'" />
        <van-field :model-value="targetWarehouseLabel" label="调入库房" readonly is-link @click="picking = 'target_warehouse'" />
        <van-field :model-value="targetLocationLabel" label="调入货位" readonly is-link @click="picking = 'target_location'" />
        <van-field :model-value="targetProjectLabel" label="调入项目" readonly is-link @click="picking = 'target_project'" />
        <van-field v-model="form.occurred_on" label="日期" readonly />
        <van-field v-model="form.handler" label="经办人" />
        <van-field v-model="form.reference_no" label="调拨依据" placeholder="必填" />
        <van-field v-model="form.description" label="备注" type="textarea" rows="2" />
      </van-cell-group>
      <div class="wh-form__submit">
        <van-button round block type="primary" native-type="submit" :loading="submitting">提交并立即过账</van-button>
      </div>
    </van-form>
    <van-action-sheet v-model:show="sheetVisible" :actions="sheetActions" @select="onSelect" />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showFailToast, showSuccessToast } from 'vant'
import { ActionSheet as VanActionSheet, Button as VanButton, Cell as VanCell, CellGroup as VanCellGroup, Field as VanField, Form as VanForm } from 'vant'
import { listLocations, postTransfer } from '@/api/warehouse'
import { evaluateQuantityExpression } from '@/utils/quantityExpression'
import { useWarehouseForm } from '@/composables/useWarehouseForm'

const router = useRouter()
const { form, warehouses, projects, materials, submitting, searchMaterials } = useWarehouseForm()
const materialKeyword = ref('')
const picking = ref('')
const sourceLocations = ref([])
const targetLocations = ref([])

const sourceWarehouseLabel = computed(() => labelWarehouse(form.value.source_warehouse_id))
const targetWarehouseLabel = computed(() => labelWarehouse(form.value.target_warehouse_id))
const sourceLocationLabel = computed(() => sourceLocations.value.find(item => item.id === form.value.source_location_id)?.name || '')
const targetLocationLabel = computed(() => targetLocations.value.find(item => item.id === form.value.target_location_id)?.name || '')
const selectedUnit = computed(() => materials.value.find(item => item.id === form.value.material_id)?.unit || '')
const sourceProjectLabel = computed(() => projects.value.find(item => item.id === form.value.source_project_id)?.name || '')
const targetProjectLabel = computed(() => projects.value.find(item => item.id === form.value.target_project_id)?.name || '')
const sheetVisible = computed({
  get: () => Boolean(picking.value),
  set: (value) => { if (!value) picking.value = '' }
})
const sheetActions = computed(() => {
  if (picking.value?.includes('warehouse')) {
    return warehouses.value.map(item => ({ name: item.warehouse_name || item.name, value: item.warehouse_id || item.id }))
  }
  if (picking.value === 'source_location') return sourceLocations.value.map(item => ({ name: item.name, value: item.id }))
  if (picking.value === 'target_location') return targetLocations.value.map(item => ({ name: item.name, value: item.id }))
  if (picking.value?.includes('project')) return projects.value.map(item => ({ name: item.name, value: item.id }))
  return []
})

function labelWarehouse(id) {
  return warehouses.value.find(item => (item.warehouse_id || item.id) === id)?.warehouse_name
    || warehouses.value.find(item => (item.warehouse_id || item.id) === id)?.name
    || ''
}

function selectMaterial(item) {
  form.value.material_id = item.id
  materialKeyword.value = `${item.code} ${item.name}`
}

async function onSelect(action) {
  if (picking.value === 'source_warehouse') form.value.source_warehouse_id = action.value
  if (picking.value === 'target_warehouse') form.value.target_warehouse_id = action.value
  if (picking.value === 'source_location') form.value.source_location_id = action.value
  if (picking.value === 'target_location') form.value.target_location_id = action.value
  if (picking.value === 'source_project') form.value.source_project_id = action.value
  if (picking.value === 'target_project') form.value.target_project_id = action.value
  picking.value = ''
}

watch(() => form.value.source_warehouse_id, async (id) => {
  sourceLocations.value = id ? await listLocations(id) : []
  form.value.source_location_id = sourceLocations.value.find(item => item.is_default)?.id || sourceLocations.value[0]?.id || null
})
watch(() => form.value.target_warehouse_id, async (id) => {
  targetLocations.value = id ? await listLocations(id) : []
  form.value.target_location_id = targetLocations.value.find(item => item.is_default)?.id || targetLocations.value[0]?.id || null
})

async function submit() {
  if (submitting.value) return
  const quantity = evaluateQuantityExpression(form.value.quantity, 3) ?? Number(form.value.quantity)
  if (!Number.isFinite(quantity) || quantity <= 0) {
    showFailToast('请输入有效数量，支持 +-*/')
    return
  }
  try {
    await showConfirmDialog({
      title: '确认调拨',
      message: `物资 ${materialKeyword.value || form.value.material_id}\n数量 ${quantity} ${selectedUnit.value}\n从 ${sourceWarehouseLabel.value}/${sourceLocationLabel.value}/${sourceProjectLabel.value}\n到 ${targetWarehouseLabel.value}/${targetLocationLabel.value}/${targetProjectLabel.value}`
    })
  } catch {
    return
  }
  submitting.value = true
  try {
    await postTransfer({
      occurred_on: form.value.occurred_on,
      handler: form.value.handler,
      reference_no: form.value.reference_no,
      description: form.value.description,
      lines: [{
        material_id: form.value.material_id,
        quantity: String(quantity),
        source_warehouse_id: form.value.source_warehouse_id,
        source_location_id: form.value.source_location_id,
        source_project_id: form.value.source_project_id,
        target_warehouse_id: form.value.target_warehouse_id,
        target_location_id: form.value.target_location_id,
        target_project_id: form.value.target_project_id
      }]
    })
    showSuccessToast('调拨已过账')
    router.push('/m/warehouse')
  } catch (error) {
    const data = error.response?.data
    if (data?.error_code === '7003') showFailToast(`库存不足，当前可用 ${data.data?.available ?? ''}，请刷新、改库位或联系管理员`)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.wh-form { display: grid; gap: 16px; }
.wh-form__submit { position: sticky; bottom: 12px; padding: 12px; }
.wh-form__submit :deep(.van-button) { min-height: 44px; }
</style>
