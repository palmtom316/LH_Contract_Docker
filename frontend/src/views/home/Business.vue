<template>
  <div class="business-dashboard" v-loading="loading">
    <!-- Header / Filter -->
    <div class="filter-container">
      <span class="filter-label">统计周期:</span>

      <!-- Year Picker -->
      <el-date-picker
        v-model="currentYear"
        type="year"
        placeholder="选择年份"
        style="width: 120px; margin-right: 10px"
        value-format="YYYY"
        @change="handleFilterChange"
      />

      <!-- Month Selector -->
      <el-select
        v-model="currentMonth"
        placeholder="选择月份 (默认全年)"
        clearable
        style="width: 180px; margin-right: 10px"
        @change="handleFilterChange"
      >
        <el-option label="全年数据" :value="null" />
        <el-option v-for="m in 12" :key="m" :label="m + '月'" :value="m" />
      </el-select>

      <el-button type="primary" icon="Refresh" @click="fetchData"
        >查询</el-button
      >
    </div>

    <!-- Row 1: Annual Summary Cards (4 Cards) -->
    <el-row :gutter="20" class="summary-row">
      <!-- 1. Annual Upstream Contract Total -->
      <el-col :xs="12" :sm="12" :md="6">
        <el-card
          shadow="hover"
          class="stat-card-modern"
          style="background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%)"
        >
          <div class="card-icon-bg">
            <el-icon><Document /></el-icon>
          </div>
          <div class="card-inner">
            <div class="card-modern-header">
              <span class="title">年度上游合同签约</span>
              <div class="icon-wrapper">
                <el-icon><Document /></el-icon>
              </div>
            </div>
            <div class="card-modern-content">
              <h2 class="amount">
                {{ annualUpstreamCount }} <small>单</small>
              </h2>
              <div class="amount-sub">
                ¥ {{ formatWan(annualUpstreamAmount) }} 万
              </div>
              <div class="sub-info">累计签约总额</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 2. Annual Receipts Total -->
      <el-col :xs="12" :sm="12" :md="6">
        <el-card
          shadow="hover"
          class="stat-card-modern"
          style="background: linear-gradient(135deg, #52c41a 0%, #95d475 100%)"
        >
          <div class="card-icon-bg">
            <el-icon><Money /></el-icon>
          </div>
          <div class="card-inner">
            <div class="card-modern-header">
              <span class="title">年度回款总额</span>
              <div class="icon-wrapper">
                <el-icon><Money /></el-icon>
              </div>
            </div>
            <div class="card-modern-content">
              <h2 class="amount">
                ¥ {{ formatWan(annualReceiptsAmount) }} <small>万</small>
              </h2>
              <div class="sub-info">实际到账金额</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 3. Annual Payments Total -->
      <el-col :xs="12" :sm="12" :md="6">
        <el-card
          shadow="hover"
          class="stat-card-modern"
          style="background: linear-gradient(135deg, #ff4d4f 0%, #f56c6c 100%)"
        >
          <div class="card-icon-bg">
            <el-icon><Coin /></el-icon>
          </div>
          <div class="card-inner">
            <div class="card-modern-header">
              <span class="title">年度付款总额</span>
              <div class="icon-wrapper">
                <el-icon><Coin /></el-icon>
              </div>
            </div>
            <div class="card-modern-content">
              <h2 class="amount">
                ¥ {{ formatWan(annualPaymentsAmount) }} <small>万</small>
              </h2>
              <div class="sub-info">下游+管理+无合同费用+零星用工</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 4. Annual Downstream & Management Contract Total -->
      <el-col :xs="12" :sm="12" :md="6">
        <el-card
          shadow="hover"
          class="stat-card-modern"
          style="background: linear-gradient(135deg, #faad14 0%, #fadb14 100%)"
        >
          <div class="card-icon-bg">
            <el-icon><Wallet /></el-icon>
          </div>
          <div class="card-inner">
            <div class="card-modern-header">
              <span class="title">年度下游及管理签约</span>
              <div class="icon-wrapper">
                <el-icon><Wallet /></el-icon>
              </div>
            </div>
            <div class="card-modern-content">
              <h2 class="amount">
                {{ annualDownMgmtCount }} <small>单</small>
              </h2>
              <div class="amount-sub">
                ¥ {{ formatWan(annualDownMgmtAmount) }} 万
              </div>
              <div class="sub-info">累计支出预算</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 2: Trend Chart (Wide) + AR + AP -->
    <el-row :gutter="20" style="margin-top: 20px" class="summary-row">
      <!-- Trend Chart (Takes 12 columns = 2 cards width) -->
      <el-col :xs="24" :sm="24" :md="12">
        <el-card
          shadow="hover"
          class="chart-card"
          style="height: 228px; display: flex; flex-direction: column"
          :body-style="{
            flex: '1',
            overflow: 'hidden',
            padding: '10px',
            display: 'flex',
            flexDirection: 'column',
          }"
        >
          <div
            class="card-content"
            style="
              flex: 1;
              display: flex;
              flex-direction: column;
              overflow: hidden;
            "
          >
            <div
              class="card-header-simple"
              style="margin-bottom: 5px; flex-shrink: 0"
            >
              <span>{{ currentYear }}年度 收支趋势</span>
              <el-tag
                v-if="currentMonth"
                type="warning"
                size="small"
                style="margin-left: 10px; transform: scale(0.8)"
              >
                {{ currentMonth }}月
              </el-tag>
            </div>
            <!-- Chart Container -->
            <div
              ref="trendChartRef"
              style="width: 100%; flex: 1; min-height: 0"
            ></div>
          </div>
        </el-card>
      </el-col>

      <!-- Receivables -->
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="chart-card" style="height: 228px">
          <template #header>
            <div class="card-header-simple">
              <span
                >{{ currentMonth ? `${currentMonth}月 ` : "" }}应收账款
                (AR)</span
              >
              <el-tooltip content="统计周期内应收款 vs 已收款" placement="top">
                <el-icon><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <div class="arap-content">
            <div class="arap-main-value text-primary">
              ¥ {{ formatWan(arStats.outstanding) }} <small>万</small>
            </div>
            <div class="arap-sub">
              <div class="sub-row">
                <span class="label">应收款</span
                ><span class="val"
                  >¥ {{ formatWan(arStats.total_receivable) }} 万</span
                >
              </div>
              <div class="sub-row">
                <span class="label">已收款</span
                ><span class="val text-success"
                  >¥ {{ formatWan(arStats.total_received) }} 万</span
                >
              </div>
            </div>
            <el-progress
              :percentage="
                calcPercentage(arStats.total_received, arStats.total_receivable)
              "
              status="success"
              :stroke-width="10"
              class="ar-progress"
            >
              <template #default="{ percentage }">
                <span style="font-size: 12px; color: #606266"
                  >{{ percentage }}%</span
                >
              </template>
            </el-progress>
          </div>
        </el-card>
      </el-col>

      <!-- Payables -->
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="chart-card" style="height: 228px">
          <template #header>
            <div class="card-header-simple">
              <span
                >{{ currentMonth ? `${currentMonth}月 ` : "" }}应付账款
                (AP)</span
              >
              <el-tooltip content="统计周期内应付款 vs 已付款" placement="top">
                <el-icon><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <div class="arap-content">
            <div class="arap-main-value text-warning">
              ¥ {{ formatWan(apStats.outstanding) }} <small>万</small>
            </div>
            <div class="arap-sub">
              <div class="sub-row">
                <span class="label">应付款</span
                ><span class="val"
                  >¥ {{ formatWan(apStats.total_payable) }} 万</span
                >
              </div>
              <div class="sub-row">
                <span class="label">已付款</span
                ><span class="val text-success"
                  >¥ {{ formatWan(apStats.total_paid) }} 万</span
                >
              </div>
            </div>
            <el-progress
              :percentage="
                calcPercentage(apStats.total_paid, apStats.total_payable)
              "
              status="success"
              :stroke-width="10"
              class="ap-progress"
            >
              <template #default="{ percentage }">
                <span style="font-size: 12px; color: #606266"
                  >{{ percentage }}%</span
                >
              </template>
            </el-progress>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 2: Contract Summaries (5 Cards) -->
    <el-row :gutter="20" style="margin-top: 20px" class="summary-card-row">
      <!-- 1. Upstream Contracts (Category) -->
      <el-col :xs="24" :sm="12" class="stat-col-5">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header-simple">
              <span
                >{{
                  currentMonth ? `${currentMonth}月 ` : ""
                }}上游概况(类别)</span
              >
              <el-tag effect="plain" type="primary">
                {{ upstreamSummary.reduce((acc, cur) => acc + cur.count, 0) }}
                单 / ¥{{
                  formatWan(
                    upstreamSummary.reduce((acc, cur) => acc + cur.amount, 0)
                  )
                }}
                万
              </el-tag>
            </div>
          </template>
          <div class="card-list-modern">
            <div
              v-for="item in upstreamSummary.slice(0, 20)"
              :key="item.name"
              class="list-item"
            >
              <span class="item-name">{{ item.name }}</span>
              <span class="item-value"
                >{{ item.count }}单 / ¥{{ formatWan(item.amount) }}万</span
              >
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 2. Upstream Contracts (Company Category) -->
      <el-col :xs="24" :sm="12" class="stat-col-5">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header-simple">
              <span
                >{{
                  currentMonth ? `${currentMonth}月 ` : ""
                }}上游概况(公司)</span
              >
              <el-tag
                effect="plain"
                type="primary"
                color="#f3e5f5"
                style="color: #8e44ad; border-color: #d7bde2"
              >
                {{
                  upstreamCompanySummary.reduce(
                    (acc, cur) => acc + cur.count,
                    0
                  )
                }}
                单 / ¥{{
                  formatWan(
                    upstreamCompanySummary.reduce(
                      (acc, cur) => acc + cur.amount,
                      0
                    )
                  )
                }}
                万
              </el-tag>
            </div>
          </template>
          <div class="card-list-modern">
            <div
              v-for="item in upstreamCompanySummary.slice(0, 20)"
              :key="item.name"
              class="list-item"
            >
              <span class="item-name">{{ item.name }}</span>
              <span class="item-value"
                >{{ item.count }}单 / ¥{{ formatWan(item.amount) }}万</span
              >
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 3. Downstream Contracts Summary -->
      <el-col :xs="24" :sm="12" class="stat-col-5">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header-simple">
              <span
                >{{
                  currentMonth ? `${currentMonth}月 ` : ""
                }}下游合同概况</span
              >
              <el-tag effect="plain" type="danger">
                {{ downstreamSummary.reduce((acc, cur) => acc + cur.count, 0) }}
                单 / ¥{{
                  formatWan(
                    downstreamSummary.reduce((acc, cur) => acc + cur.amount, 0)
                  )
                }}
                万
              </el-tag>
            </div>
          </template>
          <div class="card-list-modern">
            <div
              v-for="item in downstreamSummary.slice(0, 20)"
              :key="item.name"
              class="list-item"
            >
              <span class="item-name">{{ item.name }}</span>
              <span class="item-value"
                >{{ item.count }}单 / ¥{{ formatWan(item.amount) }}万</span
              >
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 4. Management Contracts Summary -->
      <el-col :xs="24" :sm="12" class="stat-col-5">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header-simple">
              <span
                >{{
                  currentMonth ? `${currentMonth}月 ` : ""
                }}管理合同概况</span
              >
              <el-tag effect="plain" type="warning">
                {{ managementSummary.reduce((acc, cur) => acc + cur.count, 0) }}
                单 / ¥{{
                  formatWan(
                    managementSummary.reduce((acc, cur) => acc + cur.amount, 0)
                  )
                }}
                万
              </el-tag>
            </div>
          </template>
          <div class="card-list-modern">
            <div
              v-for="item in managementSummary.slice(0, 20)"
              :key="item.name"
              class="list-item"
            >
              <span class="item-name">{{ item.name }}</span>
              <span class="item-value"
                >{{ item.count }}单 / ¥{{ formatWan(item.amount) }}万</span
              >
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 5. Non-Contract Expenses Summary -->
      <el-col :xs="24" :sm="24" :md="24" class="stat-col-5">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header-simple">
              <span
                >{{ currentMonth ? `${currentMonth}月 ` : "" }}无合同费用</span
              >
              <el-tag effect="plain" type="info">
                {{ expenseSummary.reduce((acc, cur) => acc + cur.count, 0) }} 笔
                / ¥{{
                  formatWan(
                    expenseSummary.reduce((acc, cur) => acc + cur.value, 0)
                  )
                }}
                万
              </el-tag>
            </div>
          </template>
          <div class="card-list-modern expense-grid">
            <div
              v-for="item in expenseSummary.slice(0, 20)"
              :key="item.name"
              class="list-item"
            >
              <span class="item-name">{{ item.name }}</span>
              <span class="item-value"
                >{{ item.count }}笔 / ¥{{ formatWan(item.value) }}万</span
              >
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 3: Pie Charts (4 Charts) -->
    <el-row :gutter="20" style="margin-top: 20px">
      <!-- Upstream Categories Pie -->
      <el-col :xs="24" :md="6">
        <el-card shadow="hover" style="height: 300px">
          <template #header
            ><span style="font-size: 12px; font-weight: bold"
              >上游合同分类</span
            ></template
          >
          <div ref="upstreamPieRef" style="height: 200px; width: 100%"></div>
        </el-card>
      </el-col>

      <!-- Upstream Company Categories Pie (New) -->
      <el-col :xs="24" :md="6">
        <el-card shadow="hover" style="height: 300px">
          <template #header
            ><span style="font-size: 12px; font-weight: bold"
              >上游合同公司分类</span
            ></template
          >
          <div
            ref="upstreamCompanyPieRef"
            style="height: 200px; width: 100%"
          ></div>
        </el-card>
      </el-col>

      <!-- Expense Breakdown Pie -->
      <el-col :xs="24" :md="6">
        <el-card shadow="hover" style="height: 300px">
          <template #header
            ><span style="font-size: 12px; font-weight: bold"
              >支出构成</span
            ></template
          >
          <div
            ref="expenseStructPieRef"
            style="height: 200px; width: 100%"
          ></div>
        </el-card>
      </el-col>

      <!-- Non-Contract Expense Categories Pie -->
      <el-col :xs="24" :md="6">
        <el-card shadow="hover" style="height: 300px">
          <template #header
            ><span style="font-size: 12px; font-weight: bold"
              >无合同费用分类</span
            ></template
          >
          <div ref="expenseCatPieRef" style="height: 200px; width: 100%"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import {
  ref,
  onMounted,
  onBeforeUnmount,
  nextTick,
  reactive,
  watch,
} from "vue";
import echarts from "@/utils/echarts";
import {
  getContractSummary,
  getFinanceTrend,
  getExpenseBreakdown,
  getArApStats,
} from "@/api/reports";
import { ElMessage } from "element-plus";
import {
  Document,
  Money,
  Wallet,
  Coin,
  TrendCharts,
  DataAnalysis,
  InfoFilled,
  Refresh,
} from "@element-plus/icons-vue";

