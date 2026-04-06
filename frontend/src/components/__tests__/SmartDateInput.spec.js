import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import SmartDateInput from '@/components/SmartDateInput.vue'

const ElInputStub = {
  props: ['modelValue', 'placeholder'],
  emits: ['update:modelValue', 'blur', 'keyup.enter'],
  template: `
    <input
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
      @blur="$emit('blur')"
      @keyup.enter="$emit('keyup.enter')"
    />
  `
}

function mountInput(props) {
  return mount(SmartDateInput, {
    props,
    global: {
      stubs: {
        'el-input': ElInputStub,
        'el-icon': true
      }
    }
  })
}

describe('SmartDateInput', () => {
  it('formats valid input on blur and emits iso date', async () => {
    const wrapper = mountInput({ modelValue: '' })
    await wrapper.find('input').setValue('26.4.6')
    await wrapper.find('input').trigger('blur')

    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['2026-04-06'])
    expect(wrapper.find('input').element.value).toBe('2026/04/06')
  })

  it('preserves invalid input and reports error state', async () => {
    const wrapper = mountInput({ modelValue: '2026-04-01' })
    await wrapper.find('input').setValue('2026/2/31')
    await wrapper.find('input').trigger('blur')

    expect(wrapper.emitted('update:modelValue')).toBeFalsy()
    expect(wrapper.find('input').element.value).toBe('2026/2/31')
    expect(wrapper.text()).toContain('日期格式无法识别')
  })

  it('clears the committed value when the field is emptied', async () => {
    const wrapper = mountInput({ modelValue: '2026-04-06' })
    await wrapper.find('input').setValue('')
    await wrapper.find('input').trigger('blur')

    expect(wrapper.emitted('update:modelValue')[0]).toEqual([null])
  })

  it('resyncs display and clears error after parent updates modelValue', async () => {
    const wrapper = mountInput({ modelValue: '2026-04-06' })
    await wrapper.find('input').setValue('2026/2/31')
    await wrapper.find('input').trigger('blur')

    expect(wrapper.text()).toContain('日期格式无法识别')

    await wrapper.setProps({ modelValue: '2026-04-10' })

    expect(wrapper.find('input').element.value).toBe('2026/04/10')
    expect(wrapper.text()).not.toContain('日期格式无法识别')
  })
})
