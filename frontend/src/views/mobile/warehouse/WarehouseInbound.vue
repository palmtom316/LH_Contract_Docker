<template>
  <div class="wh-form">
    <van-form @submit="submit">
      <van-cell-group inset>
        <van-field :model-value="warehouseLabel" label="库房" readonly is-link placeholder="选择库房" @click="showWarehouse = true" />
        <van-field :model-value="locationLabel" label="货位" readonly is-link placeholder="选择货位" @click="showLocation = true" />
        <van-field :model-value="projectLabel" label="项目" readonly is-link placeholder="选择项目" @click="showProject = true" />
        <van-field v-model="materialKeyword" label="物资" placeholder="搜索编码或名称" @update:model-value="searchMaterials" />
        <van-cell v-for="item in materials" :key="item.id" :title="`${item.code} ${item.name}`" :label="`${item.specification || ''} / ${item.unit || ''}`" clickable @click="selectMaterial(item)" />
        <van-field :model-value="selectedUnit" label="单位" readonly />
        <van-field v-model="form.quantity" label="数量" placeholder="支持 +-*/，如 2*1.5" />
        <van-field v-model="form.occurred_on" label="日期" readonly />
        <van-field v-model="form.handler" label="经办人" />
        <van-field :model-value="businessLabel" label="业务类型" readonly is-link @click="showBusiness = true" />
        <van-field v-model="form.reference_no" label="依据单号" />
        <van-field label="送货单" readonly :model-value="form.delivery_note_file_name || '未上传'">
          <template #button>
            <van-button size="small" type="primary" native-type="button" @click="pickFile">拍照/上传</van-button>
          </template>
        </van-field>
        <input ref="fileInput" class="hidden-file" type="file" accept=".pdf,.jpg,.jpeg,.png,image/*" capture="environment" @change="onFileChange">
        <van-field v-model="form.description" label="备注" type="textarea" rows="2" />
        <van-cell title="可用库存" :value="available == null ? '选择维度后查询' : String(available)" />
      </van-cell-group>
      <div class="wh-form__submit">
        <van-button round block type="primary" native-type="submit" :loading="submitting" :disabled="submitting">提交并过账</van-button>
      </div>
    </van-form>
    <van-action-sheet v-model:show="showWarehouse" :actions="warehouseActions" @select="onSelectWarehouse" />
    <van-action-sheet v-model:show="showLocation" :actions="locationActions" @select="onSelectLocation" />
    <van-action-sheet v-model:show="showProject" :actions="projectActions" @select="onSelectProject" />
    <van-action-sheet v-model:show="showBusiness" :actions="businessActions" @select="onSelectBusiness" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showFailToast, showSuccessToast } from 'vant'
import { ActionSheet as VanActionSheet, Button as VanButton, Cell as VanCell, CellGroup as VanCellGroup, Field as VanField, Form as VanForm } from 'vant'
import { postInbound } from '@/api/warehouse'
import { uploadFile } from '@/api/common'
import { INBOUND_BUSINESS_OPTIONS } from '@/constants/warehouse'
import { evaluateQuantityExpression } from '@/utils/quantityExpression'
import { useWarehouseForm } from '@/composables/useWarehouseForm'

const route = useRoute()
const router = useRouter()
const { form, warehouses, locations, projects, materials, available, submitting, searchMaterials } = useWarehouseForm()
const materialKeyword = ref('')
const fileInput = ref(null)
const showWarehouse = ref(false)
const showLocation = ref(false)
const showProject = ref(false)
const showBusiness = ref(false)

const businessOptions = INBOUND_BUSINESS_OPTIONS.map(item => ({ name: item.label, value: item.value }))
const warehouseLabel = computed(() => warehouses.value.find(item => (item.warehouse_id || item.id) === form.value.warehouse_id)?.warehouse_name || warehouses.value.find(item => (item.warehouse_id || item.id) === form.value.warehouse_id)?.name || '')
const locationLabel = computed(() => locations.value.find(item => item.id === form.value.location_id)?.name || '')
const projectLabel = computed(() => projects.value.find(item => item.id === form.value.project_id)?.name || '')
const businessLabel = computed(() => businessOptions.find(item => item.value === form.value.business_type)?.name || '')
const selectedUnit = computed(() => materials.value.find(item => item.id === form.value.material_id)?.unit || '')
const warehouseActions = computed(() => warehouses.value.map(item => ({ name: item.warehouse_name || item.name, value: item.warehouse_id || item.id })))
const locationActions = computed(() => locations.value.map(item => ({ name: item.name, value: item.id })))
const projectActions = computed(() => projects.value.map(item => ({ name: item.name, value: item.id })))
const businessActions = computed(() => businessOptions)

function onSelectWarehouse(action) {
  form.value.warehouse_id = action.value
  showWarehouse.value = false
}
function onSelectLocation(action) {
  form.value.location_id = action.value
  showLocation.value = false
}
function onSelectProject(action) {
  form.value.project_id = action.value
  showProject.value = false
}
function onSelectBusiness(action) {
  form.value.business_type = action.value
  showBusiness.value = false
}
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
    form.value.delivery_note_file = path
    form.value.delivery_note_file_name = file.name
    showSuccessToast('送货单已上传')
  } catch (error) {
    showFailToast(error?.message || '上传失败')
  }
}

if (route.params.id) {
  form.value.material_id = Number(route.params.id)
}

async function submit() {
  if (submitting.value) return
  const quantity = evaluateQuantityExpression(form.value.quantity, 3) ?? Number(form.value.quantity)
  if (!Number.isFinite(quantity) || quantity <= 0) {
    showFailToast('请输入有效数量，支持 +-*/')
    return
  }
  submitting.value = true
  try {
    await postInbound({
      warehouse_id: form.value.warehouse_id,
      location_id: form.value.location_id,
      project_id: form.value.project_id,
      occurred_on: form.value.occurred_on,
      handler: form.value.handler,
      business_type: form.value.business_type,
      reference_no: form.value.reference_no,
      description: form.value.description,
      delivery_note_file: form.value.delivery_note_file || null,
      delivery_note_file_name: form.value.delivery_note_file_name || null,
      lines: [{ material_id: form.value.material_id, quantity: String(quantity) }]
    })
    showSuccessToast('入库已过账')
    router.push('/m/warehouse')
  } catch (error) {
    const data = error.response?.data
    if (data?.error_code === '7003') {
      showFailToast(`库存不足，当前可用 ${data.data?.available ?? ''}`)
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.wh-form { display: grid; gap: 16px; }
.hidden-file { display: none; }
.wh-form__submit {
  position: sticky;
  bottom: 12px;
  padding: 12px;
}
.wh-form__submit :deep(.van-button) { min-height: 44px; }
</style>
