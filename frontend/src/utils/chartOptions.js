import { readChartTheme } from './chartTheme'

export function createBarChartOption({ categories = [], series = [] }) {
  const theme = readChartTheme()

  return {
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
      data: categories,
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
    series: series.map(item => ({
      ...item,
      type: 'bar',
      barMaxWidth: 18
    }))
  }
}