// State
const loading = ref(false);
const currentYear = ref(new Date().getFullYear().toString());
const currentMonth = ref(null); // null means full year

// Data storage
const arStats = reactive({
  total_receivable: 0,
  total_received: 0,
  outstanding: 0,
});
const apStats = reactive({ total_payable: 0, total_paid: 0, outstanding: 0 });
const upstreamSummary = ref([]);
const upstreamCompanySummary = ref([]);
const downstreamSummary = ref([]);
const managementSummary = ref([]);
const expenseSummary = ref([]);
const zeroHourLaborSummary = reactive({ count: 0, total: 0 });

// Annual Summary Data (for Row 1 cards)
const annualUpstreamCount = ref(0);
const annualUpstreamAmount = ref(0);
const annualReceiptsAmount = ref(0);
const annualPaymentsAmount = ref(0);
const annualDownMgmtCount = ref(0);
const annualDownMgmtAmount = ref(0);

// Chart Refs
const trendChartRef = ref(null);
const upstreamPieRef = ref(null);
const upstreamCompanyPieRef = ref(null);
const expenseStructPieRef = ref(null);
const expenseCatPieRef = ref(null);

let trendChart = null;
let upstreamPieChart = null;
let upstreamCompanyPieChart = null;
let expenseStructChart = null;
let expenseCatChart = null;

