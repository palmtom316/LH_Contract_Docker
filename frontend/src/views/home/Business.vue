<template>
  <div class="business-dashboard" v-loading="loading">
    <AppFilterBar class="dashboard-filter-bar" inline-actions>
      <span class="dashboard-filter-bar__label">统计周期</span>
      <el-date-picker
        v-model="currentYear"
        class="dashboard-filter-bar__control dashboard-filter-bar__control--year"
        type="year"
        placeholder="选择年份"
        value-format="YYYY"
        @change="handleFilterChange"
      />
      <el-select
        v-model="currentMonth"
        class="dashboard-filter-bar__control dashboard-filter-bar__control--month"
        placeholder="选择月份"
        clearable
        @change="handleFilterChange"
      >
        <el-option label="全年数据" :value="null" />
        <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
      </el-select>
      <template #actions>
        <el-button type="primary" icon="Refresh" @click="fetchData">刷新看板</el-button>
      </template>
    </AppFilterBar>

    <section class="metric-grid">
      <AppMetricCard
        v-for="item in businessMetricCards"
        :key="item.title"
        :eyebrow="''"
        :title="item.title"
        :value="item.value"
      >
        <template #badge>
          <span class="metric-badge" :class="`metric-badge--${item.tone}`">{{ item.badge }}</span>
        </template>
        <template #footer>
          <span class="business-metric-card__meta">{{ item.meta }}</span>
        </template>
      </AppMetricCard>
    </section>

    <section class="dashboard-main-grid">
      <AppSectionCard class="trend-panel">
        <template #header>
          <div class="section-heading">
            <div>
              <div class="section-heading__title">{{ currentYear }} 年度收支趋势</div>
              <div v-if="currentMonth" class="section-heading__meta">{{ currentMonth }} 月视图</div>
            </div>
          </div>
        </template>
        <div ref="trendChartRef" class="chart-surface chart-surface--trend"></div>
      </AppSectionCard>

      <div class="dashboard-side-stack">
        <AppSectionCard>
          <template #header>
            <div class="section-heading">
              <div class="section-heading__title">{{ currentMonth ? `${currentMonth}月` : '本期' }}应收账款</div>
            </div>
          </template>
          <div class="arap-panel">
            <div class="arap-panel__value arap-panel__value--primary">¥ {{ formatWan(arStats.outstanding) }} <small>万</small></div>
            <div class="arap-panel__stats">
              <div class="arap-panel__row"><span>应收款</span><strong>¥ {{ formatWan(arStats.total_receivable) }} 万</strong></div>
              <div class="arap-panel__row"><span>已收款</span><strong>¥ {{ formatWan(arStats.total_received) }} 万</strong></div>
            </div>
            <el-progress :percentage="calcPercentage(arStats.total_received, arStats.total_receivable)" :stroke-width="10" status="success" />
          </div>
        </AppSectionCard>

        <AppSectionCard>
          <template #header>
            <div class="section-heading">
              <div class="section-heading__title">{{ currentMonth ? `${currentMonth}月` : '本期' }}应付账款</div>
            </div>
          </template>
          <div class="arap-panel">
            <div class="arap-panel__value arap-panel__value--warning">¥ {{ formatWan(apStats.outstanding) }} <small>万</small></div>
            <div class="arap-panel__stats">
              <div class="arap-panel__row"><span>应付款</span><strong>¥ {{ formatWan(apStats.total_payable) }} 万</strong></div>
              <div class="arap-panel__row"><span>已付款</span><strong>¥ {{ formatWan(apStats.total_paid) }} 万</strong></div>
            </div>
            <el-progress :percentage="calcPercentage(apStats.total_paid, apStats.total_payable)" :stroke-width="10" status="success" />
          </div>
        </AppSectionCard>
      </div>
    </section>

    <section class="dashboard-detail-grid">
      <AppSectionCard>
        <template #header>
          <div class="section-heading">
            <div class="section-heading__title">业务分类摘要</div>
          </div>
        </template>
        <div class="summary-columns">
          <section v-for="group in summaryGroups" :key="group.title" class="summary-block">
            <div class="summary-block__header">
              <span>{{ group.title }}</span>
              <strong>{{ group.total }}</strong>
            </div>
            <div class="summary-block__list">
              <article v-for="item in group.items" :key="`${group.title}-${item.name}`" class="summary-item">
                <span class="summary-item__name">{{ item.name }}</span>
                <span class="summary-item__value">{{ item.label }}</span>
              </article>
            </div>
          </section>
        </div>
      </AppSectionCard>

      <AppSectionCard>
        <template #header>
          <div class="section-heading">
            <div class="section-heading__title">分类构成</div>
          </div>
        </template>
        <div class="pie-grid">
          <div class="pie-card">
            <div class="pie-card__title">上游合同分类</div>
            <div ref="upstreamPieRef" class="chart-surface chart-surface--pie"></div>
          </div>
          <div class="pie-card">
            <div class="pie-card__title">上游公司分类</div>
            <div ref="upstreamCompanyPieRef" class="chart-surface chart-surface--pie"></div>
          </div>
          <div class="pie-card">
            <div class="pie-card__title">支出构成</div>
            <div ref="expenseStructPieRef" class="chart-surface chart-surface--pie"></div>
          </div>
          <div class="pie-card">
            <div class="pie-card__title">无合同费用分类</div>
            <div ref="expenseCatPieRef" class="chart-surface chart-surface--pie"></div>
          </div>
        </div>
      </AppSectionCard>
    </section>
  </div>
