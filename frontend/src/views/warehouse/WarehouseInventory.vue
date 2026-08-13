<template>
  <div class="warehouse-page">
    <WarehouseNav />
    <AppWorkspacePanel>
      <AppSectionCard>
        <template #header>库存查询</template>
        <AppFilterBar>
          <el-select v-model="filters.warehouse_id" placeholder="库房" clearable>
            <el-option v-for="item in warehouses" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
          <el-select v-model="filters.project_id" placeholder="项目" clearable>
            <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
          <el-input v-model="filters.q" placeholder="物资编码/名称" clearable />
          <template #actions>
            <el-button type="primary" @click="load">查询</el-button>
          </template>
        </AppFilterBar>
        <AppDataTable>
          <el-table v-loading="loading" :data="items" border>
            <el-table-column prop="warehouse_name" label="库房" />
            <el-table-column prop="location_name" label="货位" />
            <el-table-column prop="project_name" label="项目" />
            <el-table-column prop="material_code" label="编码" />
            <el-table-column prop="material_name" label="物资" />
            <el-table-column prop="quantity" label="数量" />
            <el-table-column prop="material_unit" label="单位" />
            <el-table-column prop="supply_type" label="供应" />
            <el-table-column prop="condition" label="成色" />
          </el-table>
        </AppDataTable>
      </AppSectionCard>
    </AppWorkspacePanel>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { listProjects, listStockBalances, listWarehouses } from '@/api/warehouse'
import WarehouseNav from './WarehouseNav.vue'

const loading = ref(false)
const items = ref([])
const warehouses = ref([])
const projects = ref([])
const filters = reactive({ warehouse_id: null, project_id: null, q: '' })

async function load() {
  loading.value = true
  try {
    const res = await listStockBalances({
      warehouse_id: filters.warehouse_id || undefined,
      project_id: filters.project_id || undefined,
      q: filters.q || undefined,
      page_size: 100
    })
    items.value = res.items || []
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  warehouses.value = await listWarehouses()
  projects.value = await listProjects()
  await load()
})
</script>

<style scoped>
.warehouse-page { display: grid; gap: 16px; }
</style>
