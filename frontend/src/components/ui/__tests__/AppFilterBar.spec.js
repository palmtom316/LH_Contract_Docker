import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AppFilterBar from '@/components/ui/AppFilterBar.vue'

describe('AppFilterBar', () => {
  it('renders inline actions after filter controls', () => {
    const wrapper = mount(AppFilterBar, {
      props: { inlineActions: true },
      slots: {
        default:
          '<div class="filter-control--search">keyword</div><div class="filter-control--time">range</div>',
        actions: '<button>查询</button>'
      }
    })

    expect(wrapper.find('.app-filter-bar__actions--inline').exists()).toBe(true)
  })
})
