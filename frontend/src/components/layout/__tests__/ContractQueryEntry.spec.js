import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import ContractQueryEntry from '@/components/layout/ContractQueryEntry.vue'

const ElTooltipStub = {
  name: 'ElTooltip',
  template: '<div class="tooltip-stub"><slot /></div>'
}

describe('ContractQueryEntry', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders the topbar trigger with contract-query label semantics', () => {
    const wrapper = mount(ContractQueryEntry, {
      global: {
        stubs: {
          'el-tooltip': ElTooltipStub,
          'el-icon': true
        }
      }
    })

    const trigger = wrapper.get('[data-testid="contract-query-entry"]')
    expect(trigger.attributes('aria-label')).toBe('打开合同查询')
    expect(wrapper.text()).toContain('合同查询')
  })

  it('emits open when the icon is clicked', async () => {
    const wrapper = mount(ContractQueryEntry, {
      global: {
        stubs: {
          'el-tooltip': ElTooltipStub,
          'el-icon': true
        }
      }
    })

    await wrapper.get('[data-testid="contract-query-entry"]').trigger('click')

    expect(wrapper.emitted('open')).toHaveLength(1)
  })

  it('emits open for Ctrl+K and Cmd+K shortcuts', async () => {
    const wrapper = mount(ContractQueryEntry, {
      global: {
        stubs: {
          'el-tooltip': ElTooltipStub,
          'el-icon': true
        }
      }
    })

    const ctrlEvent = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true, cancelable: true })
    window.dispatchEvent(ctrlEvent)
    const metaEvent = new KeyboardEvent('keydown', { key: 'k', metaKey: true, bubbles: true, cancelable: true })
    window.dispatchEvent(metaEvent)

    expect(wrapper.emitted('open')).toHaveLength(2)
  })
})
