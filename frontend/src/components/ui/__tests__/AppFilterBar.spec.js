import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AppFilterBar from '@/components/ui/AppFilterBar.vue'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const appFilterBarSource = readFileSync(
  path.resolve(process.cwd(), 'src/components/ui/AppFilterBar.vue'),
  'utf-8'
)

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

  it('documents the medium breakpoint grid spans for range-wide and inline actions', () => {
    const mediaIndex = appFilterBarSource.indexOf('@media (max-width: 1280px)')
    expect(mediaIndex).toBeGreaterThan(-1)

    const rangeIndex = appFilterBarSource.indexOf('filter-control--range-wide', mediaIndex)
    expect(rangeIndex).toBeGreaterThan(mediaIndex)
    expect(appFilterBarSource.indexOf('grid-column: span 4', rangeIndex)).toBeGreaterThan(rangeIndex)
    expect(appFilterBarSource.indexOf('grid-row: 2', rangeIndex)).toBeGreaterThan(rangeIndex)

    const actionsIndex = appFilterBarSource.indexOf('app-filter-bar__actions--inline', mediaIndex)
    expect(actionsIndex).toBeGreaterThan(mediaIndex)
    expect(appFilterBarSource.indexOf('grid-column: 7 / -1', actionsIndex)).toBeGreaterThan(actionsIndex)
    expect(appFilterBarSource.indexOf('grid-row: 1', actionsIndex)).toBeGreaterThan(actionsIndex)
  })
})
