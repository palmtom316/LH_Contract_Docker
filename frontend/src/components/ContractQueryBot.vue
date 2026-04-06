<template>
  <!-- Floating Robot Button -->
  <div class="query-bot-container">
    <el-tooltip content="合同查询助手" placement="left">
      <button
        type="button"
        class="bot-button"
        :class="{ 'pulse': showPulse }"
        aria-label="打开合同查询助手"
        @click="openDialog"
      >
        <el-icon :size="28"><Search /></el-icon>
      </button>
    </el-tooltip>

    <!-- Query Dialog -->
    <el-dialog
      v-model="dialogVisible"
      title="合同查询助手"
      :width="dialogWidth"
      :close-on-click-modal="false"
      class="bot-dialog"
      append-to-body
      :fullscreen="isMobile"
    >
      <!-- Input Section -->
      <div class="input-section">
        <div class="input-row">
          <el-input
            v-model="searchQuery"
            placeholder="合同序号/名称/编号"
            size="large"
            clearable
            @keyup.enter="handleSearch"
            :prefix-icon="Search"
            class="search-input"
          />
          <DictSelect
            v-model="companyCategory"
            category="project_category"
            placeholder="公司合同分类"
            size="large"
            class="category-input"
          />
        </div>
        <div class="input-row">
          <el-input
            v-model="partyAName"
            placeholder="上游合同甲方单位"
            size="large"
            clearable
            @keyup.enter="handleSearch"
            class="party-a-input"
          />
          <el-input
            v-model="partyBName"
            placeholder="下游/管理合同乙方单位"
            size="large"
            clearable
            @keyup.enter="handleSearch"
            class="party-b-input"
          />
        </div>
        <div class="input-row">
          <AppRangeField
            v-model="signDateRange"
            start-placeholder="签约开始日期"
            end-placeholder="签约结束日期"
            class="sign-date-input"
          />
        </div>
        <p class="sign-date-tip">签约时间范围支持输入如 2026/04/06、26.4.6、2026-4-6。</p>
        <div class="action-row">
          <el-button type="primary" size="large" @click="handleSearch" :loading="loading" class="search-btn">
            <el-icon><Search /></el-icon> 查询
          </el-button>
          <el-button size="large" @click="handleClear" class="clear-btn">
            清除
          </el-button>
        </div>
      </div>

      <!-- Tip -->
      <div class="tip-section" v-if="!results.length && !loading && !hasSearched">
        <el-alert type="info" :closable="false">
          <template #title>
            <span class="tip-title">使用提示</span>
          </template>
          <p>您可以输入以下内容进行搜索：</p>
          <ul>
            <li>合同序号（如：1、2、10）</li>
            <li>合同名称的任意部分（如：装修、建设）</li>
            <li>合同编号的任意部分</li>
            <li><strong>公司合同分类</strong>（如：劳务合同、材料合同）</li>
            <li><strong>上游合同甲方单位</strong>（如：某某电力公司）</li>
            <li><strong>下游/管理合同乙方单位</strong>（如：某某供应商）</li>
            <li><strong>签约时间范围</strong>（开始/结束日期，支持 2026/04/06、26.4.6、2026-4-6）</li>
          </ul>
          <p>可同时输入多个条件进行组合查询。</p>
        </el-alert>
      </div>

      <!-- Loading -->
      <div class="loading-section" v-if="loading">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- No Results -->
      <div class="no-results" v-if="hasSearched && !loading && !hasAnyResults">
        <el-empty description="未找到匹配的合同，请尝试其他关键词" />
      </div>

      <!-- Results Section -->
      <div class="results-section" v-if="!loading && hasAnyResults">
        <div class="results-count">
          <el-tag type="success">找到 {{ resultCount }} 个{{ resultLabel }}</el-tag>
        </div>

        <el-collapse v-if="showUpstreamResults" v-model="activeNames" accordion>
          <el-collapse-item 
            v-for="(contract, index) in results" 
            :key="contract.id" 
            :name="index"
          >
            <template #title>
              <div class="contract-header">
                <span class="contract-serial">#{{ contract.serial_number || contract.id }}</span>
                <span class="contract-name">{{ contract.contract_name }}</span>
                <el-tag size="small" :type="getStatusType(contract.status)">{{ contract.status || '未知' }}</el-tag>
              </div>
            </template>

            <!-- Contract Details -->
            <div class="contract-details">
              <!-- Upstream Contract Info -->
              <div class="section upstream-section">
                <div class="section-header">
                  <el-icon><Document /></el-icon>
                  <span>上游合同信息</span>
                </div>
                <el-descriptions :column="isMobile ? 1 : 2" border size="small">
                  <el-descriptions-item label="合同序号">{{ contract.serial_number || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="合同编号">{{ contract.contract_code }}</el-descriptions-item>
                  <el-descriptions-item label="合同名称" :span="isMobile ? 1 : 2">{{ contract.contract_name }}</el-descriptions-item>
                  <el-descriptions-item label="公司合同分类">{{ contract.company_category || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="甲方">{{ contract.party_a_name }}</el-descriptions-item>
                  <el-descriptions-item label="乙方">{{ contract.party_b_name }}</el-descriptions-item>
                </el-descriptions>
                <div class="finance-cards">
                  <div class="finance-card blue-card">
                    <span class="label">签约金额</span>
                    <span class="value">{{ formatMoney(contract.finance.contract_amount) }}</span>
                  </div>
                  <div class="finance-card orange-card">
                    <span class="label">应收款</span>
                    <span class="value">{{ formatMoney(contract.finance.payable_amount) }}</span>
                  </div>
                  <div class="finance-card purple-card">
                    <span class="label">挂账金额</span>
                    <span class="value">{{ formatMoney(contract.finance.invoiced_amount) }}</span>
                  </div>
                  <div class="finance-card green-card">
                    <span class="label">已收款</span>
                    <span class="value">{{ formatMoney(contract.finance.paid_amount) }}</span>
                  </div>
                </div>
              </div>

              <!-- Downstream Contracts -->
              <div class="section" v-if="contract.downstream_contracts.length">
                <div class="section-header">
                  <el-icon><DocumentCopy /></el-icon>
                  <span>关联下游合同 ({{ contract.downstream_contracts.length }})</span>
                </div>
                <el-table :data="contract.downstream_contracts" border size="small" class="compact-table">
                  <el-table-column prop="serial_number" label="序号" width="70" />
                  <el-table-column prop="contract_name" label="合同名称" min-width="180" show-overflow-tooltip />
                  <el-table-column label="签约金额" width="110" align="right">
                    <template #default="{ row }">{{ formatMoney(row.finance.contract_amount) }}</template>
                  </el-table-column>
                  <el-table-column label="应付款" width="110" align="right">
                    <template #default="{ row }">{{ formatMoney(row.finance.payable_amount) }}</template>
                  </el-table-column>
                  <el-table-column label="挂账金额" width="110" align="right">
                    <template #default="{ row }">{{ formatMoney(row.finance.invoiced_amount) }}</template>
                  </el-table-column>
                  <el-table-column label="已付款" width="110" align="right">
                    <template #default="{ row }">{{ formatMoney(row.finance.paid_amount) }}</template>
                  </el-table-column>
                </el-table>
                <!-- Summary Row -->
                <div class="summary-row">
                  <span class="label">合计：</span>
                  <span class="item">签约 <strong>{{ formatMoney(sumField(contract.downstream_contracts, 'contract_amount')) }}</strong></span>
                  <span class="item">应付 <strong>{{ formatMoney(sumField(contract.downstream_contracts, 'payable_amount')) }}</strong></span>
                  <span class="item">挂账 <strong>{{ formatMoney(sumField(contract.downstream_contracts, 'invoiced_amount')) }}</strong></span>
                  <span class="item">已付 <strong>{{ formatMoney(sumField(contract.downstream_contracts, 'paid_amount')) }}</strong></span>
                </div>
              </div>

              <!-- Management Contracts -->
              <div class="section" v-if="contract.management_contracts.length">
                <div class="section-header">
                  <el-icon><FolderChecked /></el-icon>
                  <span>关联管理合同 ({{ contract.management_contracts.length }})</span>
                </div>
                <el-table :data="contract.management_contracts" border size="small" class="compact-table">
                  <el-table-column prop="serial_number" label="序号" width="70" />
                  <el-table-column prop="contract_name" label="合同名称" min-width="180" show-overflow-tooltip />
                  <el-table-column label="签约金额" width="110" align="right">
                    <template #default="{ row }">{{ formatMoney(row.finance.contract_amount) }}</template>
                  </el-table-column>
                  <el-table-column label="应付款" width="110" align="right">
                    <template #default="{ row }">{{ formatMoney(row.finance.payable_amount) }}</template>
                  </el-table-column>
                  <el-table-column label="挂账金额" width="110" align="right">
                    <template #default="{ row }">{{ formatMoney(row.finance.invoiced_amount) }}</template>
                  </el-table-column>
                  <el-table-column label="已付款" width="110" align="right">
                    <template #default="{ row }">{{ formatMoney(row.finance.paid_amount) }}</template>
                  </el-table-column>
                </el-table>
                <!-- Summary Row -->
                <div class="summary-row">
                  <span class="label">合计：</span>
                  <span class="item">签约 <strong>{{ formatMoney(sumField(contract.management_contracts, 'contract_amount')) }}</strong></span>
                  <span class="item">应付 <strong>{{ formatMoney(sumField(contract.management_contracts, 'payable_amount')) }}</strong></span>
                  <span class="item">挂账 <strong>{{ formatMoney(sumField(contract.management_contracts, 'invoiced_amount')) }}</strong></span>
                  <span class="item">已付 <strong>{{ formatMoney(sumField(contract.management_contracts, 'paid_amount')) }}</strong></span>
                </div>
              </div>

              <!-- Expenses by Category -->
              <div class="section" v-if="contract.expenses_by_category.length">
                <div class="section-header">
                  <el-icon><Money /></el-icon>
                  <span>无合同费用（各类别已付款）</span>
                </div>
                <div class="expense-grid">
                  <div 
                    class="expense-item" 
                    v-for="exp in contract.expenses_by_category" 
                    :key="exp.category"
                  >
                    <span class="category">{{ exp.category }}</span>
                    <span class="amount">{{ formatMoney(exp.amount) }}</span>
                  </div>
                </div>
                <div class="expense-total">
                  <span>无合同费用合计：</span>
                  <strong>{{ formatMoney(sumExpenses(contract.expenses_by_category)) }}</strong>
                </div>
              </div>

              <!-- Empty States -->
              <div class="section empty" v-if="!contract.downstream_contracts.length && !contract.management_contracts.length && !contract.expenses_by_category.length">
                <el-empty description="该合同暂无关联的下游合同、管理合同或无合同费用" :image-size="80" />
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>

        <!-- Downstream / Management Results -->
        <div v-else>
          <div class="section" v-if="downstreamResults.length">
            <div class="section-header">
              <el-icon><DocumentCopy /></el-icon>
              <span>下游合同 ({{ downstreamResults.length }})</span>
            </div>
            <el-table :data="downstreamResults" border size="small" class="compact-table">
              <el-table-column prop="serial_number" label="序号" width="70" />
              <el-table-column prop="contract_name" label="合同名称" min-width="180" show-overflow-tooltip />
              <el-table-column prop="contract_code" label="合同编号" min-width="140" show-overflow-tooltip />
              <el-table-column prop="party_b_name" label="乙方单位" min-width="160" show-overflow-tooltip />
              <el-table-column label="签约金额" width="110" align="right">
                <template #default="{ row }">{{ formatMoney(row.finance.contract_amount) }}</template>
              </el-table-column>
              <el-table-column label="应付款" width="110" align="right">
                <template #default="{ row }">{{ formatMoney(row.finance.payable_amount) }}</template>
              </el-table-column>
              <el-table-column label="挂账金额" width="110" align="right">
                <template #default="{ row }">{{ formatMoney(row.finance.invoiced_amount) }}</template>
              </el-table-column>
              <el-table-column label="已付款" width="110" align="right">
                <template #default="{ row }">{{ formatMoney(row.finance.paid_amount) }}</template>
              </el-table-column>
            </el-table>
          </div>

          <div class="section" v-if="managementResults.length">
            <div class="section-header">
              <el-icon><FolderChecked /></el-icon>
              <span>管理合同 ({{ managementResults.length }})</span>
            </div>
            <el-table :data="managementResults" border size="small" class="compact-table">
              <el-table-column prop="serial_number" label="序号" width="70" />
              <el-table-column prop="contract_name" label="合同名称" min-width="180" show-overflow-tooltip />
              <el-table-column prop="contract_code" label="合同编号" min-width="140" show-overflow-tooltip />
              <el-table-column prop="party_b_name" label="乙方单位" min-width="160" show-overflow-tooltip />
              <el-table-column label="签约金额" width="110" align="right">
                <template #default="{ row }">{{ formatMoney(row.finance.contract_amount) }}</template>
              </el-table-column>
              <el-table-column label="应付款" width="110" align="right">
                <template #default="{ row }">{{ formatMoney(row.finance.payable_amount) }}</template>
              </el-table-column>
              <el-table-column label="挂账金额" width="110" align="right">
                <template #default="{ row }">{{ formatMoney(row.finance.invoiced_amount) }}</template>
              </el-table-column>
              <el-table-column label="已付款" width="110" align="right">
                <template #default="{ row }">{{ formatMoney(row.finance.paid_amount) }}</template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- Overall Summary -->
        <div class="summary-section" v-if="hasSummary">
          <div class="summary-title">金额汇总</div>
          <div class="summary-list">
            <div class="summary-card" v-if="summary.party_a">
              <div class="summary-header">
                <span class="summary-label">甲方单位汇总</span>
                <span class="summary-keyword" v-if="hasPartyAFilter">关键词：{{ summary.party_a.party_name }}</span>
                <span class="summary-keyword" v-else>范围：{{ summary.party_a.party_name }}</span>
                <span class="summary-count">合同数：{{ summary.party_a.contract_count }}</span>
              </div>
              <div class="summary-metrics">
                <div class="summary-metric">
                  <span class="metric-label">签约金额</span>
                  <span class="metric-value">{{ formatMoney(summary.party_a.finance.contract_amount) }}</span>
                </div>
                <div class="summary-metric">
                  <span class="metric-label">应收款</span>
                  <span class="metric-value">{{ formatMoney(summary.party_a.finance.payable_amount) }}</span>
                </div>
                <div class="summary-metric">
                  <span class="metric-label">挂账金额</span>
                  <span class="metric-value">{{ formatMoney(summary.party_a.finance.invoiced_amount) }}</span>
                </div>
                <div class="summary-metric">
                  <span class="metric-label">已收款</span>
                  <span class="metric-value">{{ formatMoney(summary.party_a.finance.paid_amount) }}</span>
                </div>
              </div>
            </div>
            <div class="summary-card" v-if="summary.party_b">
              <div class="summary-header">
                <span class="summary-label">乙方单位汇总</span>
                <span class="summary-keyword" v-if="hasPartyBFilter">关键词：{{ summary.party_b.party_name }}</span>
                <span class="summary-keyword" v-else>范围：{{ summary.party_b.party_name }}</span>
                <span class="summary-count">合同数：{{ summary.party_b.contract_count }}</span>
              </div>
              <div class="summary-metrics">
                <div class="summary-metric">
                  <span class="metric-label">签约金额</span>
                  <span class="metric-value">{{ formatMoney(summary.party_b.finance.contract_amount) }}</span>
                </div>
                <div class="summary-metric">
                  <span class="metric-label">应付款</span>
                  <span class="metric-value">{{ formatMoney(summary.party_b.finance.payable_amount) }}</span>
                </div>
                <div class="summary-metric">
                  <span class="metric-label">挂账金额</span>
                  <span class="metric-value">{{ formatMoney(summary.party_b.finance.invoiced_amount) }}</span>
                </div>
                <div class="summary-metric">
                  <span class="metric-label">已付款</span>
                  <span class="metric-value">{{ formatMoney(summary.party_b.finance.paid_amount) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, shallowRef, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Document, DocumentCopy, FolderChecked, Money } from '@element-plus/icons-vue'
import { searchContracts } from '@/api/contractSearch'
import DictSelect from '@/components/DictSelect.vue'
import AppRangeField from '@/components/ui/AppRangeField.vue'

// State
const dialogVisible = ref(false)
const searchQuery = ref('')
const companyCategory = ref('')  // 公司合同分类
const partyAName = ref('') // 上游合同甲方单位
const partyBName = ref('') // 下游/管理合同乙方单位
const signDateRange = ref([])
const loading = ref(false)
const hasSearched = ref(false)
const results = shallowRef([])
const downstreamResults = shallowRef([])
const managementResults = shallowRef([])
const summary = ref(null)
const activeNames = ref([0])
const showPulse = ref(true)
const windowWidth = ref(window.innerWidth)

// Computed
const isMobile = computed(() => windowWidth.value < 768)
const dialogWidth = computed(() => isMobile.value ? '100%' : '900px')
const hasSummary = computed(() => summary.value && (summary.value.party_a || summary.value.party_b))
const hasPartyAFilter = computed(() => !!partyAName.value.trim())
const hasPartyBFilter = computed(() => !!partyBName.value.trim())
const showUpstreamResults = computed(() => !hasPartyBFilter.value)
const resultCount = computed(() => {
  if (showUpstreamResults.value) return results.value.length
  return downstreamResults.value.length + managementResults.value.length
})
const resultLabel = computed(() => (showUpstreamResults.value ? '上游合同' : '下游/管理合同'))
const hasAnyResults = computed(() => {
  return results.value.length > 0 || downstreamResults.value.length > 0 || managementResults.value.length > 0
})

// Handle window resize
const handleResize = () => {
  windowWidth.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

// Methods
const openDialog = () => {
  dialogVisible.value = true
  showPulse.value = false  // Stop pulsing after first click
}

const handleSearch = async () => {
  const query = searchQuery.value.trim()
  const category = companyCategory.value.trim()
  const partyA = partyAName.value.trim()
  const partyB = partyBName.value.trim()
  const hasDateRange = Array.isArray(signDateRange.value) && signDateRange.value.length === 2
  const signDateStart = hasDateRange ? signDateRange.value[0] : ''
  const signDateEnd = hasDateRange ? signDateRange.value[1] : ''

  if (!query && !category && !partyA && !partyB && !hasDateRange) {
    ElMessage.warning('请至少输入一个搜索条件')
    return
  }

  loading.value = true
  hasSearched.value = true
  results.value = []
  downstreamResults.value = []
  managementResults.value = []
  summary.value = null

  try {
    const response = await searchContracts({
      query: query,
      companyCategory: category,
      partyAName: partyA,
      partyBName: partyB,
      signDateStart,
      signDateEnd
    })
    results.value = response.results || []
    downstreamResults.value = response.downstream_results || []
    managementResults.value = response.management_results || []
    summary.value = response.summary || null
    
    if (results.value.length === 0 && downstreamResults.value.length === 0 && managementResults.value.length === 0) {
      ElMessage.info('未找到匹配的合同')
    } else {
      activeNames.value = [0]  // Expand first result
    }
  } catch (error) {
    console.error('Search error:', error)
    ElMessage.error('查询失败：' + (error.response?.data?.detail || error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

const handleClear = () => {
  searchQuery.value = ''
  companyCategory.value = ''
  partyAName.value = ''
  partyBName.value = ''
  signDateRange.value = []
  results.value = []
  downstreamResults.value = []
  managementResults.value = []
  summary.value = null
  hasSearched.value = false
  loading.value = false
  activeNames.value = [0]
}

const formatMoney = (value) => {
  if (value == null || isNaN(value)) return '¥0.00'
  return '¥' + Number(value).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const getStatusType = (status) => {
  const map = {
    '执行中': 'primary',
    '已完成': 'success',
    '已终止': 'danger',
    '已结算': 'success'
  }
  return map[status] || 'info'
}

const sumField = (contracts, field) => {
  return contracts.reduce((sum, c) => sum + (c.finance?.[field] || 0), 0)
}

const sumExpenses = (expenses) => {
  return expenses.reduce((sum, e) => sum + (e.amount || 0), 0)
}
</script>

<style scoped lang="scss">
.query-bot-container {
  position: fixed;
  right: 24px;
  bottom: 80px;
  z-index: 2000;
}

.bot-button {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--brand-primary);
  color: var(--text-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(22, 73, 106, 0.24);
  transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.3);

  &:hover {
    transform: translateY(-1px);
    background: var(--brand-primary-strong);
    box-shadow: 0 10px 24px rgba(22, 73, 106, 0.28);
  }

  &.pulse {
    animation: pulse 2.4s infinite;
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 8px 20px rgba(22, 73, 106, 0.22);
  }
  50% {
    box-shadow: 0 8px 28px rgba(22, 73, 106, 0.34);
  }
  100% {
    box-shadow: 0 8px 20px rgba(22, 73, 106, 0.22);
  }
}

.input-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;

  .input-row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;

    .search-input {
      flex: 2;
      min-width: 150px;
    }

    .category-input {
      flex: 1;
      min-width: 120px;
    }

    .party-a-input,
    .party-b-input {
      flex: 1;
      min-width: 160px;
    }

    .sign-date-input {
      flex: 1;
      min-width: 280px;
    }
  }

  .sign-date-tip {
    margin: 0;
    font-size: 12px;
    color: var(--text-secondary);
  }

  .search-btn {
    align-self: flex-start;
  }

  .action-row {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .clear-btn {
    align-self: flex-start;
  }

  @media (max-width: 768px) {
    .input-row {
      flex-direction: column;

      .search-input, .category-input, .party-a-input, .party-b-input, .sign-date-input {
        width: 100%;
        flex: none;
      }
    }

    .action-row {
      flex-direction: column;
      align-items: stretch;
    }

    .search-btn,
    .clear-btn {
      width: 100%;
    }
  }
}

.tip-section {
  .tip-title {
    font-weight: 500;
  }

  ul {
    margin: 8px 0;
    padding-left: 20px;

    li {
      margin: 4px 0;
    }
  }
}

.loading-section, .no-results {
  padding: 40px 0;
}

.results-section {
  .results-count {
    margin-bottom: 12px;
  }
}

.contract-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;

  .contract-serial {
    font-weight: 600;
    color: var(--brand-primary);
    min-width: 40px;
  }

  .contract-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.contract-details {
  .section {
    margin-bottom: 20px;
    padding: 12px;
    background: var(--surface-panel-muted);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;

    &.upstream-section {
      background: #f2f6f9;
    }

    &.empty {
      background: var(--surface-panel);
    }
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border-subtle);
  }
}

.finance-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 12px;

  .finance-card {
    padding: 16px 12px;
    border-radius: 10px;
    text-align: center;
    border: 1px solid var(--border-subtle);
    box-shadow: none;
    transition: transform 0.2s, border-color 0.2s;

    &:hover {
      transform: translateY(-2px);
      border-color: var(--border-strong);
    }

    .label {
      display: block;
      font-size: 13px;
      color: var(--text-secondary);
      margin-bottom: 8px;
    }

    .value {
      font-size: 18px;
      font-weight: bold;
      color: var(--text-primary);
    }
    
    &.blue-card {
      background: #edf4f8;
    }
    
    &.orange-card {
      background: #faf3e2;
    }

    &.purple-card {
      background: #f1eef7;
    }
    
    &.green-card {
      background: #edf5f0;
    }
  }
}

.compact-table {
  margin-bottom: 8px;
}

.summary-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 12px;
  background: #fff;
  border-radius: 4px;
  font-size: 13px;

  .label {
    color: #8c8c8c;
  }

  .item {
    color: #595959;

    strong {
      color: var(--brand-primary);
      margin-left: 4px;
    }
  }
}

.summary-section {
  margin-top: 20px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;

  .summary-title {
    font-weight: 600;
    color: #262626;
    margin-bottom: 10px;
  }

  .summary-list {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 12px;
  }

  .summary-card {
    background: #fff;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    padding: 12px;
  }

  .summary-header {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 10px;

    .summary-label {
      font-weight: 600;
      color: #262626;
    }

    .summary-keyword {
      color: #8c8c8c;
      font-size: 12px;
    }

    .summary-count {
      color: #595959;
      font-size: 12px;
    }
  }

  .summary-metrics {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .summary-metric {
    background: #f5f5f5;
    border-radius: 6px;
    padding: 8px 10px;

    .metric-label {
      display: block;
      font-size: 12px;
      color: #8c8c8c;
    }

    .metric-value {
      display: block;
      margin-top: 4px;
      font-weight: 600;
      color: var(--brand-primary);
    }
  }
}

.expense-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 8px;
  margin-bottom: 12px;

  .expense-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 12px;
    background: #fff;
    border-radius: 6px;
    border-left: 3px solid var(--brand-primary);

    .category {
      color: #595959;
      font-size: 13px;
    }

    .amount {
      font-weight: 600;
      color: var(--brand-accent);
    }
  }
}

.expense-total {
  text-align: right;
  padding: 8px 12px;
  background: #fff;
  border-radius: 4px;
  font-size: 14px;

  strong {
    color: var(--brand-accent);
    font-size: 16px;
    margin-left: 8px;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .query-bot-container {
    right: 16px;
    bottom: 60px;
  }

  .bot-button {
    width: 48px;
    height: 48px;
  }

  .finance-cards {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;

    .finance-card {
      padding: 8px;

      .value {
        font-size: 14px;
      }
    }
  }

  .expense-grid {
    grid-template-columns: 1fr;
  }

  .summary-row {
    flex-wrap: wrap;
    gap: 6px;
    font-size: 12px;
  }

  .contract-header {
    gap: 8px;

    .contract-name {
      font-size: 14px;
    }
  }

  .compact-table {
    font-size: 12px;
  }
}

/* Force HMR update 2024-12-29 */
</style>

<style lang="scss">
/* Global styles for Dialog (append-to-body) */
.bot-dialog {
  .el-dialog__header {
    background: var(--brand-primary);
    color: var(--text-inverse);
    padding: 16px 20px;
    margin: 0;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;

    .el-dialog__title {
      color: var(--text-inverse);
      font-size: 18px;
      font-weight: 600;
    }

    .el-dialog__close {
      color: var(--text-inverse);
      &:hover {
        color: rgba(255,255,255,0.8);
      }
    }
  }

  .el-dialog__body {
    padding: 20px;
    max-height: 70vh;
    overflow-y: auto;
  }
  
  @media (max-width: 768px) {
    .el-dialog {
      width: 100% !important;
      max-width: 100% !important;
      margin: 0 !important;
      border-radius: 0;
    }

    .el-dialog__header {
      padding: 12px 16px;
      border-radius: 0;
    }

    .el-dialog__body {
      padding: 12px;
      max-height: calc(100vh - 60px);
    }
  }
}
</style>
