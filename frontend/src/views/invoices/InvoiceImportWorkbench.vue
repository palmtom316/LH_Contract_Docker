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
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="primary" @click="selectBatch(row)">查看</el-button>
            <el-button link type="danger" @click="handleDeleteBatch(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </AppWorkspacePanel>

    <el-drawer v-model="itemDrawerVisible" size="min(920px, 96vw)" title="发票识别明细">
      <div class="drawer-context" v-if="selectedBatch">
        <strong>{{ selectedBatch.batch_code }}</strong>
        <span>{{ selectedBatch.original_filename }}</span>
      </div>
      <div v-if="items.length" class="invoice-card-list">
        <article v-for="item in items" :key="item.id" class="invoice-review-card">
          <header class="invoice-card-header">
            <div>
              <span class="invoice-card-kicker">发票号码</span>
              <h3>{{ item.invoice_number || '待补充' }}</h3>
            </div>
            <div class="invoice-card-statuses">
              <el-tag size="small" effect="plain">{{ directionLabel(item.direction) }}</el-tag>
              <el-tag size="small" :type="matchTagType(item.match_status)" effect="light">
                {{ matchStatusLabel(item.match_status) }}
              </el-tag>
              <el-tag size="small" :type="item.confirmation_status === 'confirmed' ? 'success' : 'info'" effect="light">
                {{ confirmationStatusLabel(item.confirmation_status) }}
              </el-tag>
            </div>
            <div class="invoice-card-total">
              <span>价税合计</span>
              <strong>¥ {{ formatAmount(item.total_amount) }}</strong>
            </div>
          </header>

          <section class="invoice-project-band">
            <div>
              <span>建筑项目名称</span>
              <strong>{{ item.construction_project_name || '未识别' }}</strong>
            </div>
            <div>
              <span>项目名称</span>
              <strong>{{ item.project_name || '未识别' }}</strong>
            </div>
          </section>

          <dl class="invoice-detail-grid">
            <div><dt>销售方</dt><dd>{{ item.seller_name || '-' }}</dd></div>
            <div><dt>购买方</dt><dd>{{ item.buyer_name || '-' }}</dd></div>
            <div><dt>开票日期</dt><dd>{{ item.invoice_date || '-' }}</dd></div>
            <div><dt>发票类型</dt><dd>{{ item.invoice_type || '-' }}</dd></div>
          </dl>

          <section class="invoice-match-panel" :class="{ 'is-empty': !item.candidates?.length }">
            <span class="invoice-match-label">匹配合同</span>
            <div v-if="item.candidates?.length" class="matched-contract-list">
              <div v-for="candidate in item.candidates" :key="candidate.id" class="matched-contract">
                <strong>[{{ candidate.contract_serial_number || '-' }}] {{ candidate.contract_name || '合同信息缺失' }}</strong>
                <span v-if="candidate.contract_code">{{ candidate.contract_code }}</span>
              </div>
            </div>
            <span v-else class="invoice-match-empty">未按建筑项目名称找到合同，可手动搜索选择</span>
          </section>

          <footer class="invoice-card-actions">
            <el-button icon="Connection" @click="openAllocation(item)">分摊到合同</el-button>
            <el-button
              type="success"
              icon="CircleCheck"
              :disabled="item.confirmation_status === 'confirmed'"
              @click="handleConfirm(item)"
            >确认挂账</el-button>
          </footer>
        </article>
      </div>
      <el-empty v-else description="该批次暂无发票识别明细" />
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
import { ElMessage, ElMessageBox } from 'element-plus'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'
import { confirmItem, createAllocation, deleteBatch, listBatchItems, listBatches, uploadBatch } from '@/api/invoiceImport'
import { getContracts as getUpstreamContracts } from '@/api/contractUpstream'
import { getContracts as getDownstreamContracts } from '@/api/contractDownstream'

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

