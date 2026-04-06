import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import Login from '@/views/Login.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() })
}))

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    login: vi.fn()
  })
}))

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn() }
}))

const mountPage = () =>
  mount(Login, {
    global: {
      stubs: {
        ElForm: { template: '<form><slot /></form>' },
        ElFormItem: { template: '<div><slot /></div>' },
        ElInput: { template: '<input />' },
        ElButton: { template: '<button type="button"><slot /></button>' }
      }
    }
  })

describe('Login workspace shell', () => {
  it('wraps login in the shared login shell', () => {
    const wrapper = mountPage()

    expect(wrapper.find('.login-shell').exists()).toBe(true)
  })
})
