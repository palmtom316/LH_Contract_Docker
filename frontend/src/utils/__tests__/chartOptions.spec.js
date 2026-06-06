import { beforeEach, describe, expect, it } from 'vitest'
import { createBarChartOption, createPieChartOption, createResultWaterfallOption } from '../chartOptions'
import { readChartTheme } from '../chartTheme'

describe('createBarChartOption', () => {
  beforeEach(() => {
    document.documentElement.style.setProperty('--text-secondary', '#475569')
    document.documentElement.style.setProperty('--text-primary', '#0f172a')
    document.documentElement.style.setProperty('--border-subtle', '#d7dfeb')
    document.documentElement.style.setProperty('--surface-panel', '#ffffff')
    document.documentElement.style.setProperty('--brand-primary', '#2563eb')
    document.documentElement.style.setProperty('--status-success', '#0f766e')
    document.documentElement.style.setProperty('--status-warning', '#b45309')
    document.documentElement.style.setProperty('--status-danger', '#b83280')
    document.documentElement.style.setProperty('--status-info', '#475569')
  })

  it('reserves legend and label space for readability', () => {
    const option = createBarChartOption({
      categories: ['2026-01', '2026-02'],
      series: [{ name: '收入', data: [10, 20], color: '#2563eb' }]
    })

    expect(option.grid.containLabel).toBe(true)
    expect(option.legend.bottom).toBe(4)
    expect(option.legend.itemGap).toBeGreaterThanOrEqual(16)
    expect(option.xAxis.axisLabel.hideOverlap).toBe(true)
    expect(option.xAxis.axisLabel.margin).toBeGreaterThanOrEqual(8)
    expect(option.aria.enabled).toBe(true)
  })

  it('guards against null categories and series input', () => {
    const option = createBarChartOption({
      categories: null,
      series: null
    })

    expect(option.xAxis.data).toEqual([])
    expect(option.series).toEqual([])
  })
})

describe('createPieChartOption', () => {
  it('uses center emphasis and legend-led reading instead of risky outside labels', () => {
    const option = createPieChartOption({
      title: '费用结构',
      data: [
        { name: '管理费', value: 30 },
        { name: '人工费', value: 20 },
        { name: '材料费', value: 10 }
      ]
    })

    expect(option.series[0].label.show).toBe(false)
    expect(option.series[0].labelLine.show).toBe(false)
    expect(option.series[0].emphasis.label.show).toBe(true)
    expect(option.series[0].emphasis.label.position).toBe('center')
    expect(option.legend.type).toBe('scroll')
    expect(option.series[0].avoidLabelOverlap).toBe(true)
    expect(option.aria.enabled).toBe(true)
  })

  it('guards against null pie data input', () => {
    const option = createPieChartOption({
      title: '合同分类',
      data: null
    })

    expect(option.series[0].data).toEqual([])
  })
})

describe('createResultWaterfallOption', () => {
  beforeEach(() => {
    document.documentElement.style.setProperty('--text-secondary', '#475569')
    document.documentElement.style.setProperty('--text-primary', '#0f172a')
    document.documentElement.style.setProperty('--border-subtle', '#d7dfeb')
    document.documentElement.style.setProperty('--surface-panel', '#ffffff')
    document.documentElement.style.setProperty('--brand-primary', '#2563eb')
    document.documentElement.style.setProperty('--status-success', '#0f766e')
    document.documentElement.style.setProperty('--status-warning', '#b45309')
    document.documentElement.style.setProperty('--status-danger', '#b83280')
    document.documentElement.style.setProperty('--status-info', '#475569')
  })

  it('switches to a dedicated empty state instead of rendering overlapping category labels when all values are zero', () => {
    const option = createResultWaterfallOption({
      received: 0,
      downstreamExpense: 0,
      managementExpense: 0,
      nonContractExpense: 0,
      laborExpense: 0
    })

    expect(option.xAxis.show).toBe(false)
    expect(option.yAxis.show).toBe(false)
    expect(option.series[0].data).toEqual([])
    expect(option.series[1].data).toEqual([])
    expect(option.graphic.elements[0].style.text).toBe('暂无数据')
  })

  it('wraps long category labels and reads the visible result series value in tooltips', () => {
    const option = createResultWaterfallOption({
      received: 1900000,
      downstreamExpense: 510000,
      managementExpense: 235000,
      nonContractExpense: 74400,
      laborExpense: 68160
    })

    expect(option.grid.bottom).toBe('22%')
    expect(option.xAxis.axisLabel.hideOverlap).toBe(true)
    expect(option.xAxis.axisLabel.formatter('无合同费用')).toBe('无合同\n费用')

    const tooltipHtml = option.tooltip.formatter([
      { seriesName: '辅助', name: '上游回款', value: 0 },
      { seriesName: '结果', name: '上游回款', value: 1900000 }
    ])

    expect(tooltipHtml).toBe('上游回款<br/>1,900,000 元')
  })
})

describe('readChartTheme', () => {
  it('falls back to default tokens when browser globals are unavailable', () => {
    const originalDocument = globalThis.document
    const originalGetComputedStyle = globalThis.getComputedStyle

    Reflect.deleteProperty(globalThis, 'document')
    Reflect.deleteProperty(globalThis, 'getComputedStyle')

    const theme = readChartTheme()

    globalThis.document = originalDocument
    globalThis.getComputedStyle = originalGetComputedStyle

    expect(theme.text).toBe('#475569')
    expect(theme.textStrong).toBe('#0f172a')
  })
})
