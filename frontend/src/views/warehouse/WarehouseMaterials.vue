<template>
  <div class="warehouse-page">
    <WarehouseNav />
    <AppWorkspacePanel>
      <AppSectionCard>
        <template #header>物资档案</template>
        <template #actions>
          <el-button v-if="userStore.canManageWarehouseMaterials" type="primary" @click="openCreate">新建物资</el-button>
        </template>
        <AppFilterBar>
          <el-input v-model="query" placeholder="编码/名称/规格" clearable @keyup.enter="load" />
          <el-select v-model="category" placeholder="类别" clearable>
            <el-option label="主材" value="ZC" />
            <el-option label="辅材" value="FC" />
            <el-option label="工器具" value="GJ" />
            <el-option label="劳保" value="LB" />
          </el-select>
          <template #actions>
            <el-button type="primary" @click="load">搜索</el-button>
          </template>
        </AppFilterBar>
        <AppDataTable>
          <el-table v-loading="loading" :data="items" border>
            <el-table-column prop="code" label="编码" width="130" />
            <el-table-column prop="name" label="名称" min-width="160" />
            <el-table-column prop="brand" label="厂家" min-width="120" />
            <el-table-column prop="specification" label="规格" min-width="140" />
            <el-table-column prop="unit" label="单位" width="80" />
            <el-table-column prop="category" label="类别" width="80" />
            <el-table-column prop="supply_type" label="供应" width="80" />
            <el-table-column prop="condition" label="成色" width="90" />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">{{ row.is_active ? '启用' : '归档' }}</template>
            </el-table-column>
          </el-table>
        </AppDataTable>
      </AppSectionCard>
    </AppWorkspacePanel>

    <el-dialog v-model="dialogVisible" title="新建物资" width="520px" append-to-body>
      <el-form :model="form" label-width="88px">
        <el-form-item label="类别"><el-select v-model="form.category"><el-option label="主材" value="ZC" /><el-option label="辅材" value="FC" /><el-option label="工器具" value="GJ" /><el-option label="劳保" value="LB" /></el-select></el-form-item>
        <el-form-item label="供应"><el-select v-model="form.supply_type"><el-option label="甲供" value="J" /><el-option label="乙供" value="Y" /></el-select></el-form-item>
        <el-form-item label="成色"><el-select v-model="form.condition"><el-option label="新料" value="NEW" /><el-option label="废旧回收" value="SCRAP" /></el-select></el-form-item>
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="厂家"><el-input v-model="form.brand" /></el-form-item>
        <el-form-item label="规格"><el-input v-model="form.specification" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="form.unit" /></el-form-item>
        <el-form-item label="数量精度"><el-input-number v-model="form.quantity_scale" :min="0" :max="4" /></el-form-item>
        <el-form-item label="批次追踪"><el-switch v-model="form.tracks_batch" /></el-form-item>
        <el-form-item label="序列号"><el-switch v-model="form.tracks_serial" /></el-form-item>
        <el-form-item label="质保天数"><el-input-number v-model="form.shelf_life_days" :min="1" /></el-form-item>
        <el-form-item label="安全库存"><el-input-number v-model="form.minimum_stock" :min="0" :precision="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存并生成编码</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createMaterial, listMaterials } from '@/api/warehouse'
import { useUserStore } from '@/stores/user'
import WarehouseNav from './WarehouseNav.vue'

const userStore = useUserStore()
const loading = ref(false)
const saving = ref(false)
const items = ref([])
const query = ref('')
const category = ref('')
const dialogVisible = ref(false)
const form = reactive({
  category: 'ZC',
  supply_type: 'J',
  condition: 'NEW',
  name: '',
  brand: '',
  specification: '',
  unit: '',
  quantity_scale: 3,
  tracks_batch: false,
  tracks_serial: false,
  shelf_life_days: null,
  minimum_stock: 0
})

async function load() {
  loading.value = true
  try {
    items.value = await listMaterials({ q: query.value || undefined, category: category.value || undefined })
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialogVisible.value = true
}

async function save() {
  saving.value = true
  try {
    const created = await createMaterial(form)
    ElMessage.success(`已生成编码 ${created.code}`)
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.warehouse-page { display: grid; gap: 16px; }
</style>
