<template>
  <div class="warehouse-page">
    <WarehouseNav />
    <AppWorkspacePanel>
      <AppSectionCard>
        <template #header>流水与报表</template>
        <template #actions>
          <el-button v-if="userStore.canExportWarehouseData" @click="download">导出流水</el-button>
        </template>
        <AppDataTable>
          <el-table v-loading="loading" :data="items" border>
            <el-table-column prop="occurred_on" label="日期" width="120" />
            <el-table-column prop="document_no" label="单号" min-width="150" />
            <el-table-column prop="document_type" label="类型" width="120" />
            <el-table-column prop="warehouse_name" label="库房" />
            <el-table-column prop="location_name" label="货位" />
            <el-table-column prop="project_name" label="项目" />
            <el-table-column prop="material_code" label="编码" />
            <el-table-column prop="material_name" label="物资" />
            <el-table-column prop="quantity_delta" label="数量变化" width="110" />
          </el-table>
        </AppDataTable>
      </AppSectionCard>
    </AppWorkspacePanel>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { exportLedger, listLedger } from '@/api/warehouse'
import { useUserStore } from '@/stores/user'
import WarehouseNav from './WarehouseNav.vue'

const userStore = useUserStore()
const loading = ref(false)
const items = ref([])

async function load() {
  loading.value = true
  try {
    const res = await listLedger({ page_size: 100 })
    items.value = res.items || []
  } finally {
    loading.value = false
  }
}

async function download() {
  const blob = await exportLedger()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'warehouse-ledger.xlsx'
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(load)
</script>

<style scoped>
.warehouse-page { display: grid; gap: 16px; }
</style>
