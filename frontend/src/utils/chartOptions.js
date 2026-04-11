import { readChartTheme } from './chartTheme'

function ensureArray(value) {
  return Array.isArray(value) ? value : []
}

function formatTrendLabel(value, sliceStart = 5) {
  if (!value || typeof value !== 'string') return value
  return value.length > sliceStart ? value.substring(sliceStart) : value
}

function formatCompactWan(value) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric)) return '0万'
  return `${Math.round(numeric / 10000)}万`
}

function formatWaterfallCategoryLabel(value) {
  const text = typeof value === 'string' ? value : String(value || '')
  if (!text) return ''
  const wrapped = {
    上游回款: '上游\n回款',
    下游合同: '下游\n合同',
    管理合同: '管理\n合同',
    无合同费用: '无合同\n费用',
    零星用工: '零星\n用工',
    净结果: '净结果'
  }
  return wrapped[text] || text
}

function hasMeaningfulValues(values = []) {
  return ensureArray(values).some((value) => Number(value || 0) !== 0)
}

function createCartesianEmptyState(theme, { seriesCount = 1, barMaxWidth = 24 } = {}) {
  return {
    aria: { enabled: true },
    tooltip: { show: false },
    grid: {
      left: '8%',
      right: '4%',
      top: '10%',
      bottom: '14%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: [],
      show: false
    },
    yAxis: {
      type: 'value',
      show: false
    },
    graphic: {
      elements: [
        {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text: '暂无数据',
            textAlign: 'center',
            fill: theme.text,
            fontSize: 13,
            fontWeight: 600
          }
        },
        {
          type: 'circle',
          left: 'center',
          top: 'middle',
          shape: { cx: 0, cy: -30, r: 16 },
          style: {
            fill: 'transparent',
            stroke: theme.border,
            lineWidth: 1.5
          }
        },
        {
          type: 'line',
          left: 'center',
          top: 'middle',
          shape: { x1: -8, y1: -20, x2: 8, y2: -20 },
          style: {
            stroke: theme.border,
            lineWidth: 1.5,
            lineCap: 'round'
          }
        }
      ]
    },
    series: Array.from({ length: seriesCount }, () => ({
      type: 'bar',
      barMaxWidth,
      data: []
    }))
  }
}

export function createBarChartOption({ categories = [], series = [] }) {
  const theme = readChartTheme()
  const safeCategories = ensureArray(categories)
  const safeSeries = ensureArray(series)

  return {
    aria: {
      enabled: true
    },
    tooltip: {
      trigger: 'axis',
      confine: true,
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: { color: theme.textStrong, fontSize: 12 }
    },
    legend: {
      bottom: 0,
      type: 'scroll',
      textStyle: { color: theme.text, fontSize: 12 }
    },
    grid: {
      left: '8%',
      right: '4%',
      top: '12%',
      bottom: '64px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: safeCategories,
      axisLabel: {
        hideOverlap: true,
        color: theme.text,
        fontSize: 11
      },
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: theme.text
      },
      axisLine: {
        show: false
      },
      splitLine: {
        lineStyle: { color: theme.gridLine }
      }
    },
    series: safeSeries.map(item => ({
      ...item,
      type: 'bar',
      barMaxWidth: 18,
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        ...(item.itemStyle || {})
      }
    }))
  }
}

export function createPieChartOption({ title = '', data = [] }) {
  const theme = readChartTheme()
  const safeData = ensureArray(data)

  return {
    aria: {
      enabled: true
    },
    title: {
      text: title,
      left: 'center',
      textStyle: {
        color: theme.textStrong,
        fontSize: 14,
        fontWeight: 600
      }
    },
    tooltip: {
      trigger: 'item',
      confine: true,
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: {
        color: theme.textStrong,
        fontSize: 12
      }
    },
    legend: {
      bottom: 0,
      type: 'scroll',
      textStyle: {
        color: theme.text,
        fontSize: 12
      }
    },
    series: [
      {
        type: 'pie',
        radius: ['56%', '74%'],
        center: ['50%', '42%'],
        avoidLabelOverlap: true,
        label: {
          show: false
        },
        labelLine: {
          show: false
        },
        emphasis: {
          scale: true,
          label: {
            show: true,
            position: 'center',
            formatter: '{b}\n{d}%',
            color: theme.textStrong,
            fontSize: 14,
            fontWeight: 600
          }
        },
        data: safeData
      }
    ]
  }
}

