<template>
  <el-dialog
    v-model="dialogVisible"
    class="contract-query-dialog"
    append-to-body
    :close-on-click-modal="false"
    :fullscreen="isMobile"
    :width="dialogWidth"
  >
    <template #header>
      <div class="contract-query-dialog__header">
        <div>
          <div class="contract-query-dialog__eyebrow">合同查询</div>
          <div class="contract-query-dialog__title">上游合同联查面板</div>
        </div>
        <div class="contract-query-dialog__meta">
          <span class="contract-query-dialog__badge">仅上游合同</span>
          <span class="contract-query-dialog__shortcut">Ctrl / Cmd + K</span>
        </div>
      </div>
    </template>

    <div class="contract-query-panel">
      <AppWorkspacePanel panel-class="contract-query-panel__workspace">
        <AppSectionCard class="contract-query-panel__section">
          <template #header>动态筛选</template>
          <template #actions>
            <button
              data-testid="contract-query-export"
              type="button"
              class="contract-query-panel__action-button"
              :disabled="exportLoading || !total"
              @click="handleExport"
            >
              {{ exportLoading ? '导出中...' : '导出 Excel' }}
            </button>
            <button type="button" class="contract-query-panel__action-button" @click="resetFilters">重置</button>
          </template>

          <AppFilterBar inline-actions>
            <el-input
              v-model="keyword"
              data-testid="contract-query-keyword"
              class="filter-control--search contract-query-panel__keyword"
              placeholder="合同名称 / 合同编号 / 合同序号"
              clearable
            />
            <el-input
              v-model="partyAName"
              data-testid="contract-query-party-a"
              class="filter-control--wide contract-query-panel__party-a"
              placeholder="甲方单位"
              clearable
            />
            <DictSelect
              v-model="contractCategory"
              category="contract_category"
              placeholder="合同类别"
              clearable
            />
            <DictSelect
              v-model="companyCategory"
              category="project_category"
              placeholder="合同公司分类"
              clearable
            />
            <AppRangeField
              v-model="signDateRange"
              class="filter-control--range-wide"
              start-placeholder="签约开始日期"
              end-placeholder="签约结束日期"
            />
            <template #actions>
              <div class="contract-query-panel__filter-tip">
                按输入与选择自动筛选，结果始终限定为上游合同。
              </div>
            </template>
          </AppFilterBar>
        </AppSectionCard>

        <AppSectionCard class="contract-query-panel__section">
          <template #header>筛选结果</template>
          <template #actions>
            <div class="contract-query-panel__stats">
              <span>{{ total }} 份上游合同</span>
              <span v-if="loading">刷新中...</span>
            </div>
          </template>

          <AppEmptyState
            v-if="errorMessage"
            title="合同查询失败"
            :description="errorMessage"
          />
          <AppEmptyState
            v-else-if="!loading && hasLoaded && rows.length === 0"
            title="暂无符合条件的上游合同"
            description="调整甲方单位、合同类别、公司分类或签约日期后会自动刷新。"
          />
          <div v-else class="contract-query-table-shell">
            <AppDataTable>
              <table class="contract-query-table">
                <thead>
                  <tr>
                    <th>合同名称</th>
                    <th>甲方单位</th>
                    <th>乙方单位</th>
                    <th class="is-number">签约金额</th>
                    <th>签约日期</th>
                    <th class="is-number">应收款</th>
                    <th class="is-number">挂账金额</th>
                    <th class="is-number">已收款</th>
                    <th class="is-number">结算金额</th>
                    <th class="is-number">关联下游合同个数</th>
                    <th class="is-number">关联下游合同签约总金额</th>
                    <th class="is-number">关联下游合同结算总金额</th>
                    <th class="is-number">关联下游合同已付款总金额</th>
                    <th class="is-number">关联管理合同个数</th>
                    <th class="is-number">关联管理合同签约总金额</th>
                    <th class="is-number">关联管理合同结算总金额</th>
                    <th class="is-number">关联管理合同已付款总金额</th>
                    <th class="is-number">关联无合同费用总金额</th>
                    <th class="is-number">关联零星用工总金额</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in rows" :key="row.id">
                    <td class="is-wide">
                      <button type="button" class="table-link table-link--primary" @click="openUpstreamDetail(row)">
                        {{ row.contract_name }}
                      </button>
                    </td>
                    <td>{{ row.party_a_name || '-' }}</td>
                    <td>{{ row.party_b_name || '-' }}</td>
                    <td class="is-number">{{ formatMoney(row.contract_amount) }}</td>
                    <td>{{ formatDate(row.sign_date) }}</td>
                    <td class="is-number">{{ formatMoney(row.receivable_amount) }}</td>
                    <td class="is-number">{{ formatMoney(row.invoiced_amount) }}</td>
                    <td class="is-number">{{ formatMoney(row.received_amount) }}</td>
                    <td class="is-number">{{ formatMoney(row.settlement_amount) }}</td>
                    <td class="is-number">
                      <button
                        :data-testid="`drilldown-downstream-count-${row.id}`"
                        type="button"
                        class="table-link"
                        :disabled="!row.downstream_contract_count"
                        @click="openRelatedList('downstream', row)"
                      >
                        {{ row.downstream_contract_count }}
                      </button>
                    </td>
                    <td class="is-number">
                      <button type="button" class="table-link" :disabled="!row.downstream_contract_amount" @click="openRelatedList('downstream', row)">
                        {{ formatMoney(row.downstream_contract_amount) }}
                      </button>
                    </td>
                    <td class="is-number">
                      <button type="button" class="table-link" :disabled="!row.downstream_settlement_amount" @click="openRelatedList('downstream', row)">
                        {{ formatMoney(row.downstream_settlement_amount) }}
                      </button>
                    </td>
                    <td class="is-number">
                      <button type="button" class="table-link" :disabled="!row.downstream_paid_amount" @click="openRelatedList('downstream', row)">
                        {{ formatMoney(row.downstream_paid_amount) }}
                      </button>
                    </td>
                    <td class="is-number">
                      <button type="button" class="table-link" :disabled="!row.management_contract_count" @click="openRelatedList('management', row)">
                        {{ row.management_contract_count }}
                      </button>
                    </td>
                    <td class="is-number">
                      <button type="button" class="table-link" :disabled="!row.management_contract_amount" @click="openRelatedList('management', row)">
                        {{ formatMoney(row.management_contract_amount) }}
                      </button>
                    </td>
                    <td class="is-number">
                      <button type="button" class="table-link" :disabled="!row.management_settlement_amount" @click="openRelatedList('management', row)">
                        {{ formatMoney(row.management_settlement_amount) }}
                      </button>
                    </td>
                    <td class="is-number">
                      <button type="button" class="table-link" :disabled="!row.management_paid_amount" @click="openRelatedList('management', row)">
                        {{ formatMoney(row.management_paid_amount) }}
                      </button>
                    </td>
                    <td class="is-number">
                      <button type="button" class="table-link" :disabled="!row.non_contract_expense_total" @click="openRelatedList('expense', row)">
                        {{ formatMoney(row.non_contract_expense_total) }}
                      </button>
                    </td>
                    <td class="is-number">
                      <button type="button" class="table-link" :disabled="!row.zero_hour_labor_total" @click="openRelatedList('labor', row)">
                        {{ formatMoney(row.zero_hour_labor_total) }}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </AppDataTable>

            <div class="contract-query-panel__pagination">
              <el-pagination
                :current-page="page"
                :page-size="pageSize"
                :page-sizes="[20, 50, 100]"
                layout="total, sizes, prev, pager, next"
                :total="total"
                @current-change="handlePageChange"
                @size-change="handlePageSizeChange"
              />
            </div>
          </div>
        </AppSectionCard>
      </AppWorkspacePanel>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { exportUpstreamContractQuery, queryUpstreamContracts } from '@/api/contractSearch'
