<template>
  <div class="warehouse-page">
    <WarehouseNav />
    <AppWorkspacePanel>
      <AppSectionCard>
        <template #header>{{ title }}</template>
        <template #actions>
          <el-button v-if="canCreate" type="primary" @click="openCreate">新建</el-button>
        </template>
        <AppDataTable>
          <el-table v-loading="loading" :data="items" border>
            <el-table-column prop="document_no" label="单号" min-width="160" />
            <el-table-column prop="occurred_on" label="日期" width="120" />
            <el-table-column label="业务类型" width="130">
              <template #default="{ row }">{{ businessLabel(row.business_type) }}</template>
            </el-table-column>
            <el-table-column label="物资 / 单位" min-width="180">
              <template #default="{ row }">{{ materialSummary(row) }}</template>
            </el-table-column>
            <el-table-column v-if="documentType === 'INBOUND'" label="送货单" min-width="140">
              <template #default="{ row }">
                <el-button v-if="row.delivery_note_file" link type="primary" @click="openFile(row.delivery_note_file)">
                  {{ row.delivery_note_file_name || '查看送货单' }}
                </el-button>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column v-if="documentType === 'OUTBOUND'" label="废旧处理依据" min-width="150">
              <template #default="{ row }">
                <el-button v-if="row.scrap_basis_file" link type="primary" @click="openFile(row.scrap_basis_file)">
                  {{ row.scrap_basis_file_name || '查看依据' }}
                </el-button>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="handler" label="经办人" width="120" />
            <el-table-column prop="status" label="状态" width="100" />
            <el-table-column prop="reference_no" label="依据" min-width="140" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button
                  v-if="userStore.canVoidWarehouseDocument && row.status === 'POSTED'"
                  link
                  type="danger"
                  @click="voidRow(row)"
                >
                  冲销
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </AppDataTable>
      </AppSectionCard>
    </AppWorkspacePanel>

    <el-dialog v-model="dialogVisible" :title="`新建${title}`" width="640px" append-to-body>
      <el-form :model="form" label-width="100px">
        <el-form-item v-if="documentType !== 'TRANSFER'" label="库房">
          <el-select v-model="form.warehouse_id"><el-option v-for="item in warehouses" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        </el-form-item>
        <el-form-item v-if="documentType !== 'TRANSFER'" label="货位">
          <el-select v-model="form.location_id"><el-option v-for="item in locations" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        </el-form-item>
        <el-form-item v-if="documentType !== 'TRANSFER'" label="项目">
          <el-select v-model="form.project_id"><el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        </el-form-item>
        <el-form-item label="物资">
          <el-select v-model="form.material_id" filterable remote :remote-method="searchMats" :loading="searching">
            <el-option v-for="item in materials" :key="item.id" :label="`${item.code} ${item.name} / ${item.unit}`" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="单位">{{ selectedMaterialUnit || '-' }}</el-form-item>
        <el-form-item label="数量">
          <FormulaInput v-model="form.quantity" :precision="3" placeholder="支持 +-*/，保留3位小数" />
        </el-form-item>
        <el-form-item label="批次号"><el-input v-model="form.batch_no" placeholder="选填，批次物资必填" /></el-form-item>
        <el-form-item label="序列号"><el-input v-model="form.serial_no" placeholder="选填，单件物资必填，每行数量为1" /></el-form-item>
        <el-form-item label="日期"><el-date-picker v-model="form.occurred_on" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="经办人"><el-input v-model="form.handler" /></el-form-item>
        <el-form-item v-if="documentType === 'INBOUND'" label="业务类型">
          <el-select v-model="form.business_type">
            <el-option v-for="item in inboundOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="documentType === 'INBOUND'" label="供应商"><el-input v-model="form.supplier_name" /></el-form-item>
        <el-form-item v-if="documentType === 'INBOUND'" label="采购订单"><el-input v-model="form.purchase_order_no" /></el-form-item>
        <el-form-item v-if="documentType === 'INBOUND'" label="送货单号"><el-input v-model="form.delivery_note_no" /></el-form-item>
        <el-form-item v-if="documentType === 'INBOUND'" label="验收单号"><el-input v-model="form.acceptance_no" /></el-form-item>
        <el-form-item v-if="documentType === 'INBOUND'" label="验收人"><el-input v-model="form.acceptor" /></el-form-item>
        <el-form-item v-if="documentType === 'INBOUND'" label="送货单">
          <WarehouseAttachmentField v-model="form.delivery_note_file" v-model:file-name="form.delivery_note_file_name" button-text="上传送货单或拍照" />
        </el-form-item>
        <el-form-item v-if="documentType === 'OUTBOUND'" label="业务类型">
          <el-select v-model="form.business_type">
            <el-option v-for="item in outboundOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="documentType === 'OUTBOUND'" label="领料申请"><el-input v-model="form.requisition_no" /></el-form-item>
        <el-form-item v-if="documentType === 'OUTBOUND'" label="班组"><el-input v-model="form.crew_name" /></el-form-item>
        <el-form-item v-if="documentType === 'OUTBOUND'" label="领料人"><el-input v-model="form.requester_name" /></el-form-item>
        <el-form-item v-if="documentType === 'OUTBOUND'" label="接收人"><el-input v-model="form.receiver_name" /></el-form-item>
        <el-form-item v-if="documentType === 'OUTBOUND' && form.business_type === 'SCRAP_DISPOSAL'" label="废旧处理依据" required>
          <WarehouseAttachmentField v-model="form.scrap_basis_file" v-model:file-name="form.scrap_basis_file_name" button-text="上传审批文件或拍照" />
        </el-form-item>
        <el-form-item v-if="documentType === 'TRANSFER'" label="调出库房">
          <el-select v-model="form.source_warehouse_id"><el-option v-for="item in warehouses" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        </el-form-item>
        <el-form-item v-if="documentType === 'TRANSFER'" label="调出货位">
          <el-select v-model="form.source_location_id"><el-option v-for="item in sourceLocations" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        </el-form-item>
        <el-form-item v-if="documentType === 'TRANSFER'" label="调出项目">
          <el-select v-model="form.source_project_id"><el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        </el-form-item>
        <el-form-item v-if="documentType === 'TRANSFER'" label="调入库房">
          <el-select v-model="form.target_warehouse_id"><el-option v-for="item in warehouses" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        </el-form-item>
        <el-form-item v-if="documentType === 'TRANSFER'" label="调入货位">
          <el-select v-model="form.target_location_id"><el-option v-for="item in targetLocations" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        </el-form-item>
        <el-form-item v-if="documentType === 'TRANSFER'" label="调入项目">
          <el-select v-model="form.target_project_id"><el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        </el-form-item>
        <el-form-item label="依据"><el-input v-model="form.reference_no" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">提交过账</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listDocuments, listLocations, listMaterials, listProjects, listWarehouses, postInbound, postOutbound, postTransfer, voidDocument } from '@/api/warehouse'
