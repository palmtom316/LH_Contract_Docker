<template>
  <div class="dashboard-container">
    <!-- Modern Top Cards -->
    <el-row :gutter="10">
      <el-col :xs="12" :sm="12" :lg="6" v-for="item in cardData" :key="item.title">
        <el-card shadow="hover" class="stat-card-modern" :style="{ background: item.color }">
          <div class="card-icon-bg">
            <component :is="item.icon" />
          </div>
          <div class="card-inner">
            <div class="card-modern-header">
              <span class="title">{{ item.title }}</span>
              <div class="icon-wrapper">
                <component :is="item.icon" />
              </div>
            </div>
            <div class="card-modern-content">
              <h2 class="amount">
                <template v-if="item.count !== undefined">
                  {{ item.count }} <small>单</small>
                </template>
                <template v-else>
                  ¥ {{ formatWan(item.value) }} <small>万</small>
                </template>
              </h2>
              <div class="amount-sub" v-if="item.count !== undefined">
                ¥ {{ formatWan(item.value) }} 万
              </div>
              <div class="sub-info">{{ item.subInfo }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Period Statistics Cards (Split) - Desktop View -->
    <template v-if="!isMobile">
      <el-row :gutter="20" style="margin-top: 10px;">
        <!-- Monthly Card -->
        <el-col :span="12">
          <el-card shadow="hover" class="period-card-modern">
            <template #header>
              <div class="card-modern-title-bar">
                <div class="title-left">
                  <el-icon class="title-icon monthly"><TrendCharts /></el-icon>
                  <span>经营状况分析 (近30天)</span>
                </div>
              </div>
            </template>

            <div class="period-content-wrapper">
              <el-row :gutter="0" class="period-content-row">
                <el-col :span="12" class="period-col left-col">
                  <div class="section-badge upstream">上游合同</div>
                  <div class="stat-modern-row">
                    <span class="label">签约数量</span>
                    <span class="value">{{ periodStats.monthly.upstream_count }} <small>单</small></span>
                  </div>
                  <div class="stat-modern-row highlight">
                    <span class="label">签约金额</span>
                    <span class="value income">¥ {{ formatWan(periodStats.monthly.upstream_amount) }} <small>万</small></span>
                  </div>
                  <div class="stat-modern-row highlight">
                    <span class="label">回款金额</span>
                    <span class="value success">¥ {{ formatWan(periodStats.monthly.upstream_receipts) }} <small>万</small></span>
                  </div>
                </el-col>
                <el-col :span="12" class="period-col right-col">
                  <div class="section-badge downstream">下游及管理合同</div>
                  <div class="stat-modern-row">
                    <span class="label">签约数量</span>
                    <span class="value">{{ periodStats.monthly.downstream_mgmt_count }} <small>单</small></span>
                  </div>
                  <div class="stat-modern-row">
                    <span class="label">签约金额</span>
                    <span class="value expense">¥ {{ formatWan(periodStats.monthly.downstream_mgmt_amount) }} <small>万</small></span>
                  </div>
                  <div class="stat-modern-row">
                    <span class="label">付款金额</span>
                    <span class="value expense">¥ {{ formatWan(periodStats.monthly.downstream_mgmt_payment) }} <small>万</small></span>
                  </div>
                  <div class="stat-modern-row">
                    <span class="label">无合同费用</span>
                    <span class="value text-gray">¥ {{ formatWan(periodStats.monthly.non_contract_expense) }} <small>万</small></span>
                  </div>
                  <div class="stat-modern-row">
                    <span class="label">零星用工</span>
                    <span class="value text-gray">¥ {{ formatWan(periodStats.monthly.zero_hour_labor) }} <small>万</small></span>
                  </div>
                </el-col>
              </el-row>
            </div>
            
            <!-- Month Trend Chart -->
            <div style="padding: 20px; border-top: 1px solid #f0f2f5;">
              <div style="font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #303133;">
                <el-icon><TrendCharts /></el-icon> 近30天收支趋势
              </div>
              <div ref="monthChartRef" style="height: 250px; width: 100%;"></div>
            </div>
          </el-card>
        </el-col>

        <!-- Quarterly Card -->
        <el-col :span="12">
          <el-card shadow="hover" class="period-card-modern">
            <template #header>
              <div class="card-modern-title-bar">
                <div class="title-left">
                  <el-icon class="title-icon quarterly"><TrendCharts /></el-icon>
                  <span>经营状况分析 (近一季度)</span>
                </div>
              </div>
            </template>

            <div class="period-content-wrapper">
               <el-row :gutter="0" class="period-content-row">
                <el-col :span="12" class="period-col left-col">
                  <div class="section-badge upstream kv-badge">上游合同</div>
                  <div class="stat-modern-row">
                    <span class="label">签约数量</span>
                    <span class="value">{{ periodStats.quarterly.upstream_count }} <small>单</small></span>
                  </div>
                  <div class="stat-modern-row highlight">
                    <span class="label">签约金额</span>
                    <span class="value income">¥ {{ formatWan(periodStats.quarterly.upstream_amount) }} <small>万</small></span>
                  </div>
                  <div class="stat-modern-row highlight">
                    <span class="label">回款金额</span>
                    <span class="value success">¥ {{ formatWan(periodStats.quarterly.upstream_receipts) }} <small>万</small></span>
                  </div>
                </el-col>
                <el-col :span="12" class="period-col right-col">
                  <div class="section-badge downstream kv-badge">下游及管理合同</div>
                  <div class="stat-modern-row">
                    <span class="label">签约数量</span>
                    <span class="value">{{ periodStats.quarterly.downstream_mgmt_count }} <small>单</small></span>
                  </div>
                  <div class="stat-modern-row">
                    <span class="label">签约金额</span>
                    <span class="value expense">¥ {{ formatWan(periodStats.quarterly.downstream_mgmt_amount) }} <small>万</small></span>
                  </div>
                  <div class="stat-modern-row">
                    <span class="label">付款金额</span>
                    <span class="value expense">¥ {{ formatWan(periodStats.quarterly.downstream_mgmt_payment) }} <small>万</small></span>
                  </div>
                  <div class="stat-modern-row">
                    <span class="label">无合同费用</span>
                    <span class="value text-gray">¥ {{ formatWan(periodStats.quarterly.non_contract_expense) }} <small>万</small></span>
                  </div>
                  <div class="stat-modern-row">
                    <span class="label">零星用工</span>
                    <span class="value text-gray">¥ {{ formatWan(periodStats.quarterly.zero_hour_labor) }} <small>万</small></span>
                  </div>
                </el-col>
              </el-row>
            </div>
            
            <!-- Quarter Trend Chart -->
            <div style="padding: 20px; border-top: 1px solid #f0f2f5;">
              <div style="font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #303133;">
                <el-icon><TrendCharts /></el-icon> 近90天收支趋势
              </div>
              <div ref="quarterChartRef" style="height: 250px; width: 100%;"></div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <!-- Mobile Tabbed View -->
    <template v-else>
      <el-row style="margin-top: 10px;">
        <el-col :span="24">
          <el-card shadow="never" class="period-card-modern mobile-tabs-card">
            <el-tabs v-model="mobileActiveTab" class="mobile-dashboard-tabs">
              <el-tab-pane label="近30天分析" name="monthly">
                <div class="period-content-wrapper">
                  <el-row :gutter="0" class="period-content-row">
                    <el-col :span="12" class="period-col left-col">
                      <div class="section-badge upstream">上游合同</div>
                       <div class="stat-modern-row">
                        <span class="label">签约</span>
                        <span class="value">{{ periodStats.monthly.upstream_count }} <small>单</small></span>
                      </div>
                      <div class="stat-modern-row highlight">
                        <span class="label">金额</span>
                        <span class="value income">¥ {{ formatWan(periodStats.monthly.upstream_amount) }}</span>
                      </div>
                      <div class="stat-modern-row highlight">
                        <span class="label">回款</span>
                        <span class="value success">¥ {{ formatWan(periodStats.monthly.upstream_receipts) }}</span>
                      </div>
                    </el-col>
                    <el-col :span="12" class="period-col right-col">
                      <div class="section-badge downstream">下游/管理</div>
                       <div class="stat-modern-row">
                        <span class="label">签约</span>
                        <span class="value">{{ periodStats.monthly.downstream_mgmt_count }} <small>单</small></span>
                      </div>
                      <div class="stat-modern-row">
                        <span class="label">金额</span>
                        <span class="value expense">¥ {{ formatWan(periodStats.monthly.downstream_mgmt_amount) }}</span>
                      </div>
                      <div class="stat-modern-row">
                        <span class="label">付款</span>
                        <span class="value expense">¥ {{ formatWan(periodStats.monthly.downstream_mgmt_payment) }}</span>
                      </div>
                       <div class="stat-modern-row">
                        <span class="label">无合同</span>
                        <span class="value text-gray">¥ {{ formatWan(periodStats.monthly.non_contract_expense) }}</span>
                      </div>
                      <div class="stat-modern-row">
                        <span class="label">零星</span>
                        <span class="value text-gray">¥ {{ formatWan(periodStats.monthly.zero_hour_labor) }}</span>
                      </div>
                    </el-col>
                  </el-row>
                </div>
                <!-- Month Trend Chart (Mobile) -->
                <div style="padding: 10px; border-top: 1px solid #f0f2f5;">
                   <div style="font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #303133;">
                    <el-icon><TrendCharts /></el-icon> 近30天趋势
                  </div>
                  <div ref="mobileMonthChartRef" style="height: 250px; width: 100%;"></div>
                </div>
              </el-tab-pane>

              <el-tab-pane label="近一季度分析" name="quarterly">
                <div class="period-content-wrapper">
                   <el-row :gutter="0" class="period-content-row">
                    <el-col :span="12" class="period-col left-col">
                      <div class="section-badge upstream kv-badge">上游合同</div>
                       <div class="stat-modern-row">
                        <span class="label">签约</span>
                        <span class="value">{{ periodStats.quarterly.upstream_count }} <small>单</small></span>
                      </div>
                      <div class="stat-modern-row highlight">
                        <span class="label">金额</span>
                        <span class="value income">¥ {{ formatWan(periodStats.quarterly.upstream_amount) }}</span>
                      </div>
                      <div class="stat-modern-row highlight">
                        <span class="label">回款</span>
                        <span class="value success">¥ {{ formatWan(periodStats.quarterly.upstream_receipts) }}</span>
                      </div>
                    </el-col>
                    <el-col :span="12" class="period-col right-col">
                      <div class="section-badge downstream kv-badge">下游/管理</div>
                       <div class="stat-modern-row">
                        <span class="label">签约</span>
                        <span class="value">{{ periodStats.quarterly.downstream_mgmt_count }} <small>单</small></span>
                      </div>
                      <div class="stat-modern-row">
                        <span class="label">金额</span>
                        <span class="value expense">¥ {{ formatWan(periodStats.quarterly.downstream_mgmt_amount) }}</span>
                      </div>
                      <div class="stat-modern-row">
                        <span class="label">付款</span>
                        <span class="value expense">¥ {{ formatWan(periodStats.quarterly.downstream_mgmt_payment) }}</span>
                      </div>
                       <div class="stat-modern-row">
                        <span class="label">无合同</span>
                        <span class="value text-gray">¥ {{ formatWan(periodStats.quarterly.non_contract_expense) }}</span>
                      </div>
                       <div class="stat-modern-row">
                        <span class="label">零星</span>
                        <span class="value text-gray">¥ {{ formatWan(periodStats.quarterly.zero_hour_labor) }}</span>
                      </div>
                    </el-col>
                  </el-row>
                </div>
                 <!-- Quarter Trend Chart (Mobile) -->
                <div style="padding: 10px; border-top: 1px solid #f0f2f5;">
                   <div style="font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #303133;">
                    <el-icon><TrendCharts /></el-icon> 近90天趋势
                  </div>
                  <div ref="mobileQuarterChartRef" style="height: 250px; width: 100%;"></div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </el-col>
      </el-row>
    </template>
    
    <!-- Charts Section -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- Bar Chart: Income vs Expense -->
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>{{ currentYear }}年度 收支趋势</span>
            </div>
          </template>
          <div ref="barChartRef" style="height: 350px; width: 100%;"></div>
        </el-card>
      </el-col>
      
      <!-- Pie Chart: Contract Categories -->
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>合同分类</span>
            </div>
          </template>
          <el-row>
            <el-col :xs="24" :sm="12">
               <div style="text-align: center; font-size: 12px; font-weight: bold; margin-bottom: 5px;">合同类别</div>
               <div ref="pieCategoryChartRef" style="height: 320px; width: 100%;"></div>
            </el-col>
            <el-col :xs="24" :sm="12">
               <div style="text-align: center; font-size: 12px; font-weight: bold; margin-bottom: 5px;">自定类别</div>
               <div ref="pieCompanyChartRef" style="height: 320px; width: 100%;"></div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import echarts from '@/utils/echarts'
import { getStats, getPeriodStats, getPeriodTrend } from '@/api/dashboard'
import { getFinanceTrend } from '@/api/reports'
import { ElMessage } from 'element-plus'
import { TrendCharts, Money, Wallet, Coin, DataAnalysis, PieChart, Document, ArrowRight } from '@element-plus/icons-vue'
import { useDevice } from '@/composables/useDevice'

const { isMobile } = useDevice()
const mobileActiveTab = ref('monthly')

const barChartRef = ref(null)
const pieCategoryChartRef = ref(null)
const pieCompanyChartRef = ref(null)
// Rename ref to distinct names
const monthChartRef = ref(null)
const quarterChartRef = ref(null)
const mobileMonthChartRef = ref(null)
const mobileQuarterChartRef = ref(null)

let barChart = null
let pieCategoryChart = null
let pieCompanyChart = null
// Rename vars
let monthChart = null
let quarterChart = null
let mobileMonthChart = null
let mobileQuarterChart = null

const currentYear = new Date().getFullYear().toString()
// const activePeriod = ref('monthly') - REMOVED

// Watcher removed because we load both now

// Watch mobile tab change to resize/init charts
watch(mobileActiveTab, (val) => {
  nextTick(() => {
    if (val === 'monthly') {
      if (mobileMonthChart) mobileMonthChart.resize()
      else if (monthTrendData) initMonthChart(monthTrendData)
    } else {
      if (mobileQuarterChart) mobileQuarterChart.resize()
      else if (quarterTrendData) initQuarterChart(quarterTrendData)
    }
  })
})

const cardData = ref([
  { title: '年度上游签约', value: 0, count: 0, tag: '总览', color: 'linear-gradient(135deg, #1890FF 0%, #36CFC9 100%)', icon: 'Document', subInfo: '累计签约总额' },
  { title: '年度下游签约', value: 0, count: 0, tag: '成本', color: 'linear-gradient(135deg, #FAAD14 0%, #FADB14 100%)', icon: 'Wallet', subInfo: '累计支出预算' },
  { title: '年度回款总额', value: 0, tag: '收入', color: 'linear-gradient(135deg, #52C41A 0%, #95D475 100%)', icon: 'Money', subInfo: '实际到账金额' },
  { title: '年度付款总额', value: 0, tag: '支出', color: 'linear-gradient(135deg, #FF4D4F 0%, #F56C6C 100%)', icon: 'Coin', subInfo: '实际支出金额' },
])

// Period statistics data
const periodStats = ref({
  monthly: {
    upstream_count: 0,
    upstream_amount: 0,
    upstream_receipts: 0,
    downstream_mgmt_count: 0,
    downstream_mgmt_amount: 0,
    downstream_mgmt_payment: 0,
    non_contract_expense: 0,
    zero_hour_labor: 0
  },
  quarterly: {
    upstream_count: 0,
    upstream_amount: 0,
    upstream_receipts: 0,
    downstream_mgmt_count: 0,
    downstream_mgmt_amount: 0,
    downstream_mgmt_payment: 0,
    non_contract_expense: 0,
    zero_hour_labor: 0
  }
})

const formatCurrency = (val) => {
  if (!val) return '0.00'
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatWan = (val) => {
  if (!val) return '0.00'
  return (Number(val) / 10000).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

let monthTrendData = null
let quarterTrendData = null

const fetchData = async () => {
  try {
    // Fetch everything in parallel, including both trend periods
    const [statsRes, trendRes, periodRes, monthTrendRes, quarterTrendRes] = await Promise.all([
      getStats(),
      getFinanceTrend(currentYear),
      getPeriodStats(),
      getPeriodTrend('monthly'),
      getPeriodTrend('quarterly')
    ])
    
    const { cards, charts } = statsRes
    
    // Update Cards with Annual Statistics
    // 0: Upstream
    cardData.value[0].count = cards.annual_upstream_count
    cardData.value[0].value = cards.annual_upstream_amount
    // 1: Downstream & Management
    cardData.value[1].count = cards.annual_down_mgmt_count
    cardData.value[1].value = cards.annual_down_mgmt_amount
    // 2: Receipts
    cardData.value[2].value = cards.annual_receipts_amount
    // 3: Payments
    cardData.value[3].value = cards.annual_payments_amount
    
    // Update Period Statistics
    periodStats.value = periodRes
    
    // Save data for re-init
    monthTrendData = monthTrendRes
    quarterTrendData = quarterTrendRes

    // Init Charts
    initTrendChart(trendRes)
    if (charts.pie_category) initCategoryPie(charts.pie_category)
    if (charts.pie_company) initCompanyPie(charts.pie_company)
    
    // Init both period charts
    initMonthChart(monthTrendData)
    initQuarterChart(quarterTrendData)

  } catch (error) {
    console.error(error)
    ElMessage.error('获取仪表盘数据失败')
  }
}
// Removed fetchPeriodTrend as it's now part of fetchData


const initMonthChart = (data) => {
  // Desktop
  if (monthChartRef.value) {
    if (monthChart) monthChart.dispose()
    monthChart = echarts.init(monthChartRef.value)
    setChartOption(monthChart, data, 4) // Show date every 5 days
  }
  // Mobile
  if (mobileMonthChartRef.value) {
    if (mobileMonthChart) mobileMonthChart.dispose()
    mobileMonthChart = echarts.init(mobileMonthChartRef.value)
    setChartOption(mobileMonthChart, data, 4)
  }
}

const initQuarterChart = (data) => {
  // Desktop
  if (quarterChartRef.value) {
    if (quarterChart) quarterChart.dispose()
    quarterChart = echarts.init(quarterChartRef.value)
    setChartOption(quarterChart, data, 9) // Show date every 10 days
  }
  // Mobile
  if (mobileQuarterChartRef.value) {
    if (mobileQuarterChart) mobileQuarterChart.dispose()
    mobileQuarterChart = echarts.init(mobileQuarterChartRef.value)
    setChartOption(mobileQuarterChart, data, 9)
  }
}

const setChartOption = (chartInstance, data, axisInterval = 'auto') => {
  chartInstance.setOption({
    baseOption: {
      tooltip: { 
        confine: true,
        trigger: 'axis',
        formatter: function (params) {
          let res = params[0].name + '<br/>'; // Date
          let hasValue = false;
          params.forEach(item => {
            const val = Number(item.value);
            if (val > 0) {
              hasValue = true;
              res += item.marker + item.seriesName + ': ' + val.toFixed(2) + ' 万元<br/>';
            }
          });
          return hasValue ? res : '';
        }
      },
      legend: { 
        data: ['收入', '下游合同', '管理合同', '无合同费用', '零星用工'],
        bottom: 0,
        itemWidth: 15,
        itemHeight: 10,
        textStyle: { fontSize: 12 }
      },
      grid: { 
        left: '8%', 
        right: '4%', 
        top: '10%', 
        bottom: '30px', 
        containLabel: true 
      },
      xAxis: { 
        type: 'category', 
        data: data.dates,
        axisLabel: { 
          fontSize: 10,
          interval: axisInterval,
          hideOverlap: true,
          rotate: 0,
          formatter: function (value) {
              // YYYY-MM-DD -> MM-DD
              if (value && value.length > 5) {
                  return value.substring(5);
              }
              return value;
          }
        }
      },
      yAxis: { 
        type: 'value',
        name: '金额 (万元)',
        splitLine: { show: false }
      },
      series: [
        {
          name: '收入',
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
        },
        {
          name: '零星用工',
          type: 'bar',
          stack: 'expense',
          data: data.expense_breakdown.labor.map(v => (v / 10000).toFixed(2)),
          itemStyle: { color: '#A0CFFF' },
          barMaxWidth: 15
        }
      ]
    },
    media: [
      {
        query: { maxWidth: 767 },
        option: {
          legend: {
            itemWidth: 10,
            textStyle: { fontSize: 9 },
            bottom: 0
          },
          grid: {
             top: '15%',
             bottom: '60px',
             left: '12%', // Increased left margin for Y-axis label
             containLabel: true
          },
          xAxis: {
            axisLabel: {
              fontSize: 9,
              rotate: 45
            }
          }
        }
      }
    ]
  })
}

const initTrendChart = (data) => {
  if (!barChartRef.value) return
  if (barChart) barChart.dispose()
  
  barChart = echarts.init(barChartRef.value)
  
  barChart.setOption({
    baseOption: {
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
        data: ['月度收入', '下游合同', '管理合同', '无合同费用', '零星用工'],
        bottom: 0,
        itemWidth: 15,
        itemHeight: 10,
        textStyle: { fontSize: 12 }
      },
      grid: { 
        left: '3%', 
        right: '4%', 
        top: '15%', 
        bottom: '30px', 
        containLabel: true 
      },
      xAxis: { 
        type: 'category', 
        data: data.months,
        axisLabel: { 
          fontSize: 10,
          interval: 'auto',
          hideOverlap: true,
          rotate: 0,
          formatter: function (value) {
              // YYYY-MM -> MM
              if (value && value.length > 5) {
                  return value.substring(5);
              }
              return value;
          }
        }
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
          barMaxWidth: 20
        },
        // Stacked Expense Series
        {
          name: '下游合同',
          type: 'bar',
          stack: 'expense',
          data: data.expense_breakdown.downstream.map(v => (v / 10000).toFixed(2)),
          itemStyle: { color: '#F56C6C' },
          barMaxWidth: 20
        },
        {
          name: '管理合同',
          type: 'bar',
          stack: 'expense',
          data: data.expense_breakdown.management.map(v => (v / 10000).toFixed(2)),
          itemStyle: { color: '#E6A23C' },
          barMaxWidth: 20
        },
        {
          name: '无合同费用',
          type: 'bar',
          stack: 'expense',
          data: data.expense_breakdown.non_contract.map(v => (v / 10000).toFixed(2)),
          itemStyle: { color: '#909399' },
          barMaxWidth: 20
        },
        {
          name: '零星用工',
          type: 'bar',
          stack: 'expense',
          data: data.expense_breakdown.zero_hour_labor.map(v => (v / 10000).toFixed(2)),
          itemStyle: { color: '#A0CFFF' },
          barMaxWidth: 20
        }
      ]
    },
    media: [
      {
        query: { maxWidth: 767 },
        option: {
          legend: {
            itemWidth: 10,
            textStyle: { fontSize: 9 },
            bottom: 0
          },
          grid: {
            bottom: '80px',
          },
          xAxis: {
            axisLabel: {
              fontSize: 9,
              rotate: 45
            }
          }
        }
      }
    ]
  })
}

const initCategoryPie = (data) => {
  if (!pieCategoryChartRef.value) return
  if (pieCategoryChart) pieCategoryChart.dispose()
  
  pieCategoryChart = echarts.init(pieCategoryChartRef.value)
  pieCategoryChart.setOption({
    tooltip: { 
      trigger: 'item',
      formatter: function(params) {
        const wanValue = Math.round(params.value / 10000)
        return `${params.name}: ${wanValue}万元 (${params.percent}%)`
      }
    },
    legend: {
      bottom: 0,
      left: 'center',
      width: '92%',
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 12,
      textStyle: { fontSize: 11, lineHeight: 14 }
    },
    series: [
      {
        name: '合同分类',
        type: 'pie',
        radius: ['35%', '60%'],
        center: ['50%', '42%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 5,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold' }
        },
        labelLine: { show: false },
        data: data
      }
    ]
  })
}

