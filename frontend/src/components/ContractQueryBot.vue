<template>
  <div class="contract-query-panel" :class="{ 'contract-query-panel--assistant': isAssistant }">
    <component :is="shellTag" v-bind="shellProps" class="contract-query-panel__shell">
      <AppSectionCard class="contract-query-panel__section contract-query-panel__section--filters">
        <template #header>
          <div class="contract-query-panel__header-copy">
            <span v-if="isAssistant" class="contract-query-panel__eyebrow">Ctrl + K</span>
            <div class="contract-query-panel__title-block">
              <span class="contract-query-panel__title">{{ isAssistant ? '合同查询助手' : '合同查询' }}</span>
            </div>
          </div>
        </template>
        <template #actions>
          <button
            v-if="showExport"
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
            placeholder="上游合同名称 / 甲方单位 / 合同序号"
            clearable
          />
          <DictSelect
            v-model="companyCategory"
            class="filter-control--compact"
            category="project_category"
            placeholder="公司合同分类"
            clearable
          />
          <DictSelect
            v-model="contractCategory"
            class="filter-control--compact"
            category="contract_category"
            placeholder="合同类别"
            clearable
          />
          <DictSelect
            v-model="managementMode"
            class="filter-control--compact"
            category="management_mode"
            placeholder="管理模式"
            clearable
          />
          <AppRangeField
            v-model="signDateRange"
            class="filter-control--range-wide"
            start-placeholder="签约开始日期"
            end-placeholder="签约结束日期"
          />
          <template #actions>
            <div class="contract-query-panel__filter-tip">结果自动刷新，仅返回当前账号有权限查看的上游合同聚合信息。</div>
          </template>
        </AppFilterBar>
      </AppSectionCard>

      <AppSectionCard class="contract-query-panel__section contract-query-panel__section--results">
        <template #header>查询结果</template>
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
          description="调整关键字、分类或签约日期后会自动刷新。"
        />

        <div v-else-if="!isAssistant" class="contract-query-table-shell">
          <AppDataTable>
            <table class="contract-query-table">
              <thead>
                <tr>
                  <th>合同名称</th>
                  <th>甲方单位</th>
                  <th>乙方单位</th>
                  <th>合同类别</th>
                  <th>公司合同分类</th>
                  <th>管理模式</th>
                  <th>签约日期</th>
                  <th class="is-number">签约金额</th>
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
                  <td>{{ row.category || '-' }}</td>
                  <td>{{ row.company_category || '-' }}</td>
                  <td>{{ row.management_mode || '-' }}</td>
                  <td>{{ formatDate(row.sign_date) }}</td>
                  <td class="is-number">{{ formatMoney(row.contract_amount) }}</td>
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
                    <button
                      :data-testid="`drilldown-labor-total-${row.id}`"
                      type="button"
                      class="table-link"
                      :disabled="!row.zero_hour_labor_total"
                      @click="openRelatedList('labor', row)"
                    >
                      {{ formatMoney(row.zero_hour_labor_total) }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </AppDataTable>
        </div>

        <div v-else class="contract-query-panel__cards">
          <article v-for="row in rows" :key="row.id" class="contract-query-card">
            <header class="contract-query-card__header">
              <div class="contract-query-card__title-group">
                <button type="button" class="contract-query-card__title" @click="openUpstreamDetail(row)">
                  {{ row.contract_name }}
                </button>
                <div class="contract-query-card__meta">
                  <span>序号 {{ row.serial_number || '-' }}</span>
                  <span>{{ row.contract_code || '-' }}</span>
                </div>
              </div>
            </header>

            <section class="contract-query-card__section">
              <h3>合同概览</h3>
              <div class="contract-query-card__grid">
                <div class="contract-query-card__item">
                  <span>甲方单位</span>
                  <strong>{{ row.party_a_name || '-' }}</strong>
                </div>
                <div class="contract-query-card__item">
                  <span>合同类别</span>
                  <strong>{{ row.category || '-' }}</strong>
                </div>
                <div class="contract-query-card__item">
                  <span>公司合同分类</span>
                  <strong>{{ row.company_category || '-' }}</strong>
                </div>
                <div class="contract-query-card__item">
                  <span>管理模式</span>
                  <strong>{{ row.management_mode || '-' }}</strong>
                </div>
                <div class="contract-query-card__item">
                  <span>签订日期</span>
                  <strong>{{ formatDate(row.sign_date) }}</strong>
                </div>
                <div class="contract-query-card__item">
                  <span>完工日期</span>
                  <strong>{{ formatDate(row.completion_date) }}</strong>
                </div>
                <div class="contract-query-card__item">
                  <span>质保期到期日期</span>
                  <strong>{{ formatDate(row.warranty_date) }}</strong>
                </div>
              </div>
            </section>

            <section class="contract-query-card__section">
              <h3>上游金额</h3>
              <div class="contract-query-card__metric-grid">
                <div class="contract-query-card__metric">
                  <span>签约金额</span>
                  <strong>¥ {{ formatMoney(row.contract_amount) }}</strong>
                </div>
                <div class="contract-query-card__metric">
                  <span>应收款金额</span>
                  <strong>¥ {{ formatMoney(row.receivable_amount) }}</strong>
                </div>
                <div class="contract-query-card__metric">
                  <span>挂账金额</span>
                  <strong>¥ {{ formatMoney(row.invoiced_amount) }}</strong>
                </div>
                <div class="contract-query-card__metric">
                  <span>已收款金额</span>
                  <strong>¥ {{ formatMoney(row.received_amount) }}</strong>
                </div>
                <div class="contract-query-card__metric">
                  <span>结算金额</span>
                  <strong>¥ {{ formatMoney(row.settlement_amount) }}</strong>
                </div>
              </div>
            </section>

            <section class="contract-query-card__section">
              <h3>关联合同</h3>
              <div class="contract-query-card__association-grid">
                <button
                  :data-testid="`drilldown-downstream-count-${row.id}`"
                  type="button"
                  class="contract-query-card__association"
                  @click="openRelatedList('downstream', row)"
                >
                  <span>关联下游合同数量</span>
                  <strong>{{ row.downstream_contract_count || 0 }}</strong>
                </button>
                <button
                  type="button"
                  class="contract-query-card__association"
                  @click="openRelatedList('downstream', row)"
                >
                  <span>下游合同签约金额合计</span>
                  <strong>¥ {{ formatMoney(row.downstream_contract_amount) }}</strong>
                </button>
                <button
                  type="button"
                  class="contract-query-card__association"
                  @click="openRelatedList('downstream', row)"
                >
                  <span>下游合同已付款金额合计</span>
                  <strong>¥ {{ formatMoney(row.downstream_paid_amount) }}</strong>
                </button>
                <button
                  type="button"
                  class="contract-query-card__association"
                  @click="openRelatedList('downstream', row)"
                >
                  <span>下游合同结算金额合计</span>
                  <strong>¥ {{ formatMoney(row.downstream_settlement_amount) }}</strong>
                </button>
                <button
                  type="button"
                  class="contract-query-card__association"
                  @click="openRelatedList('management', row)"
                >
                  <span>关联管理合同数量</span>
                  <strong>{{ row.management_contract_count || 0 }}</strong>
                </button>
                <button
                  type="button"
                  class="contract-query-card__association"
                  @click="openRelatedList('management', row)"
                >
                  <span>管理合同签约金额合计</span>
                  <strong>¥ {{ formatMoney(row.management_contract_amount) }}</strong>
                </button>
                <button
                  type="button"
                  class="contract-query-card__association"
                  @click="openRelatedList('management', row)"
                >
                  <span>管理合同已付款金额合计</span>
                  <strong>¥ {{ formatMoney(row.management_paid_amount) }}</strong>
                </button>
                <button
                  type="button"
                  class="contract-query-card__association"
                  @click="openRelatedList('management', row)"
                >
                  <span>管理合同结算金额合计</span>
                  <strong>¥ {{ formatMoney(row.management_settlement_amount) }}</strong>
                </button>
              </div>
            </section>

            <section class="contract-query-card__section">
              <h3>费用汇总</h3>
              <div class="contract-query-card__metric-grid contract-query-card__metric-grid--expenses">
                <div class="contract-query-card__metric">
                  <span>无合同费用合计</span>
                  <button type="button" class="contract-query-card__metric-link" @click="openRelatedList('expense', row)">
                    ¥ {{ formatMoney(row.non_contract_expense_total) }}
                  </button>
                </div>
                <div class="contract-query-card__metric">
                  <span>关联零星用工总金额</span>
                  <button
                    :data-testid="`drilldown-labor-total-${row.id}`"
                    type="button"
                    class="contract-query-card__metric-link"
                    @click="openRelatedList('labor', row)"
                  >
                    ¥ {{ formatMoney(row.zero_hour_labor_total) }}
                  </button>
                </div>
              </div>
              <div v-if="row.expenses_by_category?.length" class="contract-query-card__expense-list">
                <div v-for="expense in row.expenses_by_category" :key="`${row.id}-${expense.category}`" class="contract-query-card__expense-chip">
                  <span>{{ expense.category }}</span>
                  <strong>¥ {{ formatMoney(expense.amount) }}</strong>
                </div>
              </div>
              <p v-else class="contract-query-card__empty-note">暂无按费用类别归集的无合同费用。</p>
            </section>
          </article>
        </div>

        <div class="contract-query-panel__pagination">
          <el-pagination
            :current-page="page"
            :page-size="pageSize"
            :page-sizes="[12, 24, 48]"
            layout="total, sizes, prev, pager, next"
            :total="total"
            @current-change="handlePageChange"
            @size-change="handlePageSizeChange"
          />
        </div>
      </AppSectionCard>
    </component>
  </div>
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
  variant: {
    type: String,
    default: 'page'
  }
})

