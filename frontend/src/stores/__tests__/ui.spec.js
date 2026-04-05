import { beforeEach, describe, expect, it } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUiStore } from '../ui'

describe('ui store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    document.documentElement.removeAttribute('data-theme')
  })

  it('defaults to light theme and persists manual toggle', () => {
    const store = useUiStore()

    expect(store.theme).toBe('light')

    store.setTheme('dark')

    expect(store.theme).toBe('dark')
    expect(localStorage.getItem('lh-theme')).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
  })
})
