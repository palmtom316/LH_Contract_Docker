import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const businessSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/home/Business.vue'),
  'utf-8'
)

describe('Business metric cards', () => {
  it('reuses the shared metric card component for the top summary cards without the eyebrow copy', () => {
    expect(businessSource).toContain("import AppMetricCard from '@/components/ui/AppMetricCard.vue'")
    expect(businessSource).toContain('<AppMetricCard')
    expect(businessSource).toContain(":eyebrow=\"''\"")
    expect(businessSource).not.toContain('<article class="metric-card')
  })
})

describe('Business chart composition', () => {
  it('drops pie and rose chart rendering in favor of ranking and stacked bars', () => {
    expect(businessSource).toContain("from '@/utils/dashboardRanking'")
    expect(businessSource).toContain('createHorizontalRankOption')
    expect(businessSource).toContain('createStackedCategoryOption')
    expect(businessSource).not.toContain("type: \"pie\"")
    expect(businessSource).not.toContain('roseType')
  })
})
