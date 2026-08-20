<template>
  <div class="warehouse-page">
    <WarehouseNav />
    <AppWorkspacePanel>
      <AppSectionCard>
        <template #header>库存总览</template>
        <template #actions>
          <el-button v-if="userStore.canExportWarehouseData" @click="downloadStock">导出库存</el-button>
        </template>
        <div class="metrics">
          <AppMetricCard title="库存维度" :value="String(summary.dimensions)" />
          <AppMetricCard title="物资种类" :value="String(summary.materials)" />
          <AppMetricCard title="低库存" :value="String(summary.lowStock)" />
          <AppMetricCard title="待盘点" :value="String(summary.pendingCounts)" />
          <AppMetricCard title="近效期" :value="String(summary.expiring)" />
          <AppMetricCard title="长期未动" :value="String(summary.idle)" />
        </div>
      </AppSectionCard>
      <AppSectionCard v-if="userStore.canManageWarehousePeriods || periods.length">
        <template #header>库存期间</template>
        <template #actions>
          <el-button v-if="userStore.canManageWarehousePeriods" @click="closeCurrent">结账本月</el-button>
        </template>
        <el-table :data="periods" border>
          <el-table-column prop="year" label="年" width="90" />
          <el-table-column prop="month" label="月" width="80" />
          <el-table-column prop="status" label="状态" width="120" />
          <el-table-column prop="reopen_reason" label="反结账原因" min-width="180" />
          <el-table-column prop="open_reason" label="开放原因" min-width="180" />
          <el-table-column v-if="userStore.canManageWarehousePeriods" label="操作" width="120">
            <template #default="{ row }">
              <el-button v-if="row.status === 'CLOSED'" link type="primary" @click="reopen(row)">反结账</el-button>
              <el-button v-else link type="danger" @click="closeRow(row)">结账</el-button>
            </template>
          </el-table-column>
        </el-table>
      </AppSectionCard>
      <AppSectionCard>
        <template #header>库存明细</template>
        <AppDataTable>
          <el-table v-loading="loading" :data="items" border>
            <el-table-column prop="warehouse_name" label="库房" min-width="120" />
            <el-table-column prop="location_name" label="货位" min-width="100" />
            <el-table-column prop="project_name" label="项目" min-width="140" />
            <el-table-column prop="material_code" label="物资编码" min-width="120" />
            <el-table-column prop="material_name" label="物资名称" min-width="160" />
            <el-table-column prop="quantity" label="数量" width="100" />
            <el-table-column prop="material_unit" label="单位" width="80" />
            <el-table-column prop="supply_type" label="供应" width="80" />
          </el-table>
        </AppDataTable>
      </AppSectionCard>
    </AppWorkspacePanel>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { closeWarehousePeriod, exportStock, getWarehouseReport, listCounts, listStockBalances, listWarehousePeriods, reopenWarehousePeriod } from '@/api/warehouse'
import { useUserStore } from '@/stores/user'
import WarehouseNav from './WarehouseNav.vue'

const userStore = useUserStore()
const loading = ref(false)
const items = ref([])
const periods = ref([])
const summary = reactive({ dimensions: 0, materials: 0, lowStock: 0, pendingCounts: 0, expiring: 0, idle: 0 })

async function load() {
  loading.value = true
  try {
    const res = await listStockBalances({ page: 1, page_size: 50, include_zero: true })
    items.value = res.items || []
    summary.dimensions = res.total || 0
    summary.materials = new Set(items.value.map(item => item.material_id)).size
    summary.lowStock = items.value.filter(item => Number(item.quantity) <= Number(item.minimum_stock || 0)).length
    const [counts, expiring, idle] = await Promise.all([listCounts(), getWarehouseReport('expiring'), getWarehouseReport('idle')])
    summary.pendingCounts = (counts.items || []).filter(item => ['DRAFT', 'ENTERED', 'REVIEWED'].includes(item.status)).length
    summary.expiring = (expiring.items || []).length
    summary.idle = (idle.items || []).length
    periods.value = await listWarehousePeriods()
  } finally {
    loading.value = false
  }
}

async function closeRow(row) {
  await closeWarehousePeriod({ year: row.year, month: row.month })
  ElMessage.success('期间已结账')
  await load()
}

async function closeCurrent() {
  const now = new Date()
  await closeWarehousePeriod({ year: now.getFullYear(), month: now.getMonth() + 1 })
  ElMessage.success('本月已结账')
  await load()
}

async function reopen(row) {
  await reopenWarehousePeriod({ year: row.year, month: row.month, reason: '管理员反结账补录' })
  ElMessage.success('期间已反结账')
  await load()
}

async function downloadStock() {
  const blob = await exportStock()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'warehouse-stock.xlsx'
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已开始下载')
}

onMounted(load)
</script>

<style scoped lang="scss">
.warehouse-page {
  display: grid;
  gap: 16px;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}
</style>
