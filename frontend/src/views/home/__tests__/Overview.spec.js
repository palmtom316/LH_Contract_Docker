import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const overviewSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/home/Overview.vue'),
  'utf-8'
)

describe('Overview metric cards', () => {
  it('does not include eyebrow copy in the top four summary cards', () => {
    expect(overviewSource).toContain("eyebrow: ''")
    expect(overviewSource).not.toContain("eyebrow: '年度经营'")
    expect(overviewSource).toContain(":eyebrow=\"item.eyebrow\"")
  })
})

describe('Overview chart composition', () => {
  it('uses dashboard ranking helpers instead of pie chart initialization for category summaries', () => {
    expect(overviewSource).toContain("from '@/utils/dashboardRanking'")
    expect(overviewSource).toContain('createHorizontalRankOption')
    expect(overviewSource).not.toContain('createPieChartOption')
    expect(overviewSource).not.toContain('initCategoryPie')
    expect(overviewSource).not.toContain('initCompanyPie')
  })

  it('places the 30 day and 90 day business sections in separate full-width cards before the category rankings', () => {
    const monthlyIndex = overviewSource.indexOf('近30天经营表现')
    const quarterlyIndex = overviewSource.indexOf('近90天经营表现')
    const categoryIndex = overviewSource.indexOf('合同分类')

    expect(monthlyIndex).toBeGreaterThan(-1)
    expect(quarterlyIndex).toBeGreaterThan(monthlyIndex)
    expect(categoryIndex).toBeGreaterThan(quarterlyIndex)
    expect(overviewSource).not.toContain('class="period-grid"')
    expect(overviewSource).toContain('class="period-stack"')
  })
})
