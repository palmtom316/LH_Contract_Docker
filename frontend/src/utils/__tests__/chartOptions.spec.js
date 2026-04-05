import { beforeEach, describe, expect, it } from 'vitest'
import { createBarChartOption } from '../chartOptions'

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
  })
})
