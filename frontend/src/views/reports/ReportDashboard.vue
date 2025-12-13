<!-- Report Dashboard Module -->
<template>
  <div class="app-container" v-loading="loading">
    <!-- Header / Filter -->
    <div class="filter-container">
      <span class="filter-label">统计周期:</span>
      
      <!-- Year Picker -->
      <el-date-picker
        v-model="currentYear"
        type="year"
        placeholder="选择年份"
        style="width: 120px; margin-right: 10px;"
        value-format="YYYY"
        @change="handleFilterChange"
      />
      
      <!-- Month Selector -->
      <el-select 
        v-model="currentMonth" 
        placeholder="选择月份 (默认全年)" 
        clearable 
        style="width: 180px; margin-right: 10px;"
        @change="handleFilterChange"
      >
        <el-option label="全年数据" :value="null" />
        <el-option v-for="m in 12" :key="m" :label="m + '月'" :value="m" />
      </el-select>

      <el-button type="primary" icon="Refresh" @click="fetchData">查询</el-button>
    </div>

    <!-- Row 1: Annual Summary Cards (4 Cards) -->
    <el-row :gutter="20" class="summary-row">
      <!-- 1. Annual Upstream Contract Total -->
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card border-left-primary" style="height: 160px;">
          <div class="card-content">
            <div class="card-title">年度上游合同签约总金额</div>
            <div class="card-amount text-primary">
              {{ annualUpstreamCount }} 单
            </div>
            <div class="card-sub">
              <span class="text-primary">¥ {{ formatWan(annualUpstreamAmount) }} 万元</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 2. Annual Receipts Total -->
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card border-left-success" style="height: 160px;">
          <div class="card-content">
            <div class="card-title">年度回款总金额</div>
            <div class="card-amount text-success">
              ¥ {{ formatWan(annualReceiptsAmount) }} 万元
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 3. Annual Payments Total -->
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card border-left-warning" style="height: 160px;">
          <div class="card-content">
            <div class="card-title">年度付款总金额</div>
            <div class="card-amount text-warning">
              ¥ {{ formatWan(annualPaymentsAmount) }} 万元
            </div>
            <div class="card-sub" style="font-size: 11px;">
              <span class="text-info">下游+管理+无合同费用</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 4. Annual Downstream & Management Contract Total -->
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card border-left-info" style="height: 160px;">
          <div class="card-content">
            <div class="card-title">年度下游及管理合同签约总金额</div>
            <div class="card-amount text-info">
              {{ annualDownMgmtCount }} 单
            </div>
            <div class="card-sub">
              <span class="text-info">¥ {{ formatWan(annualDownMgmtAmount) }} 万元</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 2: Trend Chart (Wide) + AR + AP -->
    <el-row :gutter="20" style="margin-top: 20px;" class="summary-row">
      <!-- Trend Chart (Takes 12 columns = 2 cards width) -->
      <el-col :xs="24" :sm="24" :md="12">
        <el-card shadow="hover" class="stat-card" style="height: 228px; display: flex; flex-direction: column;" :body-style="{ flex: '1', overflow: 'hidden', padding: '10px', display: 'flex', flexDirection: 'column' }">
          <div class="card-content" style="flex: 1; display: flex; flex-direction: column; overflow: hidden;">
            <div class="card-title" style="margin-bottom: 5px; flex-shrink: 0;">
              {{ currentYear }}年度 收支趋势
              <el-tag v-if="currentMonth" type="warning" size="small" style="margin-left: 10px; transform: scale(0.8);">
                {{ currentMonth }}月
              </el-tag>
            </div>
            <!-- Chart Container -->
            <div ref="trendChartRef" style="width: 100%; flex: 1; min-height: 0;"></div>
          </div>
        </el-card>
      </el-col>

      <!-- Receivables -->
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card border-left-success" style="height: 228px;">
          <div class="card-content">
            <div class="card-title">
              {{ currentMonth ? `${currentMonth}月 ` : '' }}应收账款 (AR)
              <el-tooltip content="统计周期内应收款 vs 已收款" placement="top">
                 <el-icon><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
            <div class="card-amount text-primary">¥ {{ formatWan(arStats.outstanding) }} 万元</div>
            <div class="card-sub">
              <span class="text-primary">应收款: ¥ {{ formatWan(arStats.total_receivable) }} 万元</span>
              <br>
              <span class="text-success">已收款: ¥ {{ formatWan(arStats.total_received) }} 万元</span>
            </div>
            <el-progress 
              :percentage="calcPercentage(arStats.total_received, arStats.total_receivable)" 
              status="success"
              :stroke-width="10"
              class="ar-progress"
            >
              <template #default="{ percentage }">
                <span style="font-size: 12px; color: #606266;">{{ percentage }}%</span>
              </template>
            </el-progress>
          </div>
        </el-card>
      </el-col>
      
      <!-- Payables -->
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card border-left-warning" style="height: 228px;">
          <div class="card-content">
            <div class="card-title">
              {{ currentMonth ? `${currentMonth}月 ` : '' }}应付账款 (AP)
              <el-tooltip content="统计周期内应付款 vs 已付款" placement="top">
                 <el-icon><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
            <div class="card-amount text-warning">¥ {{ formatWan(apStats.outstanding) }} 万元</div>
            <div class="card-sub">
              <span class="text-primary">应付款: ¥ {{ formatWan(apStats.total_payable) }} 万元</span>
              <br>
              <span class="text-success">已付款: ¥ {{ formatWan(apStats.total_paid) }} 万元</span>
            </div>
            <el-progress 
              :percentage="calcPercentage(apStats.total_paid, apStats.total_payable)" 
              status="warning"
              :stroke-width="10"
              class="ap-progress"
            >
              <template #default="{ percentage }">
                <span style="font-size: 12px; color: #606266;">{{ percentage }}%</span>
              </template>
            </el-progress>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 2: Contract Summaries (5 Cards) -->
    <el-row :gutter="20" style="margin-top: 20px;" class="summary-card-row">
      <!-- 1. Upstream Contracts (Category) -->
      <el-col :xs="24" :sm="12" class="stat-col-5">
        <el-card shadow="hover" class="stat-card border-left-primary" style="height: 300px;">
          <div class="card-content">
            <div class="card-title">{{ currentMonth ? `${currentMonth}月 ` : '' }}上游概况(类别)</div>
             <div class="card-amount text-primary">
               {{ upstreamSummary.reduce((acc, cur) => acc + cur.count, 0) }} 单 / 
               ¥{{ formatWan(upstreamSummary.reduce((acc, cur) => acc + cur.amount, 0)) }} 万
             </div>
             <div class="card-list">
               <div v-for="item in upstreamSummary.slice(0, 5)" :key="item.name" class="list-item">
                 <span>{{ item.name }}</span>
                 <span>{{ item.count }}单 / ¥{{ formatWan(item.amount) }}万</span>
               </div>
             </div>
          </div>
        </el-card>
      </el-col>

      <!-- 2. Upstream Contracts (Company Category) -->
      <el-col :xs="24" :sm="12" class="stat-col-5">
        <el-card shadow="hover" class="stat-card border-left-purple" style="height: 300px; border-left: 4px solid #8e44ad;">
          <div class="card-content">
            <div class="card-title">{{ currentMonth ? `${currentMonth}月 ` : '' }}上游概况(公司)</div>
             <div class="card-amount" style="color: #8e44ad;">
               {{ upstreamCompanySummary.reduce((acc, cur) => acc + cur.count, 0) }} 单 / 
               ¥{{ formatWan(upstreamCompanySummary.reduce((acc, cur) => acc + cur.amount, 0)) }} 万
             </div>
             <div class="card-list">
               <div v-for="item in upstreamCompanySummary.slice(0, 5)" :key="item.name" class="list-item">
                 <span>{{ item.name }}</span>
                 <span>{{ item.count }}单 / ¥{{ formatWan(item.amount) }}万</span>
               </div>
             </div>
          </div>
        </el-card>
      </el-col>

      <!-- 3. Downstream Contracts Summary -->
      <el-col :xs="24" :sm="12" class="stat-col-5">
        <el-card shadow="hover" class="stat-card border-left-info" style="height: 300px;">
          <div class="card-content">
            <div class="card-title">{{ currentMonth ? `${currentMonth}月 ` : '' }}下游合同概况</div>
             <div class="card-amount text-info">
               {{ downstreamSummary.reduce((acc, cur) => acc + cur.count, 0) }} 单 / 
               ¥{{ formatWan(downstreamSummary.reduce((acc, cur) => acc + cur.amount, 0)) }} 万
             </div>
             <div class="card-list">
               <div v-for="item in downstreamSummary.slice(0, 5)" :key="item.name" class="list-item">
                 <span>{{ item.name }}</span>
                 <span>{{ item.count }}单 / ¥{{ formatWan(item.amount) }}万</span>
               </div>
             </div>
          </div>
        </el-card>
      </el-col>

      <!-- 4. Management Contracts Summary (New) -->
      <el-col :xs="24" :sm="12" class="stat-col-5">
        <el-card shadow="hover" class="stat-card border-left-warning" style="height: 300px;">
          <div class="card-content">
            <div class="card-title">{{ currentMonth ? `${currentMonth}月 ` : '' }}管理合同概况</div>
             <div class="card-amount text-warning">
               {{ managementSummary.reduce((acc, cur) => acc + cur.count, 0) }} 单 / 
               ¥{{ formatWan(managementSummary.reduce((acc, cur) => acc + cur.amount, 0)) }} 万
             </div>
             <div class="card-list">
               <div v-for="item in managementSummary.slice(0, 5)" :key="item.name" class="list-item">
                 <span>{{ item.name }}</span>
                 <span>{{ item.count }}单 / ¥{{ formatWan(item.amount) }}万</span>
               </div>
             </div>
          </div>
        </el-card>
      </el-col>

      <!-- 5. Non-Contract Expenses Summary (New) -->
      <el-col :xs="24" :sm="12" class="stat-col-5">
        <el-card shadow="hover" class="stat-card border-left-danger" style="height: 300px; border-left: 4px solid #F56C6C;">
          <div class="card-content">
            <div class="card-title">{{ currentMonth ? `${currentMonth}月 ` : '' }}无合同费用</div>
             <div class="card-amount text-danger">
               {{ expenseSummary.reduce((acc, cur) => acc + cur.count, 0) }} 笔 / 
               ¥{{ formatWan(expenseSummary.reduce((acc, cur) => acc + cur.value, 0)) }} 万
             </div>
             <div class="card-list">
               <!-- Note: Field is 'value' not 'amount' for expense -->
               <div v-for="item in expenseSummary.slice(0, 5)" :key="item.name" class="list-item">
                 <span>{{ item.name }}</span>
                 <span>{{ item.count }}笔 / ¥{{ formatWan(item.value) }}万</span>
               </div>
             </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 3: Pie Charts (4 Charts) -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- Upstream Categories Pie -->
      <el-col :xs="24" :md="6">
        <el-card shadow="hover" style="height: 300px;">
          <template #header><span style="font-size: 12px; font-weight: bold;">上游合同分类</span></template>
          <div ref="upstreamPieRef" style="height: 200px; width: 100%;"></div>
        </el-card>
      </el-col>

      <!-- Upstream Company Categories Pie (New) -->
      <el-col :xs="24" :md="6">
        <el-card shadow="hover" style="height: 300px;">
          <template #header><span style="font-size: 12px; font-weight: bold;">上游合同公司分类</span></template>
          <div ref="upstreamCompanyPieRef" style="height: 200px; width: 100%;"></div>
        </el-card>
      </el-col>

      <!-- Expense Breakdown Pie -->
      <el-col :xs="24" :md="6">
        <el-card shadow="hover" style="height: 300px;">
           <template #header><span style="font-size: 12px; font-weight: bold;">支出构成</span></template>
           <div ref="expenseStructPieRef" style="height: 200px; width: 100%;"></div>
        </el-card>
      </el-col>

       <!-- Non-Contract Expense Categories Pie -->
      <el-col :xs="24" :md="6">
        <el-card shadow="hover" style="height: 300px;">
           <template #header><span style="font-size: 12px; font-weight: bold;">无合同费用分类</span></template>
           <div ref="expenseCatPieRef" style="height: 200px; width: 100%;"></div>
        </el-card>
      </el-col>
    </el-row>

  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, reactive } from 'vue'
