<template>
  <div class="dashboard-container">
    <!-- Top Cards -->
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :lg="6" v-for="item in cardData" :key="item.title">
        <el-card shadow="hover" class="stat-card" :style="{ borderTopColor: item.color }">
          <template #header>
            <div class="card-header">
              <span>{{ item.title }}</span>
              <el-tag :color="item.color" effect="dark" style="border:none">{{ item.tag }}</el-tag>
            </div>
          </template>
          <div class="card-content">
            <h2 class="amount" :style="{ color: item.color }">
              <template v-if="item.count !== undefined">
                {{ item.count }} 单 / ¥ {{ formatWan(item.value) }} 万元
              </template>
              <template v-else>
                ¥ {{ formatWan(item.value) }} 万元
              </template>
            </h2>
            <div class="sub-info">{{ item.subInfo }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
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
            <el-col :span="12">
               <div style="text-align: center; font-size: 12px; font-weight: bold; margin-bottom: 5px;">合同类别</div>
               <div ref="pieCategoryChartRef" style="height: 320px; width: 100%;"></div>
            </el-col>
            <el-col :span="12">
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
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getStats } from '@/api/dashboard'
import { getFinanceTrend } from '@/api/reports'
import { ElMessage } from 'element-plus'

const barChartRef = ref(null)
const pieCategoryChartRef = ref(null)
const pieCompanyChartRef = ref(null)
let barChart = null
let pieCategoryChart = null
let pieCompanyChart = null
const currentYear = new Date().getFullYear().toString()

const cardData = ref([
  { title: '年度上游签约合计', value: 0, count: 0, tag: '总览', color: '#1890FF', subInfo: '' },
  { title: '年度下游签约合计', value: 0, count: 0, tag: '成本', color: '#FAAD14', subInfo: '' },
  { title: '年度回款', value: 0, tag: '收入', color: '#52C41A', subInfo: '本年度上游合同回款' },
  { title: '年度付款', value: 0, tag: '支出', color: '#FF4D4F', subInfo: '下游+管理+无合同费用' },
])

const formatCurrency = (val) => {
  if (!val) return '0.00'
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatWan = (val) => {
  if (!val) return '0.00'
  return (Number(val) / 10000).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const fetchData = async () => {
  try {
    const [statsRes, trendRes] = await Promise.all([
      getStats(),
      getFinanceTrend(currentYear)
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
    
    // Init Charts
    initTrendChart(trendRes)
    if (charts.pie_category) initCategoryPie(charts.pie_category)
    if (charts.pie_company) initCompanyPie(charts.pie_company)
  } catch (error) {
    console.error(error)
    ElMessage.error('获取仪表盘数据失败')
  }
}

const initTrendChart = (data) => {
  if (!barChartRef.value) return
  if (barChart) barChart.dispose()
  
  barChart = echarts.init(barChartRef.value)
  barChart.setOption({
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
    legend: { bottom: 0, left: 'center' },
    series: [
      {
        name: '合同分类',
        type: 'pie',
        radius: ['35%', '60%'],
        center: ['50%', '45%'],
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
    legend: { bottom: 0, left: 'center' },
    series: [
      {
        name: '公司分类',
        type: 'pie',
        radius: ['35%', '60%'],
        center: ['50%', '45%'],
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
})
</script>

<style scoped lang="scss">
.stat-card {
  border-top: 3px solid transparent; /* Color set dynamically */
  margin-bottom: 20px;
  height: 180px;

  .card-content {
    margin-top: 10px;
    
    .amount {
      font-size: 20px;
      margin-bottom: 8px;
      margin-top: 0;
      font-weight: bold;
    }
    
    .sub-info {
      font-size: 12px;
      color: #909399;
    }
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.chart-card {
  margin-bottom: 20px;
}
</style>
