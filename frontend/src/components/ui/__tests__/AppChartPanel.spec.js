import { mount } from '@vue/test-utils'
import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import { describe, expect, it } from 'vitest'

const chartPanelPath = path.resolve(process.cwd(), 'src/components/ui/AppChartPanel.vue')

describe('AppChartPanel', () => {
  it('provides a shared chart surface with header and action slots', async () => {
    expect(existsSync(chartPanelPath)).toBe(true)

    const { default: AppChartPanel } = await import(pathToFileURL(chartPanelPath).href)
    const chartPanelSource = readFileSync(chartPanelPath, 'utf-8')

    const wrapper = mount(AppChartPanel, {
      slots: {
        header: '<span>回款趋势</span>',
        actions: '<button>切换</button>',
        default: '<div class="chart">chart</div>'
      }
    })

    expect(wrapper.find('.app-chart-panel').exists()).toBe(true)
    expect(wrapper.find('.app-chart-panel__header').exists()).toBe(true)
    expect(wrapper.find('.chart').exists()).toBe(true)
    expect(chartPanelSource).toContain('background: var(--surface-panel);')
    expect(chartPanelSource).toContain('border-radius: var(--radius);')
  })
})
