<template>
  <div class="invoice-import-workbench">
    <AppPageHeader title="电子发票导入" description="上传发票压缩包，解析后确认挂账" />

    <AppWorkspacePanel>
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

    <el-drawer v-model="itemDrawerVisible" size="60%" title="发票识别明细">
      <div class="drawer-context" v-if="selectedBatch">
        <strong>{{ selectedBatch.batch_code }}</strong>
        <span>{{ selectedBatch.original_filename }}</span>
      </div>
      <el-table :data="items" border>
        <el-table-column prop="invoice_number" label="发票号" width="170" />
        <el-table-column prop="direction" label="方向" width="100" />
        <el-table-column prop="seller_name" label="销售方" min-width="180" />
        <el-table-column prop="buyer_name" label="购买方" min-width="180" />
        <el-table-column prop="total_amount" label="价税合计" width="120" align="right" />
        <el-table-column prop="match_status" label="匹配" width="130" />
        <el-table-column prop="confirmation_status" label="确认" width="120" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="openAllocation(row)">分摊</el-button>
            <el-button
              link
              type="success"
              :disabled="row.confirmation_status === 'confirmed'"
              @click="handleConfirm(row)"
            >确认</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <el-dialog v-model="allocationDialogVisible" title="新增分摊" width="520px" append-to-body>
      <el-form label-width="100px">
        <el-form-item label="方向">
          <el-radio-group v-model="allocationForm.direction" @change="handleDirectionChange">
            <el-radio-button value="upstream">上游</el-radio-button>
            <el-radio-button value="downstream">下游</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="关联合同">
          <el-select
            v-model="allocationForm.contract_id"
            filterable
            remote
            clearable
            :remote-method="searchContracts"
            :loading="contractLoading"
            placeholder="输入合同序号、编号或名称搜索"
            style="width: 100%"
          >
            <el-option
              v-for="contract in contractOptions"
              :key="contract.id"
              :label="contractOptionLabel(contract)"
              :value="contract.id"
            />
          </el-select>
          <div v-if="candidateOptions.length" class="candidate-hint">
            系统候选：
            <el-button
              v-for="candidate in candidateOptions"
              :key="candidate.id"
              link
              type="primary"
              @click="selectCandidate(candidate)"
            >
              {{ candidateLabel(candidate) }}（{{ candidate.score }} 分）
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="分摊金额">
          <el-input-number v-model="allocationForm.amount" :min="0.01" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="allocationForm.description" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="allocationDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAllocation">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'
import { confirmItem, createAllocation, listBatchItems, listBatches, uploadBatch } from '@/api/invoiceImport'
import { getContract as getUpstreamContract, getContracts as getUpstreamContracts } from '@/api/contractUpstream'
import { getContract as getDownstreamContract, getContracts as getDownstreamContracts } from '@/api/contractDownstream'

const batches = ref([])
const selectedBatch = ref(null)
const selectedItem = ref(null)
const items = ref([])
const itemDrawerVisible = ref(false)
const allocationDialogVisible = ref(false)
const contractLoading = ref(false)
const contractOptions = ref([])
const allocationForm = reactive({
  direction: 'upstream',
  contract_id: null,
  amount: 0.01,
  description: ''
})

async function loadBatches() {
  batches.value = await listBatches()
}

async function handleFileSelected(file) {
  await uploadBatch(file.raw)
  ElMessage.success('发票批次已上传，系统开始解析')
  await loadBatches()
}

async function selectBatch(row) {
  selectedBatch.value = row
  items.value = await listBatchItems(row.id)
  itemDrawerVisible.value = true
}

async function openAllocation(row) {
  selectedItem.value = row
  allocationForm.direction = row.direction === 'downstream' ? 'downstream' : 'upstream'
  allocationForm.contract_id = null
  allocationForm.amount = Number(row.total_amount || 0)
  allocationForm.description = row.remarks || ''
  contractOptions.value = []
  allocationDialogVisible.value = true
  const getter = allocationForm.direction === 'upstream'
    ? getUpstreamContract
    : getDownstreamContract
  const ids = candidateOptions.value.map((candidate) => candidate.contractId)
  const candidates = await Promise.all(ids.map(async (id) => {
    try {
      return await getter(id)
    } catch {
      return null
    }
  }))
  contractOptions.value = candidates.filter(Boolean)
}

const candidateOptions = computed(() => (selectedItem.value?.candidates || [])
  .filter((candidate) => candidate.direction === allocationForm.direction)
  .map((candidate) => ({
    ...candidate,
    contractId: candidate.direction === 'upstream'
      ? candidate.upstream_contract_id
      : candidate.downstream_contract_id
  }))
  .filter((candidate) => candidate.contractId))

function contractOptionLabel(contract) {
  return `[${contract.serial_number || '-'}] ${contract.contract_name} (${contract.contract_code || '-'})`
}

function candidateLabel(candidate) {
  const contract = contractOptions.value.find((option) => option.id === candidate.contractId)
  return contract ? contractOptionLabel(contract) : '候选合同'
}

function handleDirectionChange() {
  allocationForm.contract_id = null
  contractOptions.value = []
}

function selectCandidate(candidate) {
  allocationForm.contract_id = candidate.contractId
}

async function searchContracts(query) {
  if (!query) {
    contractOptions.value = []
    return
  }
  contractLoading.value = true
  try {
    const loader = allocationForm.direction === 'upstream'
      ? getUpstreamContracts
      : getDownstreamContracts
    const response = await loader({ keyword: query, page: 1, page_size: 20 })
    contractOptions.value = response.items || []
  } finally {
    contractLoading.value = false
  }
}

async function saveAllocation() {
  if (!selectedItem.value) return
  if (!allocationForm.contract_id) {
    ElMessage.warning('请选择关联合同')
    return
  }
  const data = {
    direction: allocationForm.direction,
    amount: allocationForm.amount,
    description: allocationForm.description || undefined,
  }
  if (allocationForm.direction === 'upstream') {
    data.upstream_contract_id = allocationForm.contract_id
  } else {
    data.downstream_contract_id = allocationForm.contract_id
  }
  await createAllocation(selectedItem.value.id, data)
  ElMessage.success('分摊已保存')
  allocationDialogVisible.value = false
  if (selectedBatch.value) {
    items.value = await listBatchItems(selectedBatch.value.id)
  }
}

async function handleConfirm(row) {
  await confirmItem(row.id)
  ElMessage.success('已确认挂账')
  if (selectedBatch.value) {
    items.value = await listBatchItems(selectedBatch.value.id)
  }
}

onMounted(loadBatches)
</script>

<style scoped>
.invoice-import-workbench {
  display: grid;
  gap: 18px;
}

.candidate-hint {
  margin-top: 8px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
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

.drawer-context {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  color: var(--el-text-color-secondary);
}

.drawer-context strong {
  color: var(--el-text-color-primary);
}
</style>
