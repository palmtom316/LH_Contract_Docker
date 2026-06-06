import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import AppMetricCard from '@/components/ui/AppMetricCard.vue'

const metricCardSource = readFileSync(
  path.resolve(process.cwd(), 'src/components/ui/AppMetricCard.vue'),
  'utf-8'
)

describe('AppMetricCard', () => {
  it('renders metric cards as quiet bordered surfaces without decorative highlight rails', () => {
    const wrapper = mount(AppMetricCard, {
      props: {
        eyebrow: '指标',
        title: '年度回款',
        value: '¥ 120 万'
      }
    })

    expect(wrapper.classes()).toContain('app-metric-card')
    expect(wrapper.find('.app-metric-card__value').text()).toContain('120')
    expect(metricCardSource).toContain('border-radius: calc(var(--radius) + 2px);')
    expect(metricCardSource).toContain('padding: 18px;')
    expect(metricCardSource).toContain('transform 180ms ease')
    expect(metricCardSource).not.toContain('::before')
    expect(metricCardSource).not.toContain('22px')
  })
})