import * as echarts from 'echarts'
import { getContractSummary, getFinanceTrend, getExpenseBreakdown, getArApStats } from '@/api/reports'
import { ElMessage } from 'element-plus'

// State
const loading = ref(false)
const currentYear = ref(new Date().getFullYear().toString())
const currentMonth = ref(null) // null means full year

// Data storage
const arStats = reactive({ total_receivable: 0, total_received: 0, outstanding: 0 })
const apStats = reactive({ total_payable: 0, total_paid: 0, outstanding: 0 })
const upstreamSummary = ref([])
const upstreamCompanySummary = ref([])
const downstreamSummary = ref([])
const managementSummary = ref([])
const expenseSummary = ref([])

// Annual Summary Data (for Row 1 cards)
const annualUpstreamCount = ref(0)
const annualUpstreamAmount = ref(0)
const annualReceiptsAmount = ref(0)
const annualPaymentsAmount = ref(0)
const annualDownMgmtCount = ref(0)
const annualDownMgmtAmount = ref(0)

// Chart Refs
const trendChartRef = ref(null)
const upstreamPieRef = ref(null)
const upstreamCompanyPieRef = ref(null)
const expenseStructPieRef = ref(null)
const expenseCatPieRef = ref(null)

let trendChart = null
let upstreamPieChart = null
let upstreamCompanyPieChart = null
let expenseStructChart = null
let expenseCatChart = null