import { useUserStore } from '@/stores/user'
import { BUSINESS_TYPE_LABELS, INBOUND_BUSINESS_OPTIONS, OUTBOUND_BUSINESS_OPTIONS } from '@/constants/warehouse'
import { evaluateQuantityExpression } from '@/utils/quantityExpression'
import { todayISODate } from '@/utils/dateInput'
import { openProtectedFile } from '@/utils/protectedFiles'
import FormulaInput from '@/components/FormulaInput.vue'
import WarehouseAttachmentField from '@/components/WarehouseAttachmentField.vue'
import WarehouseNav from './WarehouseNav.vue'

const route = useRoute()
const userStore = useUserStore()
const documentType = computed(() => route.meta.documentType || 'INBOUND')
const title = computed(() => route.meta.title || '单据')
const canCreate = computed(() => {
  if (documentType.value === 'INBOUND') return userStore.canPostWarehouseInbound
  if (documentType.value === 'OUTBOUND') return userStore.canPostWarehouseOutbound
  return userStore.canPostWarehouseTransfer
})

const loading = ref(false)
const saving = ref(false)
const searching = ref(false)
const dialogVisible = ref(false)
const items = ref([])
const warehouses = ref([])
const projects = ref([])
const materials = ref([])
const locations = ref([])
const sourceLocations = ref([])
const targetLocations = ref([])
const inboundOptions = INBOUND_BUSINESS_OPTIONS
const outboundOptions = OUTBOUND_BUSINESS_OPTIONS
const form = reactive({
  warehouse_id: null,
  location_id: null,
  project_id: null,
  material_id: null,
  quantity: 1,
  occurred_on: todayISODate(),
  handler: userStore.user?.full_name || userStore.user?.username || '',
  business_type: 'PURCHASE',
  reference_no: '',
  delivery_note_file: '',
  delivery_note_file_name: '',
  scrap_basis_file: '',
  scrap_basis_file_name: '',
  supplier_name: '',
  purchase_order_no: '',
  delivery_note_no: '',
  acceptance_no: '',
  acceptor: '',
  batch_no: '',
  serial_no: '',
  requisition_no: '',
  crew_name: '',
  requester_name: '',
  receiver_name: '',
  source_warehouse_id: null,
  source_location_id: null,
  source_project_id: null,
  target_warehouse_id: null,
  target_location_id: null,
  target_project_id: null
})
const selectedMaterialUnit = computed(() => materials.value.find(item => item.id === form.material_id)?.unit || '')

function businessLabel(value) {
  return BUSINESS_TYPE_LABELS[value] || value || '-'
}

