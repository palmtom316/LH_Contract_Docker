import { readChartTheme } from './chartTheme'

function ensureArray(value) {
  return Array.isArray(value) ? value : []
}

export function buildTopRankedItems(items, limit = 6) {
  const ranked = ensureArray(items)
    .map(item => ({
      name: item?.name,
      value: Number(item?.value ?? 0)
    }))
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

  return {
    aria: { enabled: true },
    title: {
      text: title,
      left: 'left',
      textStyle: { color: theme.textStrong, fontSize: 14, fontWeight: 600 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      confine: true
    },
    grid: {
      left: '8%',
      right: '4%',
      top: '16%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: theme.text }
    },
    yAxis: {
      type: 'category',
      data: ranked.map(item => item.name),
      axisLabel: { color: theme.text }
    },
    series: [
      {
        type: 'bar',
        data: ranked.map(item => item.value),
        barMaxWidth: 18,
        itemStyle: { color, borderRadius: [0, 8, 8, 0] }
      }
    ]
  }
}

export function createStackedCategoryOption({ title, categories, series }) {
  const theme = readChartTheme()

  return {
    aria: { enabled: true },
    title: {
      text: title,
      left: 'left',
      textStyle: { color: theme.textStrong, fontSize: 14, fontWeight: 600 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      confine: true
    },
    legend: {
      bottom: 0,
      textStyle: { color: theme.text, fontSize: 11 }
    },
    grid: {
      left: '8%',
      right: '4%',
      top: '16%',
      bottom: '56px',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: theme.text }
    },
    yAxis: {
      type: 'category',
      data: ensureArray(categories),
      axisLabel: { color: theme.text }
    },
    series: ensureArray(series).map(item => ({
      ...item,
      type: 'bar',
      stack: 'total',
      barMaxWidth: 24
    }))
  }
}