// Methods
const formatWan = (val) => {
  if (!val) return "0.00";
  return (Number(val) / 10000).toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

const calcPercentage = (num, total) => {
  if (!total || total === 0) return 0;
  const p = (num / total) * 100;
  return Number(p.toFixed(2)); // Return value for display, el-progress handles clamping
};

const fetchData = async () => {
  loading.value = true;
  try {
    const year = currentYear.value;
    const month = currentMonth.value || undefined;

    // Parallel requests
    const [summaryRes, trendRes, expenseRes, arApRes] = await Promise.all([
      getContractSummary(year, month),
      getFinanceTrend(year, month),
      getExpenseBreakdown(year, month),
      getArApStats(year, month),
    ]);

    // 1. Process AR/AP
    Object.assign(arStats, arApRes.ar);
    Object.assign(apStats, arApRes.ap);

    // 2. Process Contract Summary
    upstreamSummary.value = summaryRes.upstream_by_category;
    upstreamCompanySummary.value =
      summaryRes.upstream_by_company_category || [];
    downstreamSummary.value = summaryRes.downstream_by_category;
    managementSummary.value = summaryRes.management_by_category || [];
    expenseSummary.value = expenseRes.non_contract_breakdown || []; // Used for summary card

    // Zero Hour Labor Summary
    if (expenseRes.zero_hour_labor) {
      zeroHourLaborSummary.count = expenseRes.zero_hour_labor.count || 0;
      zeroHourLaborSummary.total = expenseRes.zero_hour_labor.total || 0;
    }

    // 3. Calculate Annual Summary Statistics (for Row 1 cards)
    // Annual Upstream: count and amount
    annualUpstreamCount.value = upstreamSummary.value.reduce(
      (acc, cur) => acc + cur.count,
      0
    );
    annualUpstreamAmount.value = upstreamSummary.value.reduce(
      (acc, cur) => acc + cur.amount,
      0
    );

    // Annual Receipts: total received amount from AR stats
    annualReceiptsAmount.value = arApRes.ar.total_received;

    // Annual Payments: total paid from AP stats (includes downstream + management + non-contract + zero hour labor)
    annualPaymentsAmount.value = arApRes.ap.total_paid;

    // Annual Downstream + Management: count and amount
    const downCount = downstreamSummary.value.reduce(
      (acc, cur) => acc + cur.count,
      0
    );
    const downAmount = downstreamSummary.value.reduce(
      (acc, cur) => acc + cur.amount,
      0
    );
    const mgmtCount = managementSummary.value.reduce(
      (acc, cur) => acc + cur.count,
      0
    );
    const mgmtAmount = managementSummary.value.reduce(
      (acc, cur) => acc + cur.amount,
      0
    );
    annualDownMgmtCount.value = downCount + mgmtCount;
    annualDownMgmtAmount.value = downAmount + mgmtAmount;

    // 4. Update Charts
    initTrendChart(trendRes);
    initUpstreamPie(summaryRes.upstream_by_category);
    initUpstreamCompanyPie(summaryRes.upstream_by_company_category || []);
    initExpenseStructPie(expenseRes.overall_breakdown);
    initExpenseCatPie(expenseRes.non_contract_breakdown);
  } catch (error) {
    console.error(error);
    ElMessage.error("获取报表数据失败");
  } finally {
    loading.value = false;
  }
};

const handleFilterChange = () => {
  fetchData();
};

// Chart Initializers
const initTrendChart = (data) => {
  if (!trendChartRef.value) return;
  if (trendChart) trendChart.dispose();

  trendChart = echarts.init(trendChartRef.value);
  trendChart.setOption({
    baseOption: {
      tooltip: {
        confine: true,
        trigger: "axis",
        formatter: function (params) {
          let res = params[0].name + "<br/>";
          params.forEach((item) => {
            res +=
              item.marker +
              item.seriesName +
              ": " +
              Number(item.value).toFixed(2) +
              " 万元<br/>";
          });
          return res;
        },
      },
      legend: {
        data: ["月度收入", "下游合同", "管理合同", "无合同费用"],
        bottom: 0,
        itemWidth: 15,
        itemHeight: 10,
        textStyle: { fontSize: 10 },
      },
      grid: {
        left: "3%",
        right: "4%",
        top: "15%",
        bottom: "30px",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        data: data.months,
        axisLabel: { interval: 0, fontSize: 10 },
      },
      yAxis: {
        type: "value",
        name: "金额 (万元)",
        splitLine: { show: false },
      },
      series: [
        {
          name: "月度收入",
          type: "bar",
          data: data.income.map((v) => (v / 10000).toFixed(2)),
          itemStyle: { color: "#67C23A" },
          barMaxWidth: 15,
        },
        // Stacked Expense Series
        {
          name: "下游合同",
          type: "bar",
          stack: "expense",
          data: data.expense_breakdown.downstream.map((v) =>
            (v / 10000).toFixed(2)
          ),
          itemStyle: { color: "#F56C6C" },
          barMaxWidth: 15,
        },
        {
          name: "管理合同",
          type: "bar",
          stack: "expense",
          data: data.expense_breakdown.management.map((v) =>
            (v / 10000).toFixed(2)
          ),
          itemStyle: { color: "#E6A23C" },
          barMaxWidth: 15,
        },
        {
          name: "无合同费用",
          type: "bar",
          stack: "expense",
          data: data.expense_breakdown.non_contract.map((v) =>
            (v / 10000).toFixed(2)
          ),
          itemStyle: { color: "#909399" },
          barMaxWidth: 15,
        },
      ],
    },
    media: [
      {
        query: { maxWidth: 767 },
        option: {
          legend: {
            itemWidth: 10,
            textStyle: { fontSize: 9 },
            bottom: 0,
          },
          grid: {
            bottom: "80px",
          },
          xAxis: {
            axisLabel: {
              fontSize: 9,
              rotate: 45,
            },
          },
        },
      },
    ],
  });
  trendChart.resize();
};

const initUpstreamPie = (data) => {
  if (!upstreamPieRef.value) return;
  if (upstreamPieChart) upstreamPieChart.dispose();

  // Format for pie: { value, name }
  const pieData = data.map((item) => ({ value: item.amount, name: item.name }));

  upstreamPieChart = echarts.init(upstreamPieRef.value);
  upstreamPieChart.setOption({
    tooltip: {
      confine: true,
      trigger: "item",
      formatter: function (params) {
        const wanValue = Math.round(params.value / 10000);
        return `${params.name}: ${wanValue}万元 (${params.percent}%)`;
      },
    },
    legend: { type: "scroll", bottom: 0, pageButtonGap: 5 },
    series: [
      {
        name: "上游合同分类",
        type: "pie",
        radius: ["35%", "60%"], // Smaller radius
        center: ["50%", "42%"], // Move up slightly
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 5,
          borderColor: "#fff",
          borderWidth: 2,
        },
        label: {
          show: false,
          position: "center",
        },
        emphasis: {
          label: {
            show: true,
            fontSize: "12",
            fontWeight: "bold",
          },
        },
        labelLine: { show: false },
        data: pieData.length > 0 ? pieData : [{ value: 0, name: "暂无数据" }],
      },
    ],
  });
};

