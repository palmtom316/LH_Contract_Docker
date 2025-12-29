<template>
  <!-- Floating Robot Button -->
  <div class="query-bot-container">
    <el-tooltip content="合同查询助手" placement="left">
      <div class="bot-button" @click="openDialog" :class="{ 'pulse': showPulse }">
        <el-icon :size="28"><Search /></el-icon>
      </div>
    </el-tooltip>

    <!-- Query Dialog -->
    <el-dialog
      v-model="dialogVisible"
      title="🤖 合同查询助手"
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
          <el-input
            v-model="companyCategory"
            placeholder="公司合同分类"
            size="large"
            clearable
            @keyup.enter="handleSearch"
            class="category-input"
          />
        </div>
        <el-button type="primary" size="large" @click="handleSearch" :loading="loading" class="search-btn">
          <el-icon><Search /></el-icon> 查询
        </el-button>
      </div>

      <!-- Tip -->
      <div class="tip-section" v-if="!results.length && !loading && !hasSearched">
        <el-alert type="info" :closable="false">
          <template #title>
            <span class="tip-title">💡 使用提示</span>
          </template>
          <p>您可以输入以下内容进行搜索：</p>
          <ul>
            <li>合同序号（如：1、2、10）</li>
            <li>合同名称的任意部分（如：装修、建设）</li>
            <li>合同编号的任意部分</li>
            <li><strong>公司合同分类</strong>（如：劳务合同、材料合同）</li>
          </ul>
          <p>可同时输入多个条件进行组合查询。</p>
        </el-alert>
      </div>

      <!-- Loading -->
      <div class="loading-section" v-if="loading">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- No Results -->
      <div class="no-results" v-if="hasSearched && !loading && !results.length">
        <el-empty description="未找到匹配的合同，请尝试其他关键词" />
      </div>

      <!-- Results Section -->
      <div class="results-section" v-if="!loading && results.length">
        <div class="results-count">
          <el-tag type="success">找到 {{ results.length }} 个上游合同</el-tag>
        </div>

        <el-collapse v-model="activeNames" accordion>
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
                  <div class="finance-card">
                    <span class="label">签约金额</span>
                    <span class="value primary">{{ formatMoney(contract.finance.contract_amount) }}</span>
                  </div>
                  <div class="finance-card">
                    <span class="label">应收款</span>
                    <span class="value warning">{{ formatMoney(contract.finance.payable_amount) }}</span>
                  </div>
                  <div class="finance-card">
                    <span class="label">挂账金额</span>
                    <span class="value info">{{ formatMoney(contract.finance.invoiced_amount) }}</span>
                  </div>
                  <div class="finance-card">
                    <span class="label">已收款</span>
                    <span class="value success">{{ formatMoney(contract.finance.paid_amount) }}</span>
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
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, shallowRef, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Document, DocumentCopy, FolderChecked, Money } from '@element-plus/icons-vue'
import { searchContracts } from '@/api/contractSearch'

// State
const dialogVisible = ref(false)
const searchQuery = ref('')
const companyCategory = ref('')  // 公司合同分类
const loading = ref(false)
const hasSearched = ref(false)
const results = shallowRef([])
const activeNames = ref([0])
const showPulse = ref(true)
const windowWidth = ref(window.innerWidth)

// Computed
const isMobile = computed(() => windowWidth.value < 768)
const dialogWidth = computed(() => isMobile.value ? '100%' : '900px')

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
  
  if (!query && !category) {
    ElMessage.warning('请至少输入一个搜索条件')
    return
  }

  loading.value = true
  hasSearched.value = true
  results.value = []

  try {
    const response = await searchContracts({
      query: query,
      companyCategory: category,
      limit: 20
    })
    results.value = response.results || []
    
    if (results.value.length === 0) {
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
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.4);
  transition: all 0.3s ease;

  &:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 24px rgba(24, 144, 255, 0.5);
  }

  &.pulse {
    animation: pulse 2s infinite;
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 4px 16px rgba(24, 144, 255, 0.4);
  }
  50% {
    box-shadow: 0 4px 24px rgba(24, 144, 255, 0.8);
  }
  100% {
    box-shadow: 0 4px 16px rgba(24, 144, 255, 0.4);
  }
}

:deep(.bot-dialog) {
  .el-dialog__header {
    background: linear-gradient(135deg, #1890ff, #096dd9);
    color: #fff;
    padding: 16px 20px;
    margin: 0;

    .el-dialog__title {
      color: #fff;
      font-size: 18px;
      font-weight: 500;
    }

    .el-dialog__close {
      color: #fff;
    }
  }

  .el-dialog__body {
    padding: 20px;
    max-height: 70vh;
    overflow-y: auto;
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
  }

  .search-btn {
    align-self: flex-start;
  }

  @media (max-width: 768px) {
    .input-row {
      flex-direction: column;

      .search-input, .category-input {
        width: 100%;
        flex: none;
      }
    }

    .search-btn {
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
    color: #1890ff;
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
    background: #fafafa;
    border-radius: 8px;

    &.upstream-section {
      background: linear-gradient(135deg, #e6f7ff, #f0f5ff);
    }

    &.empty {
      background: #fff;
    }
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
    color: #262626;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e8e8e8;
  }
}

.finance-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 12px;

  .finance-card {
    background: #fff;
    padding: 12px;
    border-radius: 6px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);

    .label {
      display: block;
      font-size: 12px;
      color: #8c8c8c;
      margin-bottom: 4px;
    }

    .value {
      font-size: 16px;
      font-weight: 600;

      &.primary { color: #1890ff; }
      &.warning { color: #faad14; }
      &.info { color: #722ed1; }
      &.success { color: #52c41a; }
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
      color: #1890ff;
      margin-left: 4px;
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
    border-left: 3px solid #1890ff;

    .category {
      color: #595959;
      font-size: 13px;
    }

    .amount {
      font-weight: 600;
      color: #fa541c;
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
    color: #fa541c;
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

  :deep(.bot-dialog) {
    .el-dialog {
      width: 100% !important;
      max-width: 100% !important;
      margin: 0 !important;
      border-radius: 0;
    }

    .el-dialog__header {
      padding: 12px 16px;
    }

    .el-dialog__body {
      padding: 12px;
      max-height: calc(100vh - 60px);
    }
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