const router = useRouter()

const keyword = ref('')
const contractCategory = ref('')
const companyCategory = ref('')
const managementMode = ref('')
const signDateRange = ref([])

const rows = shallowRef([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(12)
const loading = ref(false)
const exportLoading = ref(false)
const hasLoaded = ref(false)
const errorMessage = ref('')
let refreshTimer = null

const isAssistant = computed(() => props.variant === 'assistant')
const showExport = computed(() => !isAssistant.value)
const shellTag = computed(() => (isAssistant.value ? 'div' : AppWorkspacePanel))
const shellProps = computed(() => (
  isAssistant.value
    ? {}
    : { panelClass: 'contract-query-panel__workspace' }
))

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
    contractCategory: contractCategory.value || '',
    companyCategory: companyCategory.value || '',
    managementMode: managementMode.value || '',
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
  contractCategory.value = ''
  companyCategory.value = ''
  managementMode.value = ''
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

function openUpstreamDetail(row) {
  router.push({
    name: 'UpstreamDetail',
    params: { id: row.id },
    query: { tab: 'query' }
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
  if (target) router.push(target)
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
  () => [
    keyword.value,
    contractCategory.value,
    companyCategory.value,
    managementMode.value,
    ...(Array.isArray(signDateRange.value) ? signDateRange.value : [])
  ],
  () => {
    page.value = 1
    scheduleRefresh()
  }
)

onMounted(() => {
  loadRows()
})

onUnmounted(() => {
  clearRefreshTimer()
})
</script>

<style scoped lang="scss">
.contract-query-panel {
  min-width: 0;
}

.contract-query-panel__shell {
  display: grid;
  gap: var(--space-4);
}

.contract-query-panel__workspace,
.contract-query-panel__section {
  gap: 0;
}

.contract-query-panel__header-copy {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.contract-query-panel__eyebrow {
  font-size: 11px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: 0.12em;
  color: hsl(var(--muted-foreground));
  text-transform: uppercase;
}

.contract-query-panel__title-block {
  display: grid;
  gap: 6px;
}

.contract-query-panel__title {
  color: hsl(var(--foreground));
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.contract-query-panel__summary,
.contract-query-panel__filter-tip,
.contract-query-panel__stats,
.contract-query-card__empty-note {
  margin: 0;
  color: hsl(var(--muted-foreground));
  font-size: 13px;
  line-height: 1.6;
}

.contract-query-panel__stats {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
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
  min-width: 2160px;
  border-collapse: collapse;
  background: var(--surface-panel);
}

.contract-query-table th,
.contract-query-table td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--workspace-panel-border);
  vertical-align: top;
  text-align: left;
  font-size: 13px;
  line-height: 1.5;
  color: hsl(var(--foreground));
}

.contract-query-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: color-mix(in srgb, var(--surface-panel) 94%, var(--muted) 6%);
  color: hsl(var(--muted-foreground));
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.contract-query-table tbody tr:hover {
  background: color-mix(in srgb, var(--surface-panel) 76%, var(--brand-primary-soft) 24%);
}

.contract-query-table .is-number {
  text-align: right;
  white-space: nowrap;
}

.contract-query-table .is-wide {
  min-width: 240px;
}

.table-link {
  padding: 0;
  border: 0;
  background: transparent;
  color: hsl(var(--primary));
  font: inherit;
  cursor: pointer;
}

.table-link:hover:not(:disabled) {
  text-decoration: underline;
}

.table-link:disabled {
  color: hsl(var(--muted-foreground));
  cursor: default;
}

.table-link--primary {
  font-weight: 700;
}

.contract-query-panel__cards {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}

.contract-query-card {
  display: grid;
  gap: 18px;
  padding: 20px;
  border: 1px solid var(--workspace-panel-border);
  border-radius: calc(var(--radius-lg) + 2px);
  background: var(--surface-panel-elevated);
  box-shadow: var(--shadow-soft);
}

.contract-query-card__header,
.contract-query-card__title-group,
.contract-query-card__section {
  display: grid;
  gap: 12px;
}

.contract-query-card__title {
  padding: 0;
  border: 0;
  background: transparent;
  color: hsl(var(--foreground));
  font: inherit;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: -0.02em;
  text-align: left;
  cursor: pointer;
}

.contract-query-card__title:hover {
  color: hsl(var(--primary));
}

.contract-query-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.contract-query-card__meta span {
  padding: 4px 8px;
  border-radius: 999px;
  background: hsl(var(--muted));
  color: hsl(var(--muted-foreground));
  font-size: 12px;
  font-weight: 600;
}

.contract-query-card__section h3 {
  margin: 0;
  color: hsl(var(--foreground));
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.contract-query-card__grid,
.contract-query-card__metric-grid,
.contract-query-card__association-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.contract-query-card__item,
.contract-query-card__metric,
.contract-query-card__association {
  display: grid;
  gap: 6px;
  padding: 12px;
  border: 1px solid var(--workspace-panel-border);
  border-radius: var(--radius);
  background: color-mix(in srgb, var(--surface-panel) 82%, var(--muted) 18%);
  text-align: left;
}

.contract-query-card__item span,
.contract-query-card__metric span,
.contract-query-card__association span {
  color: hsl(var(--muted-foreground));
  font-size: 12px;
  line-height: 1.5;
}

.contract-query-card__item strong,
.contract-query-card__metric strong,
.contract-query-card__association strong,
.contract-query-card__metric-link {
  color: hsl(var(--foreground));
  font-size: 14px;
  font-weight: 700;
  line-height: 1.4;
}

.contract-query-card__association,
.contract-query-card__metric-link {
  cursor: pointer;
}

.contract-query-card__association:hover,
.contract-query-card__metric-link:hover {
  color: hsl(var(--primary));
}

.contract-query-card__association {
  border-color: hsl(var(--border));
  background: color-mix(in srgb, var(--surface-panel) 76%, var(--brand-primary-soft) 24%);
}

.contract-query-card__metric-link {
  padding: 0;
  border: 0;
  background: transparent;
  font: inherit;
  text-align: left;
}

.contract-query-card__expense-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.contract-query-card__expense-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--surface-panel) 68%, var(--muted) 32%);
  color: hsl(var(--foreground));
  font-size: 12px;
}

.contract-query-card__expense-chip strong {
  font-size: 12px;
}

.contract-query-panel__pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.contract-query-panel--assistant .contract-query-panel__section--results {
  min-height: 0;
}

.contract-query-panel--assistant .contract-query-panel__cards {
  grid-template-columns: 1fr;
}

@media (max-width: 900px) {
  .contract-query-card__grid,
  .contract-query-card__metric-grid,
  .contract-query-card__association-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .contract-query-panel__cards {
    grid-template-columns: 1fr;
  }

  .contract-query-card {
    padding: 16px;
  }

  .contract-query-panel__pagination {
    justify-content: stretch;
  }
}
</style>
