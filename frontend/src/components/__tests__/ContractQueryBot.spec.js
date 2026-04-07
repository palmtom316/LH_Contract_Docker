import { mount } from '@vue/test-utils'
import { describe, expect, it, vi, beforeEach } from 'vitest'
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
const AppRangeFieldStub = {
  name: 'AppRangeField',
  emits: ['update:modelValue'],
  template: '<div />'
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
  AppRangeField: AppRangeFieldStub,
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
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders text date range inputs instead of a date picker', async () => {
    const wrapper = createWrapper()

    await wrapper.find('.bot-button').trigger('click')

    expect(wrapper.findComponent({ name: 'AppRangeField' }).exists()).toBe(true)
    expect(wrapper.html()).not.toContain('el-date-picker')
  })

  it('ignores an empty AppRangeField payload without applying a date filter', async () => {
    const wrapper = createWrapper()

    await wrapper.find('.bot-button').trigger('click')

    const warningSpy = vi.spyOn(ElMessage, 'warning')
    const rangeField = wrapper.findComponent({ name: 'AppRangeField' })
    await rangeField.vm.$emit('update:modelValue', ['', ''])
    await wrapper.vm.$nextTick()

    await wrapper.find('.search-btn').trigger('click')

    expect(warningSpy).toHaveBeenCalledWith('请至少输入一个搜索条件')
    expect(wrapper.vm.signDateRange).toEqual(['', ''])
    expect(searchContracts).not.toHaveBeenCalled()

    warningSpy.mockRestore()
  })

  it('sends the committed range through to searchContracts', async () => {
    const wrapper = createWrapper()

    await wrapper.find('.bot-button').trigger('click')

    const rangeField = wrapper.findComponent({ name: 'AppRangeField' })
    await rangeField.vm.$emit('update:modelValue', ['2026-04-01', '2026-04-06'])
    await wrapper.vm.$nextTick()

    await wrapper.find('.search-btn').trigger('click')

    expect(searchContracts).toHaveBeenCalledWith({
      query: '',
      companyCategory: '',
      partyAName: '',
      partyBName: '',
      signDateStart: '2026-04-01',
      signDateEnd: '2026-04-06'
    })
  })
})