const initUpstreamCompanyPie = (data) => {
  if (!upstreamCompanyPieRef.value) return;
  if (upstreamCompanyPieChart) upstreamCompanyPieChart.dispose();

  // Format for pie: { value, name }
  const pieData = data.map((item) => ({ value: item.amount, name: item.name }));

  upstreamCompanyPieChart = echarts.init(upstreamCompanyPieRef.value);
  upstreamCompanyPieChart.setOption({
    tooltip: {
      confine: true,
      trigger: "item",
      formatter: function (params) {
        const wanValue = Math.round(params.value / 10000);
        return `${params.name}: ${wanValue}万元 (${params.percent}%)`;
      },
    },
    legend: { type: "scroll", bottom: 0, pageButtonGap: 5 },
    series: [
      {
        name: "上游合同公司分类",
        type: "pie",
        radius: ["35%", "60%"], // Smaller radius
        center: ["50%", "42%"], // Move up slightly
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 5,
          borderColor: "#fff",
          borderWidth: 2,
        },
        label: {
          show: false,
          position: "center",
        },
        emphasis: {
          label: {
            show: true,
            fontSize: "12",
            fontWeight: "bold",
          },
        },
        labelLine: { show: false },
        data: pieData.length > 0 ? pieData : [{ value: 0, name: "暂无数据" }],
      },
    ],
  });
};