import DictSelect from '@/components/DictSelect.vue'
import AppRangeField from '@/components/ui/AppRangeField.vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'
import AppSectionCard from '@/components/ui/AppSectionCard.vue'
import AppFilterBar from '@/components/ui/AppFilterBar.vue'
import AppDataTable from '@/components/ui/AppDataTable.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])
const router = useRouter()

const keyword = ref('')
const partyAName = ref('')
const contractCategory = ref('')
const companyCategory = ref('')
const signDateRange = ref([])

const rows = shallowRef([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const exportLoading = ref(false)
const hasLoaded = ref(false)
const errorMessage = ref('')
const viewportWidth = ref(typeof window === 'undefined' ? 1280 : window.innerWidth)

let refreshTimer = null

const dialogVisible = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value)
})

const isMobile = computed(() => viewportWidth.value < 900)
const dialogWidth = computed(() => (isMobile.value ? '100%' : 'calc(100vw - 48px)'))

function syncViewportWidth() {
  viewportWidth.value = window.innerWidth
}

function getDateRangePayload() {
  if (!Array.isArray(signDateRange.value)) {
    return ['', '']
  }
  return [signDateRange.value[0] || '', signDateRange.value[1] || '']
}

function buildQueryParams(includePaging = true) {
  const [signDateStart, signDateEnd] = getDateRangePayload()
  const params = {
    keyword: keyword.value.trim(),
    partyAName: partyAName.value.trim(),
    contractCategory: contractCategory.value || '',
    companyCategory: companyCategory.value || '',
    signDateStart,
    signDateEnd
  }

  if (includePaging) {
    params.page = page.value
    params.pageSize = pageSize.value
  }

  return params
}

