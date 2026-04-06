import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'

describe('AppPageHeader', () => {
  it('renders eyebrow, title, description, meta, and actions within the shared side wrapper', () => {
    const wrapper = mount(AppPageHeader, {
      props: {
        eyebrow: 'Contracts',
        title: 'Upstream Contracts',
        description: 'Manage upstream contract records.',
        meta: '12 active contracts'
      },
      slots: {
        actions: '<button type="button" class="header-action">New Contract</button>'
      }
    })

    expect(wrapper.find('.app-page-header').exists()).toBe(true)
    expect(wrapper.find('.app-page-header__eyebrow').text()).toBe('Contracts')
    expect(wrapper.find('.app-page-header__title').text()).toBe('Upstream Contracts')
    expect(wrapper.find('.app-page-header__description').text()).toBe('Manage upstream contract records.')
    expect(wrapper.find('.app-page-header__side').exists()).toBe(true)
    expect(wrapper.find('.app-page-header__meta').text()).toBe('12 active contracts')
    expect(wrapper.find('.app-page-header__actions').text()).toContain('New Contract')
  })
})