const initExpenseStructPie = (data) => {
  if (!expenseStructPieRef.value) return;
  if (expenseStructChart) expenseStructChart.dispose();

  // Check empty
  const hasData = data.some((d) => d.value > 0);

  expenseStructChart = echarts.init(expenseStructPieRef.value);
  expenseStructChart.setOption({
    tooltip: {
      confine: true,
      trigger: "item",
      formatter: function (params) {
        const wanValue = Math.round(params.value / 10000);
        return `${params.name}: ${wanValue}万元 (${params.percent}%)`;
      },
    },
    legend: { bottom: "0%" },
    series: [
      {
        name: "支出构成",
        type: "pie",
        radius: "60%",
        center: ["50%", "45%"],
        data: hasData ? data : [{ value: 0, name: "暂无数据" }],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: "rgba(0, 0, 0, 0.5)",
          },
        },
      },
    ],
  });
};

const initExpenseCatPie = (data) => {
  if (!expenseCatPieRef.value) return;
  if (expenseCatChart) expenseCatChart.dispose();

  const hasData = data.some((d) => d.value > 0);

  expenseCatChart = echarts.init(expenseCatPieRef.value);
  expenseCatChart.setOption({
    tooltip: {
      confine: true,
      trigger: "item",
      formatter: function (params) {
        const wanValue = Math.round(params.value / 10000);
        return `${params.name}: ${wanValue}万元 (${params.percent}%)`;
      },
    },
    legend: { type: "scroll", bottom: "0%" },
    series: [
      {
        name: "无合同费用分类",
        type: "pie",
        radius: ["30%", "60%"],
        center: ["50%", "45%"],
        roseType: "area", // Rose chart for variety
        data: hasData ? data : [{ value: 0, name: "暂无数据" }],
        itemStyle: { borderRadius: 5 },
      },
    ],
  });
};