export function createStackedTrendOption({
  categories = [],
  income = [],
  expenseBreakdown = {},
  incomeName = '收入',
  laborKey = 'labor',
  mobile = false,
  labelSliceStart = 5,
  legendNames = []
}) {
  const theme = readChartTheme()
  const safeCategories = ensureArray(categories)
  const series = [
    {
      name: incomeName,
      data: ensureArray(income).map((value) => Number((Number(value || 0) / 10000).toFixed(2))),
      color: theme.success
    },
    {
      name: '下游合同',
      stack: 'expense',
      data: ensureArray(expenseBreakdown.downstream).map((value) => Number((Number(value || 0) / 10000).toFixed(2))),
      color: theme.danger
    },
    {
      name: '管理合同',
      stack: 'expense',
      data: ensureArray(expenseBreakdown.management).map((value) => Number((Number(value || 0) / 10000).toFixed(2))),
      color: theme.warning
    },
    {
      name: '无合同费用',
      stack: 'expense',
      data: ensureArray(expenseBreakdown.non_contract).map((value) => Number((Number(value || 0) / 10000).toFixed(2))),
      color: theme.info
    },
    {
      name: '零星用工',
      stack: 'expense',
      data: ensureArray(expenseBreakdown[laborKey]).map((value) => Number((Number(value || 0) / 10000).toFixed(2))),
      color: theme.primary
    }
  ]
  const option = createBarChartOption({ categories: safeCategories, series })

  option.tooltip.formatter = (params) => {
    if (!Array.isArray(params) || !params.length) return ''
    const lines = [`${params[0].axisValueLabel || params[0].name}`]
    params.forEach((item) => {
      const value = Number(item.value)
      if (!Number.isNaN(value) && value > 0) {
        lines.push(`${item.marker}${item.seriesName}: ${value.toFixed(2)} 万元`)
      }
    })
    return lines.length > 1 ? lines.join('<br/>') : ''
  }
  option.legend.data = legendNames.length ? legendNames : series.map((item) => item.name)
  option.legend.type = mobile ? 'scroll' : 'plain'
  option.legend.textStyle = { color: theme.text, fontSize: mobile ? 10 : 12 }
  option.grid.top = mobile ? '14%' : '12%'
  option.grid.bottom = mobile ? '88px' : '72px'
  option.grid.left = mobile ? '11%' : '8%'
  option.grid.right = '4%'
  option.xAxis.axisLabel.interval = 'auto'
  option.xAxis.axisLabel.rotate = mobile ? 36 : 0
  option.xAxis.axisLabel.formatter = (value) => formatTrendLabel(value, labelSliceStart)
  option.yAxis.name = '金额 (万元)'
  option.yAxis.nameTextStyle = { color: theme.text, padding: [0, 0, 6, 0] }

  return option
}

export function createResultWaterfallOption({
  received = 0,
  downstreamExpense = 0,
  managementExpense = 0,
  nonContractExpense = 0,
  laborExpense = 0
}) {
  const theme = readChartTheme()
  const safeReceived = Number(received || 0)
  const safeDownstream = Number(downstreamExpense || 0)
  const safeManagement = Number(managementExpense || 0)
  const safeNonContract = Number(nonContractExpense || 0)
  const safeLabor = Number(laborExpense || 0)
  const netResult = safeReceived - safeDownstream - safeManagement - safeNonContract - safeLabor
  const deltas = [
    safeReceived,
    -safeDownstream,
    -safeManagement,
    -safeNonContract,
    -safeLabor,
    netResult
  ]

  if (!hasMeaningfulValues(deltas)) {
    return createCartesianEmptyState(theme, { seriesCount: 2, barMaxWidth: 24 })
  }

  let runningTotal = 0
  const offsetSeries = deltas.map((delta, index) => {
    if (index === deltas.length - 1) {
      return 0
    }

    const offset = delta >= 0 ? runningTotal : runningTotal + delta
    runningTotal += delta
    return offset
  })

  const resultSeries = [
    { value: safeReceived, itemStyle: { color: theme.success } },
    { value: safeDownstream, itemStyle: { color: theme.danger } },
    { value: safeManagement, itemStyle: { color: theme.warning } },
    { value: safeNonContract, itemStyle: { color: theme.info } },
    { value: safeLabor, itemStyle: { color: theme.primary } },
    { value: netResult, itemStyle: { color: netResult >= 0 ? theme.success : theme.danger } }
  ]

  return {
    aria: { enabled: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      confine: true,
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      textStyle: { color: theme.textStrong, fontSize: 12 },
      formatter(params) {
        const safeParams = Array.isArray(params) ? params : [params]
        const visiblePoint = safeParams.find((item) => Number(item?.value || 0) !== 0) || safeParams[safeParams.length - 1]
        if (!visiblePoint) return ''
        return `${visiblePoint.name}<br/>${Number(visiblePoint.value || 0).toLocaleString('zh-CN')} 元`
      }
    },
    grid: {
      left: '8%',
      right: '4%',
      top: '10%',
      bottom: '22%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['上游回款', '下游合同', '管理合同', '无合同费用', '零星用工', '净结果'],
      axisLabel: {
        color: theme.text,
        fontSize: 11,
        interval: 0,
        hideOverlap: true,
        lineHeight: 14,
        formatter: formatWaterfallCategoryLabel
      },
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      name: '金额（万元）',
      axisLabel: {
        color: theme.text,
        formatter: formatCompactWan
      },
      axisLine: {
        show: false
      },
      splitLine: {
        lineStyle: { color: theme.gridLine || theme.border }
      }
    },
    series: [
      {
        type: 'bar',
        stack: 'result',
        itemStyle: { opacity: 0 },
        emphasis: { disabled: true },
        barMaxWidth: 24,
        data: offsetSeries
      },
      {
        type: 'bar',
        stack: 'result',
        barMaxWidth: 24,
        data: resultSeries
      }
    ]
  }
}
