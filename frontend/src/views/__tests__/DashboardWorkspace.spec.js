import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import Dashboard from '@/views/Dashboard.vue'

const mountPage = () =>
  mount(Dashboard, {
    global: {
      stubs: {
        Overview: { template: '<div class="overview-stub" />' },
        Business: { template: '<div class="business-stub" />' },
        ElTabs: { template: '<div><slot /></div>' },
        ElTabPane: { template: '<div><slot /></div>' }
      }
    }
  })

describe('Dashboard workspace shell', () => {
  it('renders the dashboard shell wrapper', () => {
    const wrapper = mountPage()

    expect(wrapper.find('.dashboard-shell').exists()).toBe(true)
  })
})
