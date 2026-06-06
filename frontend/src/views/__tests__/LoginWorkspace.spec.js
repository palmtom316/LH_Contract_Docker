import { flushPromises, shallowMount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import Login from '@/views/Login.vue'

const fetchConfigMock = vi.fn().mockResolvedValue(undefined)

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() })
}))

vi.mock('@/stores/system', () => ({
  useSystemStore: () => ({
    config: {
      system_name: '合同管理系统',
      system_name_line_2: 'Contract Workspace',
      system_logo: ''
    },
    fetchConfig: fetchConfigMock
  })
}))

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    login: vi.fn()
  })
}))

vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    ElMessage: { success: vi.fn(), error: vi.fn() }
  }
})

const ElInputStub = defineComponent({
  props: ['modelValue', 'type', 'placeholder', 'size', 'disabled'],
  template: '<div class="el-input-stub" />'
})

const mountPage = () =>
  shallowMount(Login, {
    global: {
      stubs: {
        ElForm: { template: '<form><slot /></form>' },
        ElFormItem: { template: '<div><slot /></div>' },
        ElInput: ElInputStub,
        ElButton: { template: '<button type="button"><slot /></button>' }
      }
    }
  })

const loginSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/Login.vue'),
  'utf-8'
)

describe('Login workspace shell', () => {
  it('renders login in a single workspace surface with configured system copy', async () => {
    const wrapper = mountPage()
    await flushPromises()

    expect(fetchConfigMock).toHaveBeenCalled()
    expect(wrapper.find('.login-shell').exists()).toBe(true)
    expect(wrapper.find('.login-shell__panel').exists()).toBe(true)
    expect(wrapper.find('.login-shell__header').exists()).toBe(true)
    expect(wrapper.find('.login-shell__form').exists()).toBe(true)
    expect(wrapper.find('.login-shell__brand').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('系统配置 / 基础设置')
    expect(wrapper.text()).toContain('合同管理系统')
    expect(wrapper.text()).toContain('Contract Workspace')
  })

  it('keeps the login surface aligned with the refined workspace tokens', () => {
    expect(loginSource).toContain('background: var(--surface-page-gradient);')
    expect(loginSource).toContain('background: color-mix(in srgb, hsl(var(--card)) 94%, hsl(var(--muted)) 6%);')
    expect(loginSource).toContain('border-radius: calc(var(--radius-lg) + 2px);')
    expect(loginSource).toContain('min-height: 40px;')
  })
})