async function handleDeleteBatch(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除发票导入批次“${row.original_filename}”吗？`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  await deleteBatch(row.id)
  if (selectedBatch.value?.id === row.id) {
    itemDrawerVisible.value = false
    selectedBatch.value = null
    items.value = []
  }
  ElMessage.success('发票导入批次已删除')
  await loadBatches()
}

async function openAllocation(row) {
  selectedItem.value = row
  allocationForm.direction = row.direction === 'downstream' ? 'downstream' : 'upstream'
  allocationForm.contract_id = null
  allocationForm.amount = Number(row.total_amount || 0)
  allocationForm.description = row.construction_project_name || row.project_name || row.remarks || ''
  allocationDialogVisible.value = true
  contractOptions.value = candidateOptions.value.map((candidate) => ({
    id: candidate.contractId,
    serial_number: candidate.contract_serial_number,
    contract_code: candidate.contract_code,
    contract_name: candidate.contract_name,
  }))
  allocationForm.contract_id = candidateOptions.value[0]?.contractId || null
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
  return `[${candidate.contract_serial_number || '-'}] ${candidate.contract_name || '候选合同'}`
}

function formatAmount(value) {
  return Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function directionLabel(direction) {
  if (direction === 'upstream') return '上游开票'
  if (direction === 'downstream') return '下游收票'
  return '方向待确认'
}

function matchStatusLabel(status) {
  return status === 'matched' ? '已匹配' : '未匹配'
}

function matchTagType(status) {
  return status === 'matched' ? 'success' : 'warning'
}

function confirmationStatusLabel(status) {
  return status === 'confirmed' ? '已挂账' : '待确认'
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

.invoice-card-list {
  display: grid;
  gap: 16px;
}

.invoice-review-card {
  overflow: hidden;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-bg-color);
  box-shadow: 0 8px 24px rgb(31 45 61 / 6%);
}

.invoice-card-header {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) auto auto;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
}

.invoice-card-kicker,
.invoice-card-total span,
.invoice-project-band span,
.invoice-match-label {
  display: block;
  margin-bottom: 5px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .04em;
}

.invoice-card-header h3 {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 18px;
  font-variant-numeric: tabular-nums;
}

.invoice-card-statuses {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;
}

.invoice-card-total {
  min-width: 140px;
  text-align: right;
}

.invoice-card-total strong {
  color: var(--el-color-primary);
  font-size: 20px;
  font-variant-numeric: tabular-nums;
}

.invoice-project-band {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  padding: 16px 20px;
  border-block: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
}

.invoice-project-band strong {
  display: block;
  color: var(--el-text-color-primary);
  line-height: 1.55;
}

.invoice-detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  margin: 0;
  padding: 6px 20px;
}

.invoice-detail-grid div {
  display: grid;
  grid-template-columns: 72px 1fr;
  gap: 8px;
  padding: 9px 0;
}

.invoice-detail-grid dt {
  color: var(--el-text-color-secondary);
}

.invoice-detail-grid dd {
  margin: 0;
  color: var(--el-text-color-primary);
  overflow-wrap: anywhere;
}

.invoice-match-panel {
  margin: 4px 20px 16px;
  padding: 13px 15px;
  border: 1px solid var(--el-color-success-light-7);
  border-left: 4px solid var(--el-color-success);
  border-radius: 6px;
  background: var(--el-color-success-light-9);
}

.invoice-match-panel.is-empty {
  border-color: var(--el-color-warning-light-7);
  border-left-color: var(--el-color-warning);
  background: var(--el-color-warning-light-9);
}

.matched-contract-list {
  display: grid;
  gap: 8px;
}

.matched-contract {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.matched-contract strong {
  color: var(--el-text-color-primary);
  line-height: 1.5;
}

.matched-contract span,
.invoice-match-empty {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.invoice-card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--el-border-color-lighter);
}

@media (max-width: 720px) {
  .invoice-card-header,
  .invoice-project-band,
  .invoice-detail-grid {
    grid-template-columns: 1fr;
  }

  .invoice-card-statuses {
    justify-content: flex-start;
  }

  .invoice-card-total {
    text-align: left;
  }

  .matched-contract {
    align-items: flex-start;
    flex-direction: column;
    gap: 2px;
  }

  .invoice-card-actions {
    justify-content: stretch;
  }

  .invoice-card-actions .el-button {
    flex: 1;
  }
}
</style>
