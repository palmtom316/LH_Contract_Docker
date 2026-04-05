import { readChartTheme } from './chartTheme'

function ensureArray(value) {
  return Array.isArray(value) ? value : []
}

export function createBarChartOption({ categories = [], series = [] }) {
  const theme = readChartTheme()
  const safeCategories = ensureArray(categories)
  const safeSeries = ensureArray(series)

  return {
    aria: {
      enabled: true
    },
    tooltip: { trigger: 'axis', confine: true },
    legend: {
      bottom: 0,
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
        lineStyle: { color: theme.border }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: theme.text
      },
      splitLine: {
        lineStyle: { color: theme.border }
      }
    },
    series: safeSeries.map(item => ({
      ...item,
      type: 'bar',
      barMaxWidth: 18
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
      confine: true
    },
    legend: {
      bottom: 0,
      type: 'scroll',
      textStyle: {
        color: theme.text,
        fontSize: 11
      }
    },
    series: [
      {
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['50%', '42%'],
        avoidLabelOverlap: true,
        label: {
          position: 'outside',
          color: theme.text,
          formatter: '{b}: {d}%'
        },
        labelLine: {
          show: true,
          length: 10,
          length2: 8
        },
        data: safeData
      }
    ]
  }
}