</template>

<script setup>
import {
  computed,
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
import AppFilterBar from "@/components/ui/AppFilterBar.vue";
import AppMetricCard from '@/components/ui/AppMetricCard.vue';

const getThemeColor = (name, fallback = "") =>
  getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;

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

const businessMetricCards = computed(() => [
  {
    badge: "签约",
    tone: "primary",
    title: "上游签约",
    value: `${annualUpstreamCount.value} 单`,
    meta: `¥ ${formatWan(annualUpstreamAmount.value)} 万`,
  },
  {
    badge: "收入",
    tone: "success",
    title: "回款总额",
    value: `¥ ${formatWan(annualReceiptsAmount.value)} 万`,
    meta: "实际到账金额",
  },
  {
    badge: "支出",
    tone: "danger",
    title: "付款总额",
    value: `¥ ${formatWan(annualPaymentsAmount.value)} 万`,
    meta: "下游、管理及零星支出",
  },
  {
    badge: "成本",
    tone: "warning",
    title: "下游及管理签约",
    value: `${annualDownMgmtCount.value} 单`,
    meta: `¥ ${formatWan(annualDownMgmtAmount.value)} 万`,
  },
]);

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

const formatSummaryTotal = (items, valueKey = "amount", unit = "单") => {
  const count = items.reduce((acc, cur) => acc + (cur.count || 0), 0);
  const amount = items.reduce((acc, cur) => acc + (cur[valueKey] || 0), 0);
  return `${count}${unit} / ¥${formatWan(amount)}万`;
};

const summaryGroups = computed(() => [
  {
    title: "上游合同",
    total: formatSummaryTotal(upstreamSummary.value),
    items: upstreamSummary.value.slice(0, 6).map((item) => ({
      name: item.name,
      label: `${item.count}单 / ¥${formatWan(item.amount)}万`,
    })),
  },
  {
    title: "上游公司分类",
    total: formatSummaryTotal(upstreamCompanySummary.value),
    items: upstreamCompanySummary.value.slice(0, 6).map((item) => ({
      name: item.name,
      label: `${item.count}单 / ¥${formatWan(item.amount)}万`,
    })),
  },
  {
    title: "下游合同",
    total: formatSummaryTotal(downstreamSummary.value),
    items: downstreamSummary.value.slice(0, 6).map((item) => ({
      name: item.name,
      label: `${item.count}单 / ¥${formatWan(item.amount)}万`,
    })),
  },
  {
    title: "管理合同",
    total: formatSummaryTotal(managementSummary.value),
    items: managementSummary.value.slice(0, 6).map((item) => ({
      name: item.name,
      label: `${item.count}单 / ¥${formatWan(item.amount)}万`,
    })),
  },
  {
    title: "无合同费用",
    total: formatSummaryTotal(expenseSummary.value, "value", "笔"),
    items: expenseSummary.value.slice(0, 6).map((item) => ({
      name: item.name,
      label: `${item.count}笔 / ¥${formatWan(item.value)}万`,
    })),
  },
  {
    title: "零星用工",
    total: `${zeroHourLaborSummary.count}笔 / ¥${formatWan(zeroHourLaborSummary.total)}万`,
    items: [
      { name: "零星用工支出", label: `¥${formatWan(zeroHourLaborSummary.total)}万` },
      { name: "发生笔数", label: `${zeroHourLaborSummary.count}笔` },
    ],
  },
]);

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
          borderColor: getThemeColor("--surface-panel"),
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
          borderColor: getThemeColor("--surface-panel"),
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
.business-dashboard {
  display: grid;
  gap: var(--space-5);
}

:deep(.app-filter-bar.dashboard-filter-bar) {
  padding: 14px 16px;
}

.dashboard-filter-bar__label {
  display: inline-flex;
  align-items: center;
  min-height: var(--workspace-control-height);
  font-size: 13px;
  font-weight: 700;
  color: var(--text-secondary);
  white-space: nowrap;
}

.dashboard-filter-bar__control {
  width: 172px;
}

.dashboard-filter-bar__control--year {
  width: 124px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

.metric-grid :deep(.app-metric-card) {
  min-height: 208px;
  border-radius: 22px;
}

.metric-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.metric-badge--primary {
  background: var(--brand-primary-soft);
  color: var(--brand-primary-strong);
}

.metric-badge--warning {
  background: color-mix(in srgb, var(--status-warning) 14%, transparent);
  color: var(--status-warning);
}

.metric-badge--success {
  background: color-mix(in srgb, var(--status-success) 14%, transparent);
  color: var(--status-success);
}

.metric-badge--danger {
  background: color-mix(in srgb, var(--status-danger) 14%, transparent);
  color: var(--status-danger);
}

.business-metric-card__meta {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.arap-panel__value small {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-muted);
}

.dashboard-main-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(300px, 0.9fr);
  gap: var(--space-4);
}

.dashboard-side-stack {
  display: grid;
  gap: var(--space-4);
}

.trend-panel :deep(.el-card__body) {
  padding-top: 18px;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.section-heading__title {
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 700;
}

.section-heading__meta {
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 12px;
}

.chart-surface {
  width: 100%;
  min-width: 0;
}

.chart-surface--trend {
  height: 360px;
}

.chart-surface--pie {
  height: 240px;
}

.arap-panel {
  display: grid;
  gap: 18px;
}

.arap-panel__value {
  font-size: 30px;
  font-weight: 700;
  line-height: 1.08;
}

.arap-panel__value--primary {
  color: var(--brand-primary);
}

.arap-panel__value--warning {
  color: var(--status-warning);
}

.arap-panel__stats {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--surface-panel-muted) 72%, var(--surface-panel) 28%);
}

