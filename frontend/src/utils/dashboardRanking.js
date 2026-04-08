import { readChartTheme } from './chartTheme'

function ensureArray(value) {
  return Array.isArray(value) ? value : []
}

function formatAmountTick(value) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric)) return '0'
  return `${Math.round(numeric / 10000)}万`
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
  const yAxisData = hasRankedData ? ranked.map(item => item.name) : ['暂无数据']
  const seriesData = hasRankedData ? ranked.map(item => item.value) : [0]

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
      left: '18%',
      right: '4%',
      top: '8%',
      bottom: '12%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '金额（万元）',
      nameTextStyle: { color: theme.text, padding: [0, 0, 0, 4] },
      splitNumber: 4,
      axisLabel: {
        color: theme.text,
        fontSize: 11,
        formatter: formatAmountTick
      },
      splitLine: {
        lineStyle: { color: theme.border }
      }
    },
    yAxis: {
      type: 'category',
      data: yAxisData,
      axisLabel: {
        color: theme.text,
        width: 84,
        overflow: 'truncate'
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
      textStyle: { color: theme.text, fontSize: 11 }
    },
    grid: {
      left: '18%',
      right: '4%',
      top: '8%',
      bottom: '56px',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '金额（万元）',
      nameTextStyle: { color: theme.text, padding: [0, 0, 0, 4] },
      splitNumber: 4,
      axisLabel: {
        color: theme.text,
        fontSize: 11,
        formatter: formatAmountTick
      },
      splitLine: {
        lineStyle: { color: theme.border }
      }
    },
    yAxis: {
      type: 'category',
      data: ensureArray(categories),
      axisLabel: {
        color: theme.text,
        width: 84,
        overflow: 'truncate'
      }
    },
    series: ensureArray(series).map(item => ({
      ...item,
      type: 'bar',
      stack: 'total',
      barMaxWidth: 24
    }))
  }
}