function materialSummary(row) {
  const line = row.lines?.[0]
  if (!line) return '-'
  const unit = line.material_unit ? ` / ${line.material_unit}` : ''
  return `${line.material_code || ''} ${line.material_name || ''}${unit}`.trim()
}

function resolveQuantity() {
  const value = evaluateQuantityExpression(form.quantity, 3)
  const quantity = value ?? Number(form.quantity)
  if (!Number.isFinite(quantity) || quantity <= 0) {
    throw new Error('请输入有效数量，支持 +-*/，结果须大于 0')
  }
  return String(quantity)
}

async function openFile(path) {
  if (path) await openProtectedFile(path)
}

async function load() {
  loading.value = true
  try {
    const res = await listDocuments({ document_type: documentType.value, page_size: 50 })
    items.value = res.items || []
  } finally {
    loading.value = false
  }
}

async function searchMats(q) {
  if (!q) return
  searching.value = true
  try {
    materials.value = await listMaterials({ q })
  } finally {
    searching.value = false
  }
}

function openCreate() {
  form.business_type = documentType.value === 'OUTBOUND' ? 'ISSUE' : 'PURCHASE'
  form.delivery_note_file = ''
  form.delivery_note_file_name = ''
  form.scrap_basis_file = ''
  form.scrap_basis_file_name = ''
  dialogVisible.value = true
}

async function submit() {
  saving.value = true
  try {
    let quantity
    try {
      quantity = resolveQuantity()
    } catch (error) {
      ElMessage.error(error.message || '数量无效')
      return
    }
    if (documentType.value === 'OUTBOUND' && form.business_type === 'SCRAP_DISPOSAL' && !form.scrap_basis_file) {
      ElMessage.error('选择废旧处理必须上传废旧处理依据文件')
      return
    }
    if (documentType.value === 'INBOUND') {
      await postInbound({
        warehouse_id: form.warehouse_id,
        location_id: form.location_id,
        project_id: form.project_id,
        occurred_on: form.occurred_on,
        handler: form.handler,
        business_type: form.business_type,
        reference_no: form.reference_no,
        delivery_note_file: form.delivery_note_file || null,
        delivery_note_file_name: form.delivery_note_file_name || null,
        supplier_name: form.supplier_name || null,
        purchase_order_no: form.purchase_order_no || null,
        delivery_note_no: form.delivery_note_no || null,
        acceptance_no: form.acceptance_no || null,
        acceptor: form.acceptor || null,
        lines: [{ material_id: form.material_id, quantity, batch_no: form.batch_no || null, serial_no: form.serial_no || null }]
      })
    } else if (documentType.value === 'OUTBOUND') {
      await postOutbound({
        warehouse_id: form.warehouse_id,
        location_id: form.location_id,
        project_id: form.project_id,
        occurred_on: form.occurred_on,
        handler: form.handler,
        business_type: form.business_type,
        reference_no: form.reference_no,
        scrap_basis_file: form.scrap_basis_file || null,
        scrap_basis_file_name: form.scrap_basis_file_name || null,
        requisition_no: form.requisition_no || null,
        crew_name: form.crew_name || null,
        requester_name: form.requester_name || null,
        receiver_name: form.receiver_name || null,
        signed_off: true,
        lines: [{ material_id: form.material_id, quantity, batch_no: form.batch_no || null, serial_no: form.serial_no || null }]
      })
    } else {
      await postTransfer({
        occurred_on: form.occurred_on,
        handler: form.handler,
        reference_no: form.reference_no,
        lines: [{
          material_id: form.material_id,
          quantity,
          batch_no: form.batch_no || null,
          serial_no: form.serial_no || null,
          source_warehouse_id: form.source_warehouse_id,
          source_location_id: form.source_location_id,
          source_project_id: form.source_project_id,
          target_warehouse_id: form.target_warehouse_id,
          target_location_id: form.target_location_id,
          target_project_id: form.target_project_id
        }]
      })
    }
    ElMessage.success('已过账')
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function voidRow(row) {
  const { value } = await ElMessageBox.prompt('请填写冲销原因', '冲销单据', { inputPattern: /.+/, inputErrorMessage: '必须填写原因' })
  await voidDocument(row.id, { reason: value })
  ElMessage.success('已冲销')
  await load()
}

watch(() => form.warehouse_id, async (id) => {
  locations.value = id ? await listLocations(id) : []
  form.location_id = locations.value.find(item => item.is_default)?.id || locations.value[0]?.id || null
})
watch(() => form.source_warehouse_id, async (id) => {
  sourceLocations.value = id ? await listLocations(id) : []
})
watch(() => form.target_warehouse_id, async (id) => {
  targetLocations.value = id ? await listLocations(id) : []
})
watch(documentType, load)

onMounted(async () => {
  warehouses.value = await listWarehouses()
  projects.value = await listProjects()
  await load()
})
</script>

<style scoped>
.warehouse-page { display: grid; gap: 16px; }
</style>