const handleResize = () => {
  trendChart && trendChart.resize();
  upstreamPieChart && upstreamPieChart.resize();
  upstreamCompanyPieChart && upstreamCompanyPieChart.resize();
  expenseStructChart && expenseStructChart.resize();
  expenseCatChart && expenseCatChart.resize();
};

onMounted(() => {
  nextTick(() => {
    fetchData();
    window.addEventListener("resize", handleResize);
  });
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  trendChart && trendChart.dispose();
  upstreamPieChart && upstreamPieChart.dispose();
  upstreamCompanyPieChart && upstreamCompanyPieChart.dispose();
  expenseStructChart && expenseStructChart.dispose();
  expenseCatChart && expenseCatChart.dispose();
});
</script>

<style scoped lang="scss">
.filter-container {
  background-color: #fff;
  padding: 15px;
  margin-bottom: 20px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;

  .filter-label {
    font-weight: bold;
    color: #606266;
    margin-right: 10px;
    font-size: 14px;
  }
}

/* Modern Top Cards */
.stat-card-modern {
  border: none;
  border-radius: 12px;
  color: #fff;
  position: relative;
  overflow: hidden;
  height: 160px;
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
    padding: 24px;
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
    margin-bottom: 15px;

    .title {
      font-size: 16px;
      font-weight: 500;
      opacity: 0.95;
    }

    .icon-wrapper {
      background: rgba(255, 255, 255, 0.2);
      border-radius: 50%;
      padding: 8px;
      display: flex;
      align-items: center;
      justify-content: center;

      .el-icon {
        font-size: 20px;
        color: #fff;
      }
    }
  }

  .card-modern-content {
    .amount {
      font-size: 32px;
      margin: 0 0 8px;
      font-weight: bold;
      line-height: 1.2;

      small {
        font-size: 16px;
        font-weight: normal;
        opacity: 0.8;
      }
    }

    .amount-sub {
      font-size: 15px;
      opacity: 0.95;
      font-weight: 500;
      margin-bottom: 4px;
    }

    .sub-info {
      font-size: 12px;
      opacity: 0.7;
    }
  }
}