const initCompanyPie = (data) => {
  if (!pieCompanyChartRef.value) return
  if (pieCompanyChart) pieCompanyChart.dispose()
  
  pieCompanyChart = echarts.init(pieCompanyChartRef.value)
  pieCompanyChart.setOption({
    tooltip: { 
      trigger: 'item',
      formatter: function(params) {
        const wanValue = Math.round(params.value / 10000)
        return `${params.name}: ${wanValue}万元 (${params.percent}%)`
      }
    },
    legend: {
      bottom: 0,
      left: 'center',
      width: '92%',
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 12,
      textStyle: { fontSize: 11, lineHeight: 14 }
    },
    series: [
      {
        name: '公司分类',
        type: 'pie',
        radius: ['35%', '60%'],
        center: ['50%', '42%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 5,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold' }
        },
        labelLine: { show: false },
        data: data
      }
    ]
  })
}

const handleResize = () => {
  barChart && barChart.resize()
  pieCategoryChart && pieCategoryChart.resize()
  pieCompanyChart && pieCompanyChart.resize()
  monthChart && monthChart.resize()
  quarterChart && quarterChart.resize()
}

onMounted(() => {
  nextTick(() => {
    fetchData()
    window.addEventListener('resize', handleResize)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  barChart && barChart.dispose()
  pieCategoryChart && pieCategoryChart.dispose()
  pieCompanyChart && pieCompanyChart.dispose()
  monthChart && monthChart.dispose()
  quarterChart && quarterChart.dispose()
})
</script>

<style scoped lang="scss">
/* Dashboard Container */
.dashboard-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 84px);
}

