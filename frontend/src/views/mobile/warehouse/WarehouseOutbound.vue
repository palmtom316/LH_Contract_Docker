<template>
  <div class="wh-form">
    <van-form @submit="submit">
      <van-cell-group inset>
        <van-field :model-value="warehouseLabel" label="调出库房" readonly is-link @click="showWarehouse = true" />
        <van-field :model-value="locationLabel" label="货位" readonly is-link @click="showLocation = true" />
        <van-field :model-value="projectLabel" label="项目" readonly is-link @click="showProject = true" />
        <van-field v-model="materialKeyword" label="物资" placeholder="搜索物资" @update:model-value="searchMaterials" />
        <van-cell v-for="item in materials" :key="item.id" :title="`${item.code} ${item.name}`" clickable @click="selectMaterial(item)" />
        <van-field v-model="form.quantity" type="number" label="数量" />
        <van-field v-model="form.occurred_on" label="日期" readonly />
        <van-field v-model="form.handler" label="经办人" />
        <van-field :model-value="businessLabel" label="业务类型" readonly is-link @click="showBusiness = true" />
        <van-cell title="可用库存" :value="available == null ? '-' : String(available)" />
      </van-cell-group>
      <div class="wh-form__submit">
        <van-button round block type="primary" native-type="submit" :loading="submitting">提交并过账</van-button>
      </div>
    </van-form>
    <van-action-sheet v-model:show="showWarehouse" :actions="warehouseActions" @select="action => { form.warehouse_id = action.value; showWarehouse = false }" />
    <van-action-sheet v-model:show="showLocation" :actions="locationActions" @select="action => { form.location_id = action.value; showLocation = false }" />
    <van-action-sheet v-model:show="showProject" :actions="projectActions" @select="action => { form.project_id = action.value; showProject = false }" />
    <van-action-sheet v-model:show="showBusiness" :actions="businessActions" @select="action => { form.business_type = action.value; showBusiness = false }" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showFailToast, showSuccessToast } from 'vant'
import { ActionSheet as VanActionSheet, Button as VanButton, Cell as VanCell, CellGroup as VanCellGroup, Field as VanField, Form as VanForm } from 'vant'
import { postOutbound } from '@/api/warehouse'
import { useWarehouseForm } from '@/composables/useWarehouseForm'

const router = useRouter()
const { form, warehouses, locations, projects, materials, available, submitting, searchMaterials } = useWarehouseForm()
form.value.business_type = 'ISSUE'
const materialKeyword = ref('')
const showWarehouse = ref(false)
const showLocation = ref(false)
const showProject = ref(false)
const showBusiness = ref(false)
const businessOptions = [
  { name: '领用出库', value: 'ISSUE' },
  { name: '退废旧', value: 'SCRAP_RETURN' },
  { name: '报废', value: 'WRITE_OFF' }
]
const warehouseLabel = computed(() => warehouses.value.find(item => (item.warehouse_id || item.id) === form.value.warehouse_id)?.warehouse_name || warehouses.value.find(item => (item.warehouse_id || item.id) === form.value.warehouse_id)?.name || '')
const locationLabel = computed(() => locations.value.find(item => item.id === form.value.location_id)?.name || '')
const projectLabel = computed(() => projects.value.find(item => item.id === form.value.project_id)?.name || '')
const businessLabel = computed(() => businessOptions.find(item => item.value === form.value.business_type)?.name || '')
const warehouseActions = computed(() => warehouses.value.map(item => ({ name: item.warehouse_name || item.name, value: item.warehouse_id || item.id })))
const locationActions = computed(() => locations.value.map(item => ({ name: item.name, value: item.id })))
const projectActions = computed(() => projects.value.map(item => ({ name: item.name, value: item.id })))
const businessActions = computed(() => businessOptions)

function selectMaterial(item) {
  form.value.material_id = item.id
  materialKeyword.value = `${item.code} ${item.name}`
}

async function submit() {
  if (submitting.value) return
  submitting.value = true
  try {
    await postOutbound({
      warehouse_id: form.value.warehouse_id,
      location_id: form.value.location_id,
      project_id: form.value.project_id,
      occurred_on: form.value.occurred_on,
      handler: form.value.handler,
      business_type: form.value.business_type,
      reference_no: form.value.reference_no,
      lines: [{ material_id: form.value.material_id, quantity: form.value.quantity }]
    })
    showSuccessToast('出库已过账')
    router.push('/m/warehouse')
  } catch (error) {
    const data = error.response?.data
    if (data?.error_code === '7003') {
      showFailToast(`库存不足，当前可用 ${data.data?.available ?? ''}，请刷新后重试`)
    }
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
