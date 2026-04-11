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
