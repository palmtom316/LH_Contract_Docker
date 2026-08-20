<template>
  <div class="warehouse-page">
    <WarehouseNav />
    <AppWorkspacePanel>
      <AppSectionCard>
        <template #header>盘点</template>
        <template #actions>
          <el-button v-if="userStore.canEnterWarehouseCount" type="primary" @click="createVisible = true">新建盘点</el-button>
        </template>
        <AppDataTable>
          <el-table :data="items" border>
            <el-table-column prop="count_no" label="盘点单号" />
            <el-table-column prop="warehouse_name" label="库房" />
            <el-table-column prop="counted_on" label="日期" />
            <el-table-column prop="status" label="状态" />
            <el-table-column label="操作" width="160">
              <template #default="{ row }">
                <el-button link type="primary" @click="openCount(row)">录入</el-button>
                <el-button
                  v-if="userStore.canConfirmWarehouseCount && ['ENTERED', 'REVIEWED'].includes(row.status)"
                  link
                  type="warning"
                  @click="review(row)"
                >
                  复核
                </el-button>
                <el-button
                  v-if="userStore.canConfirmWarehouseCount && !['CONFIRMED', 'VOIDED'].includes(row.status)"
                  link
                  type="success"
                  @click="confirm(row)"
                >
                  确认
                </el-button>
                <el-button
                  v-if="userStore.canConfirmWarehouseCount && !['CONFIRMED', 'VOIDED'].includes(row.status)"
                  link
                  type="danger"
                  @click="voidRow(row)"
                >
                  作废
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </AppDataTable>
      </AppSectionCard>
    </AppWorkspacePanel>

    <el-dialog v-model="detailVisible" title="盘点明细" width="760px" append-to-body>
      <el-table :data="current?.lines || []" border>
        <el-table-column prop="material_code" label="编码" />
        <el-table-column prop="material_name" label="物资" />
        <el-table-column prop="material_unit" label="单位" width="80" />
        <el-table-column prop="book_quantity" label="账面" />
        <el-table-column label="实盘">
          <template #default="{ row }">
            <FormulaInput v-model="row.counted_quantity" :precision="3" placeholder="支持 +-*/" />
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="saveLines">保存实盘</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="createVisible" title="新建盘点" width="420px" append-to-body>
      <el-form label-width="80px">
        <el-form-item label="库房">
          <el-select v-model="createForm.warehouse_id">
            <el-option v-for="item in warehouses" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="createForm.counted_on" value-format="YYYY-MM-DD" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="create">创建快照</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { confirmCount, createCount, getCount, listCounts, listWarehouses, reviewCount, updateCountLines, voidCount } from '@/api/warehouse'
import { useUserStore } from '@/stores/user'
import { evaluateQuantityExpression } from '@/utils/quantityExpression'
import { todayISODate } from '@/utils/dateInput'
import FormulaInput from '@/components/FormulaInput.vue'
import WarehouseNav from './WarehouseNav.vue'

const userStore = useUserStore()
const items = ref([])
const warehouses = ref([])
const current = ref(null)
const detailVisible = ref(false)
const createVisible = ref(false)
const createForm = reactive({ warehouse_id: null, counted_on: todayISODate() })

async function load() {
  const res = await listCounts()
  items.value = res.items || []
}

async function openCount(row) {
  current.value = await getCount(row.id)
  detailVisible.value = true
}

async function saveLines() {
  await updateCountLines(current.value.id, {
    lines: current.value.lines.map(line => {
      const raw = line.counted_quantity ?? line.book_quantity
      const quantity = evaluateQuantityExpression(raw, 3) ?? Number(raw)
      return { id: line.id, counted_quantity: String(Number.isFinite(quantity) ? quantity : 0) }
    })
  })
  ElMessage.success('实盘已保存')
  await load()
}

async function confirm(row) {
  await confirmCount(row.id)
  ElMessage.success('盘点已确认并过账')
  await load()
}

async function review(row) {
  await reviewCount(row.id)
  ElMessage.success('差异已复核')
  await load()
}

async function voidRow(row) {
  await voidCount(row.id, { reason: '现场盘点作废后重新开放' })
  ElMessage.success('盘点已作废')
  await load()
}

async function create() {
  await createCount(createForm)
  createVisible.value = false
  await load()
}

onMounted(async () => {
  warehouses.value = await listWarehouses()
  await load()
})
</script>

<style scoped>
.warehouse-page { display: grid; gap: 16px; }
</style>
