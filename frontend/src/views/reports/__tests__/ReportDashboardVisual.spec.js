import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const overview = readFileSync(
  path.resolve(process.cwd(), 'src/views/home/Overview.vue'),
  'utf-8'
)
const business = readFileSync(
  path.resolve(process.cwd(), 'src/views/home/Business.vue'),
  'utf-8'
)
const reports = readFileSync(
  path.resolve(process.cwd(), 'src/views/reports/ReportDashboard.vue'),
  'utf-8'
)

describe('dashboard and reports visual contract', () => {
  it('uses shared chart panel wrappers instead of ad-hoc chart card shells', () => {
    expect(overview).toContain('AppChartPanel')
    expect(business).toContain('AppChartPanel')
    expect(reports).toContain('AppSectionCard')
  })

  it('removes hand-crafted inline chart option islands from business dashboard', () => {
    expect(business).not.toContain('resultChart.setOption({')
    expect(business).not.toContain('trendChart.setOption({')
  })
})
