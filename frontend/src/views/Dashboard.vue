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
              ¥ {{ formatCurrency(item.value) }}
            </h2>
            <div class="sub-info">{{ item.subInfo }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- Charts Section -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- Bar Chart: Income vs Expense -->
      <el-col :xs="24" :lg="16">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>收支趋势 (本年度)</span>
            </div>
          </template>
          <div ref="barChartRef" style="height: 350px; width: 100%;"></div>
        </el-card>
      </el-col>
      
      <!-- Pie Chart: Contract Categories -->
      <el-col :xs="24" :lg="8">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>合同分类分布</span>
            </div>
          </template>
          <div ref="pieChartRef" style="height: 350px; width: 100%;"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getStats } from '@/api/dashboard'
import { ElMessage } from 'element-plus'

const barChartRef = ref(null)
const pieChartRef = ref(null)
let barChart = null
let pieChart = null

const cardData = ref([
  { title: '上游合同总额', value: 0, tag: '总览', color: '#1890FF', subInfo: '所有甲方合同总金额' },
  { title: '实际已收款', value: 0, tag: '收入', color: '#52C41A', subInfo: '所有已确认到账款项' },
  { title: '总支出', value: 0, tag: '支出', color: '#FF4D4F', subInfo: '下游付款 + 非合同费用' },
  { title: '下游合同总额', value: 0, tag: '成本', color: '#FAAD14', subInfo: '所有分包/采购合同' },
])

const formatCurrency = (val) => {
  if (!val) return '0.00'
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const fetchData = async () => {
  try {
    const res = await getStats()
    const { cards, charts } = res
    
    // Update Cards
    cardData.value[0].value = cards.total_contract_amount
    cardData.value[1].value = cards.total_received
    cardData.value[2].value = cards.total_paid
    cardData.value[3].value = cards.total_down_contract_amount
    
    // Init Charts
    initBarChart(charts.bar)
    initPieChart(charts.pie)
  } catch (error) {
    console.error(error)
    ElMessage.error('获取仪表盘数据失败')
  }
}

const initBarChart = (data) => {
  if (!barChartRef.value) return
  if (barChart) barChart.dispose()
  
  barChart = echarts.init(barChartRef.value)
  barChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['收入', '支出'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: data.categories },
    yAxis: { type: 'value' },
    series: [
      {
        name: '收入',
        type: 'bar',
        data: data.income,
        itemStyle: { color: '#52C41A' }
      },
      {
        name: '支出',
        type: 'bar',
        data: data.expense,
        itemStyle: { color: '#FF4D4F' }
      }
    ]
  })
}

const initPieChart = (data) => {
  if (!pieChartRef.value) return
  if (pieChart) pieChart.dispose()
  
  pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { top: '5%', left: 'center' },
    series: [
      {
        name: '合同分类',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 20, fontWeight: 'bold' }
        },
        labelLine: { show: false },
        data: data
      }
    ]
  })
}

const handleResize = () => {
  barChart && barChart.resize()
  pieChart && pieChart.resize()
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
  pieChart && pieChart.dispose()
})
</script>

<style scoped lang="scss">
.stat-card {
  border-top: 3px solid transparent; /* Color set dynamically */
  margin-bottom: 20px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 500;
  }
  
  .card-content {
    margin-top: 10px;
    
    .amount {
      font-size: 24px;
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

.chart-card {
  margin-bottom: 20px;
}
</style>