async function loadRows() {
  if (!dialogVisible.value) return

  loading.value = true
  errorMessage.value = ''
  try {
    const response = await queryUpstreamContracts(buildQueryParams(true))
    rows.value = response.items || []
    total.value = response.total || 0
    hasLoaded.value = true
  } catch (error) {
    rows.value = []
    total.value = 0
    errorMessage.value = error?.response?.data?.detail || '请稍后重试或联系管理员'
  } finally {
    loading.value = false
  }
}

function clearRefreshTimer() {
  if (refreshTimer) {
    clearTimeout(refreshTimer)
    refreshTimer = null
  }
}

function scheduleRefresh() {
  clearRefreshTimer()
  refreshTimer = setTimeout(() => {
    loadRows()
  }, 240)
}

function resetFilters() {
  keyword.value = ''
  partyAName.value = ''
  contractCategory.value = ''
  companyCategory.value = ''
  signDateRange.value = []
  page.value = 1
}

function formatMoney(value) {
  const amount = Number(value || 0)
  return amount.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

function formatDate(value) {
  return value || '-'
}

function closePanel() {
  dialogVisible.value = false
}

function openUpstreamDetail(row) {
  closePanel()
  router.push({
    name: 'UpstreamDetail',
    params: { id: row.id }
  })
}

function openRelatedList(type, row) {
  const upstreamContractId = String(row.id)
  const routeMap = {
    downstream: {
      path: '/contracts/downstream',
      query: { upstream_contract_id: upstreamContractId }
    },
    management: {
      path: '/contracts/management',
      query: { upstream_contract_id: upstreamContractId }
    },
    expense: {
      path: '/expenses',
      query: { tab: 'valuable', upstream_contract_id: upstreamContractId }
    },
    labor: {
      path: '/expenses',
      query: { tab: 'zeroHourLabor', upstream_contract_id: upstreamContractId }
    }
  }

  const target = routeMap[type]
  if (!target) return

  closePanel()
  router.push(target)
}

async function handleExport() {
  exportLoading.value = true
  try {
    const blob = await exportUpstreamContractQuery(buildQueryParams(false))
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `上游合同查询_${new Date().toISOString().slice(0, 10)}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '导出失败')
  } finally {
    exportLoading.value = false
  }
}

function handlePageChange(nextPage) {
  page.value = nextPage
  loadRows()
}

function handlePageSizeChange(nextSize) {
  pageSize.value = nextSize
  page.value = 1
  loadRows()
}

watch(
  () => dialogVisible.value,
  open => {
    if (open) {
      page.value = 1
      clearRefreshTimer()
      loadRows()
      return
    }
    clearRefreshTimer()
  },
  { immediate: true }
)

watch(
  () => [
    keyword.value,
    partyAName.value,
    contractCategory.value,
    companyCategory.value,
    ...(Array.isArray(signDateRange.value) ? signDateRange.value : [])
  ],
  () => {
    if (!dialogVisible.value) return
    page.value = 1
    scheduleRefresh()
  }
)

onMounted(() => {
  window.addEventListener('resize', syncViewportWidth)
})

onUnmounted(() => {
  clearRefreshTimer()
  window.removeEventListener('resize', syncViewportWidth)
})
</script>

<style scoped lang="scss">
.contract-query-panel {
  min-width: 0;
}

.contract-query-panel__workspace,
.contract-query-panel__section {
  gap: 0;
}

.contract-query-dialog__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.contract-query-dialog__eyebrow {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: hsl(var(--muted-foreground));
}

.contract-query-dialog__title {
  margin-top: 4px;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: hsl(var(--foreground));
}

.contract-query-dialog__meta {
  display: inline-flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.contract-query-dialog__badge,
.contract-query-dialog__shortcut {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid var(--workspace-panel-border);
  background: color-mix(in srgb, var(--surface-panel) 94%, var(--muted) 6%);
  color: hsl(var(--muted-foreground));
  font-size: 12px;
  font-weight: 600;
}

.contract-query-panel__filter-tip,
.contract-query-panel__stats {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  color: hsl(var(--muted-foreground));
  font-size: 13px;
}

.contract-query-panel__action-button {
  min-height: var(--workspace-control-height);
  padding: 0 14px;
  border: 1px solid var(--workspace-panel-border);
  border-radius: var(--radius);
  background: var(--surface-panel);
  color: hsl(var(--foreground));
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.contract-query-panel__action-button:hover:not(:disabled) {
  background: hsl(var(--muted));
}

.contract-query-panel__action-button:disabled {
  opacity: 0.52;
  cursor: not-allowed;
}

.contract-query-table-shell {
  display: grid;
  gap: 14px;
}

.contract-query-table {
  width: 100%;
  min-width: 1920px;
  border-collapse: collapse;
  background: var(--surface-panel);
}

.contract-query-table th,
.contract-query-table td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--workspace-panel-border);
  vertical-align: middle;
  font-size: 13px;
  line-height: 1.5;
  color: hsl(var(--foreground));
}

.contract-query-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: hsl(var(--muted));
  color: hsl(var(--muted-foreground));
  font-weight: 600;
  text-align: left;
  white-space: nowrap;
}

.contract-query-table tbody tr:hover {
  background: color-mix(in srgb, var(--surface-panel) 72%, var(--muted) 28%);
}

.contract-query-table .is-number {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.contract-query-table .is-wide {
  min-width: 220px;
}

.table-link {
  padding: 0;
  border: 0;
  background: transparent;
  color: hsl(var(--primary));
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.table-link:hover:not(:disabled) {
  color: hsl(var(--foreground));
}

.table-link:disabled {
  color: hsl(var(--muted-foreground));
  cursor: default;
}

.table-link--primary {
  text-align: left;
}

.contract-query-panel__pagination {
  display: flex;
  justify-content: flex-end;
}

:deep(.contract-query-dialog .el-dialog) {
  max-width: 1460px;
}

:deep(.contract-query-dialog .el-dialog__body) {
  padding-top: 0;
}

@media (max-width: 900px) {
  .contract-query-dialog__header {
    flex-direction: column;
  }

  .contract-query-dialog__meta {
    justify-content: flex-start;
  }

  .contract-query-dialog__title {
    font-size: 18px;
  }

  .contract-query-table th,
  .contract-query-table td {
    padding: 10px 12px;
  }
}
</style>
