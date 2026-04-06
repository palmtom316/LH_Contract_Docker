import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ContractQueryBot from '@/components/ContractQueryBot.vue'

const ElDialogStub = {
  props: ['modelValue'],
  template: `
    <div>
      <slot />
    </div>
  `
}
const ElTooltipStub = {
  template: `
    <div>
      <slot />
    </div>
  `
}

describe('ContractQueryBot', () => {
  it('renders text date range inputs instead of a date picker', async () => {
    const wrapper = mount(ContractQueryBot, {
      global: {
        stubs: {
          'el-dialog': ElDialogStub,
          'el-tooltip': ElTooltipStub,
          'el-icon': true,
          'el-button': true,
          'el-input': true,
          'el-date-picker': true,
          'el-alert': true,
          'el-skeleton': true,
          'el-empty': true,
          'el-tag': true,
          'el-collapse': true,
          'el-collapse-item': true,
          'el-descriptions': true,
          'el-descriptions-item': true,
          'el-table': true,
          'el-table-column': true,
          AppRangeField: true,
          DictSelect: true
        }
      }
    })

    await wrapper.find('.bot-button').trigger('click')

    expect(wrapper.findComponent({ name: 'AppRangeField' }).exists()).toBe(true)
    expect(wrapper.html()).not.toContain('el-date-picker')
  })
})
