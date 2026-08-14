<template>
  <div class="warehouse-page">
    <WarehouseNav />
    <AppWorkspacePanel>
      <AppSectionCard>
        <template #header>库房与货位</template>
        <template #actions>
          <el-button v-if="userStore.canManageWarehouseMaster" type="primary" @click="openCreateWarehouse">新建库房</el-button>
        </template>
        <p class="warehouse-hint">
          暂存区是新建库房时自动创建的默认货位，用于物资尚未分拣到正式货位前的临时存放。可以改名或新增货位，但启用中的库房至少要保留一个默认货位。
        </p>
        <div v-for="item in items" :key="item.id" class="warehouse-card">
          <div class="warehouse-card__title">
            <strong>{{ item.name }}</strong>
            <span>{{ item.code }}</span>
            <el-tag size="small">{{ item.is_active ? '启用' : '停用' }}</el-tag>
            <div v-if="userStore.canManageWarehouseMaster" class="warehouse-card__actions">
              <el-button link type="primary" @click="openCreateLocation(item)">新增货位</el-button>
              <el-button link type="danger" @click="removeWarehouse(item)">删除库房</el-button>
            </div>
          </div>
          <p>{{ item.address || '未填写地址' }} / 负责人 {{ item.manager_name || '-' }}</p>
          <div class="locations">
            <el-tag
              v-for="loc in item.locations"
              :key="loc.id"
              class="location-tag"
              :type="loc.is_default ? 'success' : 'info'"
              :closable="userStore.canManageWarehouseMaster"
              @close="removeLocation(item, loc)"
            >
              {{ loc.name }} ({{ loc.code }}){{ loc.is_default ? ' · 暂存/默认' : '' }}
            </el-tag>
          </div>
        </div>
      </AppSectionCard>
    </AppWorkspacePanel>
    <el-dialog v-model="createVisible" title="新建库房" width="480px" append-to-body>
      <el-form :model="form" label-width="88px">
        <el-form-item label="编码"><el-input v-model="form.code" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="负责人"><el-input v-model="form.manager_name" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveWarehouse">保存</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="locationVisible" title="新增货位" width="420px" append-to-body>
      <el-form :model="locationForm" label-width="88px">
        <el-form-item label="编码"><el-input v-model="locationForm.code" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="locationForm.name" /></el-form-item>
        <el-form-item label="设为默认"><el-switch v-model="locationForm.is_default" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="locationVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingLocation" @click="saveLocation">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createLocation, createWarehouse, deleteLocation, deleteWarehouse, listWarehouses } from '@/api/warehouse'
import { useUserStore } from '@/stores/user'
import WarehouseNav from './WarehouseNav.vue'

const userStore = useUserStore()
const items = ref([])
const createVisible = ref(false)
const locationVisible = ref(false)
const saving = ref(false)
const savingLocation = ref(false)
const currentWarehouse = ref(null)
const form = reactive({ code: '', name: '', address: '', manager_name: '' })
const locationForm = reactive({ code: '', name: '', is_default: false })

async function load() {
  items.value = await listWarehouses({ include_inactive: true })
}

function openCreateWarehouse() {
  Object.assign(form, { code: '', name: '', address: '', manager_name: '' })
  createVisible.value = true
}

function openCreateLocation(item) {
  currentWarehouse.value = item
  Object.assign(locationForm, { code: '', name: '', is_default: false })
  locationVisible.value = true
}

async function saveWarehouse() {
  saving.value = true
  try {
    await createWarehouse(form)
    ElMessage.success('库房已创建，并自动建立暂存区作为默认货位')
    createVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function saveLocation() {
  if (!currentWarehouse.value) return
  savingLocation.value = true
  try {
    await createLocation(currentWarehouse.value.id, locationForm)
    ElMessage.success('货位已创建')
    locationVisible.value = false
    await load()
  } finally {
    savingLocation.value = false
  }
}

async function removeWarehouse(item) {
  await ElMessageBox.confirm(`确认删除库房「${item.name}」？有库存或单据的库房不能删除。`, '删除库房', { type: 'warning' })
  await deleteWarehouse(item.id)
  ElMessage.success('库房已删除')
  await load()
}

async function removeLocation(warehouse, loc) {
  await ElMessageBox.confirm(`确认删除货位「${loc.name}」？有库存或单据的货位不能删除。`, '删除货位', { type: 'warning' })
  await deleteLocation(loc.id)
  ElMessage.success('货位已删除')
  await load()
}

onMounted(load)
</script>

<style scoped lang="scss">
.warehouse-page { display: grid; gap: 16px; }
.warehouse-hint {
  margin: 0 0 12px;
  color: var(--text-secondary, #606266);
  line-height: 1.6;
}
.warehouse-card {
  display: grid;
  gap: 8px;
  padding: 12px 0;
  border-bottom: 1px solid hsl(var(--border));
}
.warehouse-card__title {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.warehouse-card__actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
}
.locations { display: flex; flex-wrap: wrap; gap: 8px; }
</style>