/* Modern Top Cards */
.stat-card-modern {
  border: none;
  border-radius: 12px;
  color: #fff;
  position: relative;
  overflow: hidden;
  height: 140px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 20px;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 20px -8px rgba(0, 0, 0, 0.2);
    
    .card-icon-bg {
      transform: scale(1.1) rotate(10deg);
      opacity: 0.25;
    }
  }

  .card-icon-bg {
    position: absolute;
    right: -20px;
    bottom: -20px;
    font-size: 100px;
    opacity: 0.15;
    transition: all 0.4s ease;
    
    .el-icon {
      color: #fff;
    }
  }

  :deep(.el-card__body) {
    padding: 20px;
    height: 100%;
    box-sizing: border-box;
  }

  .card-inner {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
  }

  .card-modern-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .title {
      font-size: 16px;
      font-weight: 500;
      opacity: 0.9;
    }
    
    .icon-wrapper {
      background: rgba(255, 255, 255, 0.2);
      border-radius: 50%;
      padding: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .el-icon {
        font-size: 18px;
        color: #fff;
      }
    }
  }

  .card-modern-content {
    .amount {
      font-size: 28px;
      margin: 10px 0 5px;
      font-weight: bold;
      line-height: 1.2;
      
      small {
        font-size: 14px;
        font-weight: normal;
        opacity: 0.8;
      }
    }
    
    .amount-sub {
      font-size: 13px;
      opacity: 0.9;
      margin-bottom: 4px;
    }

    .sub-info {
      font-size: 12px;
      opacity: 0.7;
    }
  }
}

