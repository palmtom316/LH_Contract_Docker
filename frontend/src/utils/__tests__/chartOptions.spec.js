import { beforeEach, describe, expect, it } from 'vitest'
import { createBarChartOption, createPieChartOption } from '../chartOptions'
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
    expect(option.legend.bottom).toBe(0)
    expect(option.xAxis.axisLabel.hideOverlap).toBe(true)
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
  it('moves pie labels outside the plot area', () => {
    const option = createPieChartOption({
      title: '合同分类',
      data: [{ name: '工程', value: 30 }]
    })

    expect(option.series[0].label.position).toBe('outside')
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
