<template>
  <div class="wh-form">
    <van-form @submit="submit">
      <van-cell-group inset>
        <van-field :model-value="warehouseLabel" label="调出库房" readonly is-link @click="showWarehouse = true" />
        <van-field :model-value="locationLabel" label="货位" readonly is-link @click="showLocation = true" />
        <van-field :model-value="projectLabel" label="项目" readonly is-link @click="showProject = true" />
        <van-field v-model="materialKeyword" label="物资" placeholder="搜索物资" @update:model-value="searchMaterials" />
        <van-cell v-for="item in materials" :key="item.id" :title="`${item.code} ${item.name}`" :label="item.unit || ''" clickable @click="selectMaterial(item)" />
        <van-field :model-value="selectedUnit" label="单位" readonly />
        <van-field v-model="form.quantity" label="数量" placeholder="支持 +-*/，如 3+1.5" />
        <van-field v-model="form.occurred_on" label="日期" readonly />
        <van-field v-model="form.handler" label="经办人" />
        <van-field :model-value="businessLabel" label="业务类型" readonly is-link @click="showBusiness = true" />
        <van-field
          v-if="form.business_type === 'SCRAP_DISPOSAL'"
          label="废旧处理依据"
          readonly
          required
          :model-value="form.scrap_basis_file_name || '必须上传'"
        >
          <template #button>
            <van-button size="small" type="primary" native-type="button" @click="pickFile">拍照/上传</van-button>
          </template>
        </van-field>
        <input ref="fileInput" class="hidden-file" type="file" accept=".pdf,.jpg,.jpeg,.png,image/*" capture="environment" @change="onFileChange">
        <van-field v-model="form.requisition_no" label="领料申请" />
        <van-field v-model="form.work_package" label="分部分项" />
        <van-field v-model="form.crew_name" label="班组" />
        <van-field v-model="form.requester_name" label="领料人" />
        <van-field v-model="form.receiver_name" label="接收人" />
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
import { showConfirmDialog, showFailToast, showSuccessToast } from 'vant'
import { ActionSheet as VanActionSheet, Button as VanButton, Cell as VanCell, CellGroup as VanCellGroup, Field as VanField, Form as VanForm } from 'vant'
import { postOutbound } from '@/api/warehouse'
import { uploadFile } from '@/api/common'
import { OUTBOUND_BUSINESS_OPTIONS } from '@/constants/warehouse'
import { evaluateQuantityExpression } from '@/utils/quantityExpression'
import { useWarehouseForm } from '@/composables/useWarehouseForm'

const router = useRouter()
const { form, warehouses, locations, projects, materials, available, submitting, searchMaterials } = useWarehouseForm()
form.value.business_type = 'ISSUE'
const materialKeyword = ref('')
const fileInput = ref(null)
const showWarehouse = ref(false)
const showLocation = ref(false)
const showProject = ref(false)
const showBusiness = ref(false)
const businessOptions = OUTBOUND_BUSINESS_OPTIONS.map(item => ({ name: item.label, value: item.value }))
const warehouseLabel = computed(() => warehouses.value.find(item => (item.warehouse_id || item.id) === form.value.warehouse_id)?.warehouse_name || warehouses.value.find(item => (item.warehouse_id || item.id) === form.value.warehouse_id)?.name || '')
const locationLabel = computed(() => locations.value.find(item => item.id === form.value.location_id)?.name || '')
const projectLabel = computed(() => projects.value.find(item => item.id === form.value.project_id)?.name || '')
const businessLabel = computed(() => businessOptions.find(item => item.value === form.value.business_type)?.name || '')
const selectedUnit = computed(() => materials.value.find(item => item.id === form.value.material_id)?.unit || '')
const warehouseActions = computed(() => warehouses.value.map(item => ({ name: item.warehouse_name || item.name, value: item.warehouse_id || item.id })))
const locationActions = computed(() => locations.value.map(item => ({ name: item.name, value: item.id })))
const projectActions = computed(() => projects.value.map(item => ({ name: item.name, value: item.id })))
const businessActions = computed(() => businessOptions)

function selectMaterial(item) {
  form.value.material_id = item.id
  materialKeyword.value = `${item.code} ${item.name}`
}

function pickFile() {
  fileInput.value?.click()
}

async function onFileChange(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  try {
    const result = await uploadFile(file, 'warehouse')
    const path = result?.key || result?.path
    if (!path) throw new Error('上传返回路径为空')
    form.value.scrap_basis_file = path
    form.value.scrap_basis_file_name = file.name
    showSuccessToast('废旧处理依据已上传')
  } catch (error) {
    showFailToast(error?.message || '上传失败')
  }
}

async function submit() {
  if (submitting.value) return
  const quantity = evaluateQuantityExpression(form.value.quantity, 3) ?? Number(form.value.quantity)
  if (!Number.isFinite(quantity) || quantity <= 0) {
    showFailToast('请输入有效数量，支持 +-*/')
    return
  }
  if (form.value.business_type === 'SCRAP_DISPOSAL' && !form.value.scrap_basis_file) {
    showFailToast('选择废旧处理必须上传废旧处理依据文件')
    return
  }
  try {
    await showConfirmDialog({
      title: '确认出库',
      message: `库房 ${warehouseLabel.value}\n货位 ${locationLabel.value}\n项目 ${projectLabel.value}\n物资 ${materialKeyword.value || form.value.material_id}\n数量 ${quantity} ${selectedUnit.value}`
    })
  } catch {
    return
  }
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
      scrap_basis_file: form.value.scrap_basis_file || null,
      scrap_basis_file_name: form.value.scrap_basis_file_name || null,
      requisition_no: form.value.requisition_no || null,
      work_package: form.value.work_package || null,
      crew_name: form.value.crew_name || null,
      requester_name: form.value.requester_name || null,
      receiver_name: form.value.receiver_name || null,
      signed_off: true,
      lines: [{ material_id: form.value.material_id, quantity: String(quantity) }]
    })
    showSuccessToast('出库已过账')
    router.push('/m/warehouse')
  } catch (error) {
    const data = error.response?.data
    if (data?.error_code === '7003') {
      showFailToast(`库存不足，当前可用 ${data.data?.available ?? ''}，请刷新、改库位或联系管理员`)
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.wh-form { display: grid; gap: 16px; }
.hidden-file { display: none; }
.wh-form__submit { position: sticky; bottom: 12px; padding: 12px; }
.wh-form__submit :deep(.van-button) { min-height: 44px; }
</style>
