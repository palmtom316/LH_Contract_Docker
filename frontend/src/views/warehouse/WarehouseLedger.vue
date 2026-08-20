<template>
  <div class="warehouse-page">
    <WarehouseNav />
    <AppWorkspacePanel>
      <AppSectionCard>
        <template #header>流水筛选</template>
        <el-form inline :model="filters">
          <el-form-item label="关键字">
            <el-input v-model="filters.q" placeholder="单号/物资/批次/序列号" clearable style="width: 200px" @keyup.enter="load" />
          </el-form-item>
          <el-form-item label="业务类型">
            <el-select v-model="filters.business_type" clearable style="width: 150px">
              <el-option v-for="item in businessOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="类别">
            <el-select v-model="filters.category" clearable style="width: 110px">
              <el-option label="主材" value="ZC" /><el-option label="辅材" value="FC" />
              <el-option label="工器具" value="GJ" /><el-option label="劳保" value="LB" />
            </el-select>
          </el-form-item>
          <el-form-item label="供应">
            <el-select v-model="filters.supply_type" clearable style="width: 100px">
              <el-option label="甲供" value="J" /><el-option label="乙供" value="Y" />
            </el-select>
          </el-form-item>
          <el-form-item label="成色">
            <el-select v-model="filters.condition" clearable style="width: 120px">
              <el-option label="新料" value="NEW" /><el-option label="废旧回收" value="SCRAP" />
            </el-select>
          </el-form-item>
          <el-form-item label="经办人">
            <el-input v-model="filters.handler" clearable style="width: 120px" />
          </el-form-item>
          <el-form-item label="日期">
            <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD" start-placeholder="开始" end-placeholder="结束" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="load">查询</el-button>
          </el-form-item>
        </el-form>
      </AppSectionCard>

      <AppSectionCard>
        <template #header>库存流水</template>
        <template #actions>
          <el-button v-if="userStore.canExportWarehouseData" @click="download">导出流水</el-button>
        </template>
        <AppDataTable>
          <el-table v-loading="loading" :data="items" border>
            <el-table-column prop="occurred_on" label="日期" width="110" />
            <el-table-column prop="document_no" label="单号" min-width="150" />
            <el-table-column prop="business_type" label="业务类型" width="110" />
            <el-table-column prop="warehouse_name" label="库房" />
            <el-table-column prop="location_name" label="货位" />
            <el-table-column prop="project_name" label="项目" />
            <el-table-column prop="material_code" label="编码" />
            <el-table-column prop="material_name" label="物资" />
            <el-table-column prop="batch_no" label="批次" width="100">
              <template #default="{ row }">{{ row.batch_no || '-' }}</template>
            </el-table-column>
            <el-table-column prop="serial_no" label="序列号" width="100">
              <template #default="{ row }">{{ row.serial_no || '-' }}</template>
            </el-table-column>
            <el-table-column prop="handler" label="经办人" width="90" />
            <el-table-column prop="quantity_delta" label="数量变化" width="110" />
          </el-table>
        </AppDataTable>
      </AppSectionCard>

      <AppSectionCard>
        <template #header>库存报表</template>
        <template #actions>
          <el-radio-group v-model="reportKind" size="small" @change="loadReport">
            <el-radio-button value="consumption">项目耗用</el-radio-button>
            <el-radio-button value="turnover">收发存</el-radio-button>
            <el-radio-button value="low-stock">低库存</el-radio-button>
            <el-radio-button value="idle">呆滞库存</el-radio-button>
            <el-radio-button value="expiring">近效期</el-radio-button>
          </el-radio-group>
        </template>
        <AppDataTable>
          <el-table v-loading="reportLoading" :data="reportItems" border>
            <el-table-column v-if="reportKind === 'consumption'" prop="project_name" label="项目" min-width="160" />
            <el-table-column v-if="reportKind !== 'consumption'" prop="warehouse_name" label="库房" min-width="120" />
            <el-table-column prop="material_code" label="编码" min-width="110" />
            <el-table-column prop="material_name" label="物资" min-width="150" />
            <el-table-column prop="material_unit" label="单位" width="70" />
            <el-table-column v-if="reportKind === 'turnover'" prop="inbound_qty" label="累计入库" width="110" />
            <el-table-column prop="outbound_qty" label="累计出库/耗用" width="130" />
            <el-table-column v-if="['low-stock', 'idle', 'expiring', 'turnover'].includes(reportKind)" prop="quantity" label="当前结存" width="110" />
            <el-table-column v-if="reportKind === 'low-stock'" prop="minimum_stock" label="安全库存" width="100" />
            <el-table-column v-if="reportKind === 'idle'" prop="idle_days" label="闲置天数" width="100" />
            <el-table-column v-if="reportKind === 'expiring'" prop="expiry_date" label="到期日" width="110" />
            <el-table-column v-if="reportKind === 'expiring'" prop="days_to_expiry" label="剩余天数" width="100" />
          </el-table>
        </AppDataTable>
      </AppSectionCard>
    </AppWorkspacePanel>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { exportLedger, getWarehouseReport, listLedger } from '@/api/warehouse'
import { useUserStore } from '@/stores/user'
import WarehouseNav from './WarehouseNav.vue'

const userStore = useUserStore()
const loading = ref(false)
const items = ref([])
const filters = reactive({
  q: '',
  business_type: null,
  category: null,
  supply_type: null,
  condition: null,
  handler: ''
})
const dateRange = ref(null)
const reportKind = ref('consumption')
const reportLoading = ref(false)
const reportItems = ref([])

const businessOptions = [
  { label: '采购入库', value: 'PURCHASE' },
  { label: '甲供入库', value: 'OWNER_SUPPLY' },
  { label: '退料入库', value: 'RETURN' },
  { label: '拆除回收', value: 'DEMOLITION' },
  { label: '领用出库', value: 'ISSUE' },
  { label: '废旧退库', value: 'SCRAP_RETURN' },
  { label: '报废处理', value: 'WRITE_OFF' },
  { label: '废旧处理', value: 'SCRAP_DISPOSAL' }
]

async function load() {
  loading.value = true
  try {
    const params = { page_size: 100 }
    for (const [key, value] of Object.entries(filters)) {
      if (value) params[key] = value
    }
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await listLedger(params)
    items.value = res.items || []
  } finally {
    loading.value = false
  }
}

async function loadReport() {
  reportLoading.value = true
  try {
    const res = await getWarehouseReport(reportKind.value)
    reportItems.value = res.items || []
  } finally {
    reportLoading.value = false
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

onMounted(() => {
  load()
  loadReport()
})
</script>