/* Chart Cards */
.chart-card {
  border: none;
  border-radius: 12px;
  margin-bottom: 20px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s;

  &:hover {
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
  }

  :deep(.el-card__header) {
    padding: 15px 20px;
    border-bottom: 1px solid #f0f2f5;
    background: #fff;
  }
}

.card-header-simple {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 15px;
  color: #303133;
}

/* Card Lists */
.card-list-modern {
  padding: 5px 0;

  .list-item {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    font-size: 13px;
    color: #606266;
    border-bottom: 1px dashed #ebeef5;
    transition: background-color 0.2s;

    &:hover {
      background-color: #f5f7fa;
      padding-left: 5px;
      padding-right: 5px;
      border-radius: 4px;
    }

    &:last-child {
      border-bottom: none;
    }

    .item-name {
      flex: 1;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
      margin-right: 15px;
    }

    .item-value {
      font-weight: 500;
      color: #303133;
    }
  }
}

/* Non-contract expense grid (4-6 columns on wide screens) */
.expense-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px 12px;
  padding: 10px 0 5px;

  .list-item {
    flex-direction: column;
    align-items: flex-start;
    justify-content: flex-start;
    border: 1px dashed #ebeef5;
    border-radius: 6px;
    border-bottom: none;
    padding: 8px 10px;
    margin: 0;

    &:hover {
      padding-left: 10px;
      padding-right: 10px;
    }

    .item-name {
      margin: 0 0 4px 0;
      font-weight: 500;
    }

    .item-value {
      font-size: 12px;
      color: #606266;
    }
  }
}

