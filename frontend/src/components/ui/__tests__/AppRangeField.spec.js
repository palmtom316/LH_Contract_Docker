import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AppRangeField from '@/components/ui/AppRangeField.vue'

const ElInputStub = {
  props: ['modelValue', 'placeholder'],
  emits: ['update:modelValue', 'blur', 'keyup.enter', 'clear'],
  template: `
    <div>
      <input
        :value="modelValue"
        :placeholder="placeholder"
        @input="$emit('update:modelValue', $event.target.value)"
        @blur="$emit('blur')"
        @keyup.enter="$emit('keyup.enter')"
      />
      <button type="button" data-test="clear" @click="$emit('clear')">clear</button>
    </div>
  `
}

function mountRange(props) {
  return mount(AppRangeField, {
    props,
    global: {
      stubs: {
        'el-input': ElInputStub,
        'el-icon': true
      }
    }
  })
}

describe('AppRangeField', () => {
  it('emits a normalized range when both dates are valid', async () => {
    const wrapper = mountRange({ modelValue: [] })
    const inputs = wrapper.findAll('input')

    await inputs[0].setValue('26/4/1')
    await inputs[0].trigger('blur')
    await inputs[1].setValue('26/4/6')
    await inputs[1].trigger('blur')

    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([['2026-04-01', '2026-04-06']])
  })

  it('keeps a partial range when only one side is valid', async () => {
    const wrapper = mountRange({ modelValue: [] })
    const inputs = wrapper.findAll('input')

    await inputs[0].setValue('2026/04/01')
    await inputs[0].trigger('blur')
    await inputs[1].setValue('2026/2/31')
    await inputs[1].trigger('blur')

    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([['2026-04-01', '']])
  })

  it('shows range-order error and blocks the range when start is after end', async () => {
    const wrapper = mountRange({ modelValue: [] })
    const inputs = wrapper.findAll('input')

    await inputs[0].setValue('2026/04/08')
    await inputs[0].trigger('blur')
    await inputs[1].setValue('2026/04/06')
    await inputs[1].trigger('blur')

    expect(wrapper.text()).toContain('开始日期不能晚于结束日期')
    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([['', '']])
  })
})
