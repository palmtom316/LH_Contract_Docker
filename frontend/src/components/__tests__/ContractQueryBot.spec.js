import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { ElMessage, ElAlert } from 'element-plus'
import ContractQueryBot from '@/components/ContractQueryBot.vue'
import { searchContracts } from '@/api/contractSearch'

vi.mock('@/api/contractSearch', () => ({
  searchContracts: vi.fn(() =>
    Promise.resolve({
      results: [],
      downstream_results: [],
      management_results: [],
      summary: null
    })
  )
}))

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
const commonStubs = {
  'el-dialog': ElDialogStub,
  'el-tooltip': ElTooltipStub,
  'el-icon': true,
  'el-button': true,
  'el-input': true,
  'el-date-picker': true,
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
const createWrapper = () =>
  mount(ContractQueryBot, {
    global: {
      stubs: commonStubs,
      components: { ElAlert }
    }
  })

describe('ContractQueryBot', () => {
  it('renders text date range inputs instead of a date picker', async () => {
    const wrapper = createWrapper()

    await wrapper.find('.bot-button').trigger('click')

    expect(wrapper.findComponent({ name: 'AppRangeField' }).exists()).toBe(true)
    expect(wrapper.html()).not.toContain('el-date-picker')
  })

  it('ignores an empty AppRangeField payload as a date filter and reiterates guidance text', async () => {
    const wrapper = createWrapper()

    await wrapper.find('.bot-button').trigger('click')

    const warningSpy = vi.spyOn(ElMessage, 'warning')
    const rangeRef = wrapper.vm.$.setupState.signDateRange
    rangeRef.value = ['', '']

    await wrapper.find('.search-btn').trigger('click')

    expect(warningSpy).toHaveBeenCalledWith('请至少输入一个搜索条件')
    expect(rangeRef.value).toEqual(['', ''])
    expect(searchContracts).not.toHaveBeenCalled()

    const tipSection = wrapper.find('.tip-section')
    const tipText = tipSection.text()
    expect(tipText).toContain('签约时间范围')
    expect(tipText).toContain('26.4.6')

    warningSpy.mockRestore()
  })
})