@media only screen and (min-width: 1400px) {
  .expense-grid {
    grid-template-columns: repeat(5, minmax(0, 1fr));
  }
}

@media only screen and (min-width: 1700px) {
  .expense-grid {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }
}

@media only screen and (max-width: 1100px) {
  .expense-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media only screen and (max-width: 800px) {
  .expense-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media only screen and (max-width: 560px) {
  .expense-grid {
    grid-template-columns: 1fr;
  }
}

/* AR/AP Content */
.arap-content {
  padding: 10px 0;

  .arap-main-value {
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 15px;
    text-align: center;

    small {
      font-size: 14px;
      font-weight: normal;
      color: #909399;
    }
  }

  .arap-sub {
    margin-bottom: 15px;
    background: #f8f9fa;
    padding: 12px;
    border-radius: 8px;

    .sub-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 5px;
      font-size: 13px;

      &:last-child {
        margin-bottom: 0;
      }

      .label {
        color: #909399;
      }

      .val {
        font-weight: bold;
        color: #303133;
      }
    }
  }
}

/* Text Colors */
.text-primary {
  color: #409eff;
}
.text-success {
  color: #67c23a;
}
.text-warning {
  color: #e6a23c;
}
.text-danger {
  color: #f56c6c;
}
.text-info {
  color: #909399;
}
.text-purple {
  color: #8e44ad;
}
/* Mobile Responsive Adjustments */
@media only screen and (max-width: 767px) {
  .stat-card-modern {
    height: 120px !important;
    margin-bottom: 10px !important;

    :deep(.el-card__body) {
      padding: 12px !important;
    }

    .card-modern-header {
      margin-bottom: 5px;

      .title {
        font-size: 13px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 85%;
      }

      .icon-wrapper {
        padding: 4px;
        .el-icon {
          font-size: 14px;
        }
      }
    }

    .card-modern-content {
      .amount {
        font-size: 20px;
        margin-bottom: 2px;

        small {
          font-size: 12px;
        }
      }

      .amount-sub {
        font-size: 12px;
      }

      .sub-info {
        display: none; /* Hide sub-info on mobile to save space */
      }
    }

    .card-icon-bg {
      font-size: 60px;
      right: -10px;
      bottom: -10px;
    }
  }

  /* Adjust chart and list cards on mobile */
  .chart-card {
    margin-bottom: 10px;

    :deep(.el-card__header) {
      padding: 10px 12px;
    }
  }

  /* Compact Filter Container */
  .filter-container {
    padding: 10px;

    .el-select,
    .el-date-editor {
      width: 100% !important; /* Full width inputs on mobile */
      margin-right: 0 !important;
      margin-bottom: 10px;
    }

    .el-button {
      width: 100%;
    }
  }

  /* Reduce summary row gutters */
  .summary-row {
    margin-left: -5px !important;
    margin-right: -5px !important;

    .el-col {
      padding-left: 5px !important;
      padding-right: 5px !important;
    }
  }
}
</style>
