import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import SmartDateInput from '@/components/SmartDateInput.vue'

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

  it('clears the committed value when using the clear action', async () => {
    const wrapper = mountInput({ modelValue: '2026-04-06' })
    await wrapper.find('[data-test="clear"]').trigger('click')

    expect(wrapper.emitted('update:modelValue')[0]).toEqual([null])
    expect(wrapper.text()).not.toContain('日期格式无法识别')
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

  it('emits a single null update when clear is followed by blur', async () => {
    const wrapper = mountInput({ modelValue: '2026-04-06' })
    await wrapper.find('[data-test="clear"]').trigger('click')
    await wrapper.find('input').trigger('blur')

    const updates = wrapper.emitted('update:modelValue') || []
    const nullUpdates = updates.filter(([value]) => value === null)
    expect(nullUpdates).toHaveLength(1)

    const validity = wrapper.emitted('validity-change') || []
    const nullValidity = validity.filter(([payload]) => payload?.value === null)
    expect(nullValidity).toHaveLength(1)
  })

  it('emits a new value after clear then new input on blur', async () => {
    const wrapper = mountInput({ modelValue: '2026-04-06' })
    await wrapper.find('[data-test="clear"]').trigger('click')
    await wrapper.find('input').setValue('2026/4/10')
    await wrapper.find('input').trigger('blur')

    const updates = wrapper.emitted('update:modelValue') || []
    const values = updates.map(([value]) => value)
    expect(values).toContain('2026-04-10')
  })

  it('clears after resync and emits a single null update on manual clear', async () => {
    const wrapper = mountInput({ modelValue: '2026-04-06' })
    await wrapper.find('[data-test="clear"]').trigger('click')
    await wrapper.setProps({ modelValue: '2026-04-10' })
    const updatesBefore = wrapper.emitted('update:modelValue') || []
    const nullCountBefore = updatesBefore.filter(([value]) => value === null).length
    await wrapper.find('input').setValue('')
    await wrapper.find('input').trigger('blur')

    const updates = wrapper.emitted('update:modelValue') || []
    const nullCountAfter = updates.filter(([value]) => value === null).length
    expect(nullCountAfter - nullCountBefore).toBe(1)
  })
})
