import { shallowMount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import Dashboard from '@/views/Dashboard.vue'

const mountPage = () =>
  shallowMount(Dashboard, {
    global: {
      stubs: {
        Overview: { template: '<div class="overview-stub" />' },
        Business: { template: '<div class="business-stub" />' },
        AppPageHeader: { template: '<div class="app-page-header-stub"><slot name="actions" /></div>' },
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
  it('renders the shared dashboard header and frame wrappers', () => {
    const wrapper = mountPage()

    expect(wrapper.find('.dashboard-page-header').exists()).toBe(true)
    expect(wrapper.find('.dashboard-shell').exists()).toBe(true)
    expect(wrapper.find('.dashboard-tabs-panel').exists()).toBe(true)
    expect(wrapper.find('.dashboard-tab-panel').exists()).toBe(true)
  })
})
