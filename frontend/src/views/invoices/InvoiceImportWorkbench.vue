<template>
  <div class="invoice-import-workbench">
    <AppPageHeader title="电子发票导入" subtitle="上传发票压缩包，解析后确认挂账" />

    <AppWorkspacePanel>
      <template #header>
        <div class="workbench-toolbar">
          <div>
            <h2>导入批次</h2>
            <p>仅处理含 XML 的电子发票压缩包；确认前不会写入正式挂账。</p>
          </div>
          <div class="toolbar-actions">
            <el-upload :auto-upload="false" :show-file-list="false" accept=".zip" :on-change="handleFileSelected">
              <el-button type="primary">上传压缩包</el-button>
            </el-upload>
            <el-button @click="loadBatches">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="batches" border class="batch-table">
        <el-table-column prop="batch_code" label="批次号" width="190" />
        <el-table-column prop="original_filename" label="文件名" min-width="180" />
        <el-table-column prop="status" label="状态" width="150" />
        <el-table-column prop="total_items" label="总数" width="80" />
        <el-table-column prop="parsed_items" label="已解析" width="90" />
        <el-table-column prop="duplicate_items" label="重复" width="80" />
        <el-table-column prop="error_items" label="异常" width="80" />
        <el-table-column prop="confirmed_items" label="已确认" width="90" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="selectBatch(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </AppWorkspacePanel>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'
import { listBatches, uploadBatch } from '@/api/invoiceImport'

const batches = ref([])
const selectedBatch = ref(null)

async function loadBatches() {
  batches.value = await listBatches()
}

async function handleFileSelected(file) {
  await uploadBatch(file.raw)
  ElMessage.success('发票批次已上传，系统开始解析')
  await loadBatches()
}

function selectBatch(row) {
  selectedBatch.value = row
}

onMounted(loadBatches)
</script>

<style scoped>
.invoice-import-workbench {
  display: grid;
  gap: 18px;
}

.workbench-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.workbench-toolbar h2 {
  margin: 0 0 4px;
  color: var(--el-text-color-primary);
  font-size: 18px;
  font-weight: 700;
}

.workbench-toolbar p {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.batch-table {
  --el-table-border-color: var(--el-border-color-lighter);
}
</style>