.arap-panel__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  font-size: 13px;
  color: var(--text-secondary);
}

.arap-panel__row strong {
  color: var(--text-primary);
}

.dashboard-detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  gap: var(--space-4);
}

.summary-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.summary-block {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface-panel) 82%, var(--surface-panel-muted) 18%);
}

.summary-block__header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}

.summary-block__header strong {
  font-size: 12px;
  color: var(--text-secondary);
}

.summary-block__list {
  display: grid;
  gap: 8px;
}

.summary-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}

.summary-item__name {
  min-width: 0;
  color: var(--text-secondary);
}

.summary-item__value {
  flex-shrink: 0;
  color: var(--text-primary);
  font-weight: 600;
}

.pie-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.pie-card {
  min-width: 0;
  padding: 14px;
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface-panel) 84%, var(--surface-panel-muted) 16%);
}

.pie-card__title {
  margin-bottom: 12px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
}

@media (max-width: 1279px) {
  .metric-grid,
  .summary-columns,
  .pie-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .dashboard-main-grid,
  .dashboard-detail-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .business-dashboard {
    gap: var(--space-4);
  }

  :deep(.app-filter-bar.dashboard-filter-bar) {
    padding: 16px;
  }

  :deep(.app-filter-bar.dashboard-filter-bar .app-filter-bar__main),
  :deep(.app-filter-bar.dashboard-filter-bar .app-filter-bar__actions) {
    width: 100%;
  }

  .dashboard-filter-bar__control,
  :deep(.app-filter-bar.dashboard-filter-bar .app-filter-bar__actions .el-button) {
    width: 100%;
  }

  .metric-grid,
  .summary-columns,
  .pie-grid {
    grid-template-columns: 1fr;
  }

  .metric-grid :deep(.app-metric-card) {
    min-height: 156px;
  }

  .chart-surface--trend,
  .chart-surface--pie {
    height: 280px;
  }

  .summary-item,
  .summary-block__header,
  .arap-panel__row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