// Methods
const formatMoney = (val) => {
  if (!val) return '0.00'
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatWan = (val) => {
  if (!val) return '0.00'
  return (Number(val) / 10000).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const calcPercentage = (num, total) => {
  if (!total || total === 0) return 0
  const p = (num / total) * 100
  return Number(p.toFixed(2)) // Return value for display, el-progress handles clamping
}

const fetchData = async () => {
  loading.value = true
  try {
    const year = currentYear.value
    const month = currentMonth.value || undefined

    // Parallel requests
    const [summaryRes, trendRes, expenseRes, arApRes] = await Promise.all([
      getContractSummary(year, month),
      getFinanceTrend(year, month),
      getExpenseBreakdown(year, month),
      getArApStats(year, month)
    ])

    // 1. Process AR/AP
    Object.assign(arStats, arApRes.ar)
    Object.assign(apStats, arApRes.ap)

    // 2. Process Contract Summary
    upstreamSummary.value = summaryRes.upstream_by_category
    upstreamCompanySummary.value = summaryRes.upstream_by_company_category || []
    downstreamSummary.value = summaryRes.downstream_by_category
    managementSummary.value = summaryRes.management_by_category || []
    expenseSummary.value = expenseRes.non_contract_breakdown || [] // Used for summary card
    
    // 3. Calculate Annual Summary Statistics (for Row 1 cards)
    // Annual Upstream: count and amount
    annualUpstreamCount.value = upstreamSummary.value.reduce((acc, cur) => acc + cur.count, 0)
    annualUpstreamAmount.value = upstreamSummary.value.reduce((acc, cur) => acc + cur.amount, 0)
    
    // Annual Receipts: total received amount from AR stats
    annualReceiptsAmount.value = arApRes.ar.total_received
    
    // Annual Payments: total paid from AP stats (includes downstream + management + non-contract)
    annualPaymentsAmount.value = arApRes.ap.total_paid
    
    // Annual Downstream + Management: count and amount
    const downCount = downstreamSummary.value.reduce((acc, cur) => acc + cur.count, 0)
    const downAmount = downstreamSummary.value.reduce((acc, cur) => acc + cur.amount, 0)
    const mgmtCount = managementSummary.value.reduce((acc, cur) => acc + cur.count, 0)
    const mgmtAmount = managementSummary.value.reduce((acc, cur) => acc + cur.amount, 0)
    annualDownMgmtCount.value = downCount + mgmtCount
    annualDownMgmtAmount.value = downAmount + mgmtAmount
    
    // 4. Update Charts
    initTrendChart(trendRes)
    initUpstreamPie(summaryRes.upstream_by_category)
    initUpstreamCompanyPie(summaryRes.upstream_by_company_category || [])
    initExpenseStructPie(expenseRes.overall_breakdown)
    initExpenseCatPie(expenseRes.non_contract_breakdown)

  } catch (error) {
    console.error(error)
    ElMessage.error('获取报表数据失败')
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  fetchData()
}

// Chart Initializers
const initTrendChart = (data) => {
  if (!trendChartRef.value) return
  if (trendChart) trendChart.dispose()
  
  trendChart = echarts.init(trendChartRef.value)
  trendChart.setOption({
    tooltip: { 
      confine: true,
      trigger: 'axis',
      formatter: function (params) {
        let res = params[0].name + '<br/>';
        params.forEach(item => {
          res += item.marker + item.seriesName + ': ' + Number(item.value).toFixed(2) + ' 万元<br/>';
        });
        return res;
      }
    },
    legend: { 
      data: ['月度收入', '下游合同', '管理合同', '无合同费用'],
      bottom: 0,
      itemWidth: 15,
      itemHeight: 10,
      textStyle: { fontSize: 10 }
    },
    grid: { 
      left: '3%', 
      right: '4%', 
      top: '15%', 
      bottom: '25px', 
      containLabel: true 
    },
    xAxis: { 
      type: 'category', 
      data: data.months,
      axisLabel: { interval: 0, fontSize: 10 }
    },
    yAxis: { 
      type: 'value',
      name: '金额 (万元)',
      splitLine: { show: false }
    },
    series: [
      {
        name: '月度收入',
        type: 'bar',
        data: data.income.map(v => (v / 10000).toFixed(2)),
        itemStyle: { color: '#67C23A' },
        barMaxWidth: 15
      },
      // Stacked Expense Series
      {
        name: '下游合同',
        type: 'bar',
        stack: 'expense',
        data: data.expense_breakdown.downstream.map(v => (v / 10000).toFixed(2)),
        itemStyle: { color: '#F56C6C' },
        barMaxWidth: 15
      },
      {
        name: '管理合同',
        type: 'bar',
        stack: 'expense',
        data: data.expense_breakdown.management.map(v => (v / 10000).toFixed(2)),
        itemStyle: { color: '#E6A23C' },
        barMaxWidth: 15
      },
      {
        name: '无合同费用',
        type: 'bar',
        stack: 'expense',
        data: data.expense_breakdown.non_contract.map(v => (v / 10000).toFixed(2)),
        itemStyle: { color: '#909399' },
        barMaxWidth: 15
      }
    ]
  })
  trendChart.resize()
}

const initUpstreamPie = (data) => {
  if (!upstreamPieRef.value) return
  if (upstreamPieChart) upstreamPieChart.dispose()
  
  // Format for pie: { value, name }
  const pieData = data.map(item => ({ value: item.amount, name: item.name }))
  
  upstreamPieChart = echarts.init(upstreamPieRef.value)
  upstreamPieChart.setOption({
    tooltip: { 
      confine: true,
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)' 
    },
    legend: { type: 'scroll', bottom: 0, pageButtonGap: 5 },
    series: [
      {
        name: '上游合同分类',
        type: 'pie',
        radius: ['35%', '60%'], // Smaller radius
        center: ['50%', '42%'], // Move up slightly
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 5,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '12',
            fontWeight: 'bold'
          }
        },
        labelLine: { show: false },
        data: pieData.length > 0 ? pieData : [{ value: 0, name: '暂无数据' }]
      }
    ]
  })
}

