<template>
  <div class="warehouse-page">
    <WarehouseNav />
    <AppWorkspacePanel>
      <AppSectionCard>
        <template #header>期初材料录入</template>
        <template #actions>
          <el-button @click="downloadTemplate">下载 Excel 模板</el-button>
          <el-button
            v-if="userStore.canImportWarehouseData"
            type="primary"
            :loading="importing"
            @click="fileInput?.click()"
          >
            导入 Excel
          </el-button>
          <input
            ref="fileInput"
            class="hidden-file"
            type="file"
            accept=".xlsx,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            @change="onFileChange"
          >
        </template>
        <p class="opening-hint">
          模板含物资档案、库房货位、项目对照。在「期初录入」表填写物资编码、库房编码、项目编码和数量后导入，系统会按期初入库立即过账。货位可空，空则入该库房暂存区。
        </p>
        <div v-if="lastResult" class="opening-result">
          <el-alert
            :title="`已生成 ${lastResult.created_count} 张期初单，共 ${lastResult.line_count} 行${lastResult.skipped_count ? `，跳过 ${lastResult.skipped_count} 行` : ''}`"
            :type="lastResult.skipped_count ? 'warning' : 'success'"
            show-icon
            :closable="false"
          />
          <el-table v-if="lastResult.errors?.length" :data="lastResult.errors" border class="opening-errors">
            <el-table-column prop="row_no" label="行号" width="80" />
            <el-table-column prop="message" label="原因" min-width="280" />
          </el-table>
        </div>
      </AppSectionCard>
      <AppSectionCard>
        <template #header>已导入期初单</template>
        <AppDataTable>
          <el-table v-loading="loading" :data="items" border>
            <el-table-column prop="document_no" label="单号" min-width="160" />
            <el-table-column prop="occurred_on" label="日期" width="120" />
            <el-table-column label="物资 / 单位" min-width="220">
              <template #default="{ row }">{{ materialSummary(row) }}</template>
            </el-table-column>
            <el-table-column label="数量" width="100">
              <template #default="{ row }">{{ row.lines?.[0]?.quantity ?? '-' }}</template>
            </el-table-column>
            <el-table-column prop="handler" label="经办人" width="120" />
            <el-table-column prop="status" label="状态" width="100" />
            <el-table-column prop="reference_no" label="来源" min-width="160" />
          </el-table>
        </AppDataTable>
      </AppSectionCard>
    </AppWorkspacePanel>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { downloadOpeningTemplate, importOpeningEntries, listDocuments } from '@/api/warehouse'
import { downloadExcel } from '@/utils/download'
import { useUserStore } from '@/stores/user'
import WarehouseNav from './WarehouseNav.vue'

const userStore = useUserStore()
const fileInput = ref(null)
const importing = ref(false)
const loading = ref(false)
const items = ref([])
const lastResult = ref(null)

function materialSummary(row) {
  const lines = row.lines || []
  if (!lines.length) return '-'
  return lines.map((line) => {
    const unit = line.material_unit ? ` / ${line.material_unit}` : ''
    return `${line.material_code || ''} ${line.material_name || ''}${unit}`.trim()
  }).join('；')
}

async function load() {
  loading.value = true
  try {
    const res = await listDocuments({
      document_type: 'INBOUND',
      business_type: 'OPENING',
      page_size: 50
    })
    items.value = res.items || []
  } finally {
    loading.value = false
  }
}

async function downloadTemplate() {
  const blob = await downloadOpeningTemplate()
  downloadExcel(blob, '期初材料录入表.xlsx')
  ElMessage.success('模板已开始下载')
}

async function onFileChange(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  importing.value = true
  try {
    lastResult.value = await importOpeningEntries(file)
    if (lastResult.value.created_count) {
      ElMessage.success(`已导入 ${lastResult.value.created_count} 张期初单`)
    } else if (lastResult.value.skipped_count) {
      ElMessage.warning('没有成功导入的行，请检查错误列表')
    }
    await load()
  } finally {
    importing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.warehouse-page { display: grid; gap: 16px; }
.hidden-file { display: none; }
.opening-hint {
  margin: 0 0 12px;
  color: var(--text-secondary, #606266);
  line-height: 1.6;
}
.opening-result { display: grid; gap: 12px; }
.opening-errors { margin-top: 4px; }
</style>
