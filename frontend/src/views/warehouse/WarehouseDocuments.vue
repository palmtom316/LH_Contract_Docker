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
            <el-table-column prop="business_type" label="业务类型" width="130" />
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
            <el-option v-for="item in materials" :key="item.id" :label="`${item.code} ${item.name}`" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量"><el-input-number v-model="form.quantity" :min="0.0001" :precision="4" /></el-form-item>
        <el-form-item label="日期"><el-date-picker v-model="form.occurred_on" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="经办人"><el-input v-model="form.handler" /></el-form-item>
        <el-form-item v-if="documentType === 'INBOUND'" label="业务类型">
          <el-select v-model="form.business_type">
            <el-option label="采购入库" value="PURCHASE" />
            <el-option label="领用退回" value="RETURN" />
            <el-option label="拆除回收" value="DEMOLITION" />
            <el-option label="期初" value="OPENING" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="documentType === 'OUTBOUND'" label="业务类型">
          <el-select v-model="form.business_type">
            <el-option label="领用出库" value="ISSUE" />
            <el-option label="退废旧" value="SCRAP_RETURN" />
            <el-option label="报废" value="WRITE_OFF" />
          </el-select>
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
const form = reactive({
  warehouse_id: null,
  location_id: null,
  project_id: null,
  material_id: null,
  quantity: 1,
  occurred_on: new Date().toISOString().slice(0, 10),
  handler: userStore.user?.full_name || userStore.user?.username || '',
  business_type: 'PURCHASE',
  reference_no: '',
  source_warehouse_id: null,
  source_location_id: null,
  source_project_id: null,
  target_warehouse_id: null,
  target_location_id: null,
  target_project_id: null
})

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
  dialogVisible.value = true
}

async function submit() {
  saving.value = true
  try {
    if (documentType.value === 'INBOUND') {
      await postInbound({
        warehouse_id: form.warehouse_id,
        location_id: form.location_id,
        project_id: form.project_id,
        occurred_on: form.occurred_on,
        handler: form.handler,
        business_type: form.business_type,
        reference_no: form.reference_no,
        lines: [{ material_id: form.material_id, quantity: String(form.quantity) }]
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
        lines: [{ material_id: form.material_id, quantity: String(form.quantity) }]
      })
    } else {
      await postTransfer({
        occurred_on: form.occurred_on,
        handler: form.handler,
        reference_no: form.reference_no,
        lines: [{
          material_id: form.material_id,
          quantity: String(form.quantity),
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
