import { readChartTheme } from './chartTheme'

function ensureArray(value) {
  return Array.isArray(value) ? value : []
}

function formatAmountTick(value) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric)) return '0'
  return `${Math.round(numeric / 10000)}万`
}

function hasMeaningfulValues(values = []) {
  return ensureArray(values).some((value) => Number(value || 0) !== 0)
}

function createHorizontalEmptyState(theme, color) {
  return {
    aria: { enabled: true },
    tooltip: { show: false },
    grid: {
      left: '24%',
      right: '4%',
      top: '8%',
      bottom: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      show: false
    },
    yAxis: {
      type: 'category',
      data: [],
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
          type: 'roundRect',
          left: 'center',
          top: 'middle',
          shape: { x: -14, y: -30, width: 28, height: 28, r: 9 },
          style: {
            fill: color,
            opacity: 0.12
          }
        }
      ]
    },
    series: [
      {
        type: 'bar',
        data: [],
        barMaxWidth: 18,
        itemStyle: { color, borderRadius: [0, 8, 8, 0] }
      }
    ]
  }
}

function createStackedEmptyState(theme) {
  return {
    aria: { enabled: true },
    tooltip: { show: false },
    legend: { show: false },
    grid: {
      left: '24%',
      right: '4%',
      top: '8%',
      bottom: '56px',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      show: false
    },
    yAxis: {
      type: 'category',
      data: [],
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
            fill: theme.text,
            fontSize: 13,
            fontWeight: 600,
            textAlign: 'center'
          }
        }
      ]
    },
    series: []
  }
}

export function buildTopRankedItems(items, limit = 6) {
  const ranked = ensureArray(items)
    .map(item => ({
      name: item?.name || '未分类',
      value: Number(item?.value || item?.amount || 0)
    }))
    .filter(item => item.value > 0)
    .sort((a, b) => b.value - a.value)

  if (ranked.length <= limit) {
    return ranked
  }

  const head = ranked.slice(0, limit)
  const tailValue = ranked.slice(limit).reduce((sum, item) => sum + item.value, 0)
  return tailValue > 0 ? [...head, { name: '其他', value: tailValue }] : head
}

export function createHorizontalRankOption({ title, items, color = '#2563eb' }) {
  const theme = readChartTheme()
  const ranked = buildTopRankedItems(items)
  const hasRankedData = ranked.length > 0

  if (!hasRankedData) {
    return createHorizontalEmptyState(theme, color)
  }

  const yAxisData = ranked.map(item => item.name)
  const seriesData = ranked.map(item => item.value)

  return {
    aria: { enabled: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      confine: true,
      formatter(params) {
        const first = Array.isArray(params) ? params[0] : params
        if (!first) return ''
        const value = Number(first.value || 0)
        return `${first.name}<br/>${value.toLocaleString('zh-CN')} 元`
      }
    },
    grid: {
      left: '24%',
      right: '4%',
      top: '8%',
      bottom: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '金额（万元）',
      nameTextStyle: { color: theme.text, padding: [0, 0, 0, 4] },
      splitNumber: 3,
      axisLabel: {
        color: theme.text,
        fontSize: 11,
        hideOverlap: true,
        margin: 10,
        formatter: formatAmountTick
      },
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      splitLine: {
        lineStyle: { color: theme.gridLine || theme.border }
      }
    },
    yAxis: {
      type: 'category',
      data: yAxisData,
      axisLabel: {
        color: theme.text,
        width: 120,
        overflow: 'truncate'
      },
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      }
    },
    series: [
      {
        type: 'bar',
        data: seriesData,
        barMaxWidth: 18,
        itemStyle: { color, borderRadius: [0, 8, 8, 0] }
      }
    ]
  }
}

export function createStackedCategoryOption({ title, categories, series }) {
  const theme = readChartTheme()
  const safeSeries = ensureArray(series)
  const hasStackedData = safeSeries.some((item) => hasMeaningfulValues(item?.data))

  if (!ensureArray(categories).length || !hasStackedData) {
    return createStackedEmptyState(theme)
  }

  return {
    aria: { enabled: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      confine: true,
      formatter(params) {
        if (!Array.isArray(params) || !params.length) return ''
        const lines = [params[0].name]
        params.forEach((item) => {
          lines.push(`${item.marker}${item.seriesName}: ${Number(item.value || 0).toLocaleString('zh-CN')} 元`)
        })
        return lines.join('<br/>')
      }
    },
    legend: {
      bottom: 0,
      type: 'scroll',
      textStyle: { color: theme.text, fontSize: 11 }
    },
    grid: {
      left: '24%',
      right: '4%',
      top: '8%',
      bottom: '72px',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '金额（万元）',
      nameTextStyle: { color: theme.text, padding: [0, 0, 0, 4] },
      splitNumber: 3,
      axisLabel: {
        color: theme.text,
        fontSize: 11,
        hideOverlap: true,
        margin: 10,
        formatter: formatAmountTick
      },
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      splitLine: {
        lineStyle: { color: theme.gridLine || theme.border }
      }
    },
    yAxis: {
      type: 'category',
      data: ensureArray(categories),
      axisLabel: {
        color: theme.text,
        width: 120,
        overflow: 'truncate'
      },
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      }
    },
    series: safeSeries.map(item => ({
      ...item,
      type: 'bar',
      stack: 'total',
      barMaxWidth: 24
    }))
  }
}