/* Modern Period Cards */
.period-card-modern {
  border: none;
  border-radius: 12px;
  margin-bottom: 20px;
  overflow: hidden;
  transition: box-shadow 0.3s;
  
  &:hover {
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
  }
  
  :deep(.el-card__header) {
    padding: 15px 20px;
    border-bottom: 1px solid #f0f2f5;
    background: #fff;
  }
  
  :deep(.el-card__body) {
    padding: 0;
  }

  .card-modern-title-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .title-left {
      display: flex;
      align-items: center;
      font-size: 16px;
      font-weight: bold;
      color: #303133;
      
      .title-icon {
        margin-right: 8px;
        font-size: 18px;
        padding: 6px;
        border-radius: 6px;
        
        &.monthly {
          color: #409EFF;
          background: #ecf5ff;
        }
        
        &.quarterly {
          color: #E6A23C;
          background: #fdf6ec;
        }
      }
    }
  }

  .period-content-wrapper {
     /* display: flex;  Removed flex to allow wrapping on mobile if grid system fails, but el-col handles it */
  }

  .period-content-row {
     /* flex-wrap: wrap; */
  }

  .period-col {
    padding: 20px;
    box-sizing: border-box;
    
    &.left-col {
      background: #fff;
      border-right: 1px dashed #e4e7ed;
    }
    
    &.right-col {
      background: #fdfdfd;
    }
  }

  .section-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
    margin-bottom: 15px;
    
    &.upstream {
      background: #effaf5;
      color: #27ae60;
    }
    
    &.downstream {
      background: #fef0f0;
      color: #e74c3c;
    }
  }

  .stat-modern-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    font-size: 14px;
    color: #606266;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    &.highlight {
      background: #f8f9fa;
      padding: 8px;
      border-radius: 6px;
      margin-bottom: 8px;
    }

    .label {
      opacity: 0.9;
    }

    .value {
      font-weight: bold;
      color: #303133;
      
      small {
        font-size: 12px;
        font-weight: normal;
        color: #909399;
        margin-left: 2px;
      }
      
      &.income { color: #67C23A; }
      &.expense { color: #F56C6C; }
      &.success { color: #52C41A; }
      &.text-gray { color: #909399; }
    }
  }
}

/* Chart Cards */
.chart-card {
  border: none;
  border-radius: 12px;
  margin-bottom: 20px;
  
  :deep(.el-card__header) {
    padding: 15px 20px;
    border-bottom: 1px solid #f0f2f5;
  }
  
  .card-header {
    font-weight: bold;
    font-size: 16px;
    color: #303133;
  }
}

/* Mobile Responsive */
@media only screen and (max-width: 991px) {
  .period-col {
    &.left-col {
      border-right: none !important;
      border-bottom: 1px dashed #e4e7ed;
    }
  }
} 

@media only screen and (max-width: 767px) {
  .stat-card-modern {
    height: 120px !important;
    margin-bottom: 15px !important;
    
    :deep(.el-card__body) {
      padding: 15px !important;
    }

    .card-modern-header {
      .title { font-size: 14px; }
      .icon-wrapper { padding: 4px; .el-icon { font-size: 16px; } }
    }

    .card-modern-content {
      .amount { font-size: 22px; margin: 5px 0; }
      .amount-sub { font-size: 12px; }
      .sub-info { display: none; }
    }
    
    .card-icon-bg { font-size: 60px; right: -10px; bottom: -10px; }
  }
  
  .period-card-modern {
    margin-bottom: 15px;
    
    :deep(.el-card__header) {
       padding: 10px 12px;
    }
    
    .card-modern-title-bar {
       .title-left { font-size: 14px; }
    }
    
    .period-col {
       padding: 15px;
    }
  }
}
</style>
