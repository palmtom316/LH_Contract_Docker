import { shallowMount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import Dashboard from '@/views/Dashboard.vue'

const dashboardSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/Dashboard.vue'),
  'utf-8'
)

const mountPage = () =>
  shallowMount(Dashboard, {
    global: {
      stubs: {
        Overview: { template: '<div class="overview-stub" />' },
        Business: { template: '<div class="business-stub" />' },
        AppWorkspacePanel: {
          props: ['panelClass'],
          template: '<section class="app-workspace-panel-stub" :class="panelClass"><slot /></section>'
        },
        ElTabs: { template: '<div><slot /></div>' },
        ElTabPane: { template: '<div><slot /></div>' }
      }
    }
  })

describe('Dashboard workspace shell', () => {
  it('renders the shared dashboard frame wrappers without the page header', () => {
    const wrapper = mountPage()

    expect(wrapper.find('.dashboard-page-header').exists()).toBe(false)
    expect(wrapper.find('.dashboard-shell').exists()).toBe(true)
    expect(wrapper.find('.dashboard-tabs-panel').exists()).toBe(true)
    expect(wrapper.find('.dashboard-tab-panel').exists()).toBe(true)
  })

  it('uses the refined workspace spacing rhythm in the dashboard shell', () => {
    expect(dashboardSource).toContain('gap: var(--space-5);')
    expect(dashboardSource).toContain('padding: var(--space-5);')
  })
})
