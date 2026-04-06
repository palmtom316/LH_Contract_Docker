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

  it('keeps controls in order and renders inline actions at the end', () => {
    const wrapper = mount(AppFilterBar, {
      props: { inlineActions: true },
      slots: {
        default:
          '<div class="filter-control--search">keyword</div><div class="filter-control--time">range</div>',
        actions: '<button>查询</button>'
      }
    })

    const items = wrapper.find('.app-filter-bar__main').findAll(':scope > *')
    expect(items[0].classes()).toContain('filter-control--search')
    expect(items[1].classes()).toContain('filter-control--time')
    const inlineActions = items[2]
    expect(inlineActions.classes()).toContain('app-filter-bar__actions--inline')
    expect(inlineActions.text()).toBe('查询')
  })
})