const initUpstreamCompanyPie = (data) => {
  if (!upstreamCompanyPieRef.value) return
  if (upstreamCompanyPieChart) upstreamCompanyPieChart.dispose()
  
  // Format for pie: { value, name }
  const pieData = data.map(item => ({ value: item.amount, name: item.name }))
  
  upstreamCompanyPieChart = echarts.init(upstreamCompanyPieRef.value)
  upstreamCompanyPieChart.setOption({
    tooltip: { 
      confine: true,
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)' 
    },
    legend: { type: 'scroll', bottom: 0, pageButtonGap: 5 },
    series: [
      {
        name: '上游合同公司分类',
        type: 'pie',
        radius: ['35%', '60%'], // Smaller radius
        center: ['50%', '42%'], // Move up slightly
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 5,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '12',
            fontWeight: 'bold'
          }
        },
        labelLine: { show: false },
        data: pieData.length > 0 ? pieData : [{ value: 0, name: '暂无数据' }]
      }
    ]
  })
}

const initExpenseStructPie = (data) => {
  if (!expenseStructPieRef.value) return
  if (expenseStructChart) expenseStructChart.dispose()
  
  // Check empty
  const hasData = data.some(d => d.value > 0)
  
  expenseStructChart = echarts.init(expenseStructPieRef.value)
  expenseStructChart.setOption({
    tooltip: { confine: true, trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: '0%' },
    series: [
       {
        name: '支出构成',
        type: 'pie',
        radius: '60%',
        center: ['50%', '45%'],
        data: hasData ? data : [{ value: 0, name: '暂无数据' }],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  })
}

const initExpenseCatPie = (data) => {
  if (!expenseCatPieRef.value) return
  if (expenseCatChart) expenseCatChart.dispose()
  
  const hasData = data.some(d => d.value > 0)
  
  expenseCatChart = echarts.init(expenseCatPieRef.value)
  expenseCatChart.setOption({
    tooltip: { confine: true, trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { type: 'scroll', bottom: '0%' },
    series: [
       {
        name: '无合同费用分类',
        type: 'pie',
        radius: ['30%', '60%'],
        center: ['50%', '45%'],
        roseType: 'area', // Rose chart for variety
        data: hasData ? data : [{ value: 0, name: '暂无数据' }],
        itemStyle: { borderRadius: 5 }
      }
    ]
  })
}

const handleResize = () => {
  trendChart && trendChart.resize()
  upstreamPieChart && upstreamPieChart.resize()
  upstreamCompanyPieChart && upstreamCompanyPieChart.resize()
  expenseStructChart && expenseStructChart.resize()
  expenseCatChart && expenseCatChart.resize()
}

onMounted(() => {
  nextTick(() => {
    fetchData()
    window.addEventListener('resize', handleResize)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart && trendChart.dispose()
  upstreamPieChart && upstreamPieChart.dispose()
  upstreamCompanyPieChart && upstreamCompanyPieChart.dispose()
  expenseStructChart && expenseStructChart.dispose()
  expenseCatChart && expenseCatChart.dispose()
})
</script>

<style scoped lang="scss">
.filter-container {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  flex-wrap: wrap; // Responsive
  
  .filter-label {
    margin-right: 10px;
    font-weight: bold;
    color: #606266;
  }
}

.stat-card {
  margin-bottom: 20px;
  border-left-width: 5px;
  border-left-style: solid;
  
  &.border-left-primary { border-left-color: #409EFF; }
  &.border-left-success { border-left-color: #67C23A; }
  &.border-left-warning { border-left-color: #E6A23C; }
  &.border-left-info { border-left-color: #909399; }
  
  .card-content {
     position: relative;
    .card-title {
      font-size: 14px;
      color: #909399;
      font-weight: bold;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .card-amount {
      font-size: 20px;
      font-weight: bold;
      margin: 10px 0;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    }
    .card-sub {
      font-size: 12px;
      color: #606266;
      margin-bottom: 10px;
      line-height: 1.5;
    }
    .card-list {
       margin-top: 10px;
       font-size: 12px;
       .list-item {
         display: flex;
         justify-content: space-between;
         margin-bottom: 5px;
         color: #606266;
       }
    }
  }
}

.text-success { color: #67C23A; }
.text-warning { color: #E6A23C; }
.text-danger { color: #F56C6C; }
.text-primary { color: #409EFF; }
.text-info { color: #909399; }

:deep(.ap-progress .el-progress-bar__outer) {
  background-color: #faecd8 !important; /* AP Background (Light Orange) */
}

:deep(.ar-progress .el-progress-bar__outer) {
  background-color: #a0cfff !important; /* AR Background (Blue) */
}

@media (min-width: 992px) {
  .stat-col-5 {
    width: 20%;
    max-width: 20%;
    flex: 0 0 20%;
  }
}
</style>
