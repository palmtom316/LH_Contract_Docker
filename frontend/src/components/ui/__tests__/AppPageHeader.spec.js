import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'

describe('AppPageHeader', () => {
  it('renders eyebrow, title, description, and actions', () => {
    const wrapper = mount(AppPageHeader, {
      props: {
        eyebrow: 'Contracts',
        title: 'Upstream Contracts',
        description: 'Manage upstream contract records.'
      },
      slots: {
        actions: '<button type="button" class="header-action">New Contract</button>'
      }
    })

    expect(wrapper.find('.app-page-header').exists()).toBe(true)
    expect(wrapper.find('.app-page-header__eyebrow').text()).toBe('Contracts')
    expect(wrapper.find('.app-page-header__title').text()).toBe('Upstream Contracts')
    expect(wrapper.find('.app-page-header__description').text()).toBe('Manage upstream contract records.')
    expect(wrapper.find('.app-page-header__actions').exists()).toBe(true)
  })
})
