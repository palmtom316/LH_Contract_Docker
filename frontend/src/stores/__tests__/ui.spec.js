import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { useUiStore } from '../ui'

const testDir = dirname(fileURLToPath(import.meta.url))
const tokensPath = resolve(testDir, '../../styles/tokens.scss')

describe('ui store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    document.documentElement.removeAttribute('data-theme')
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('defaults to light theme and persists manual toggle', () => {
    const store = useUiStore()

    expect(store.theme).toBe('light')

    store.setTheme('dark')

    expect(store.theme).toBe('dark')
    expect(localStorage.getItem('lh-theme')).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('rehydrates persisted theme and applies it during initTheme', () => {
    localStorage.setItem('lh-theme', 'dark')

    const store = useUiStore()

    expect(store.theme).toBe('dark')
    expect(document.documentElement.dataset.theme).toBeUndefined()

    store.initTheme()

    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('does not crash when browser globals are unavailable', () => {
    vi.stubGlobal('localStorage', undefined)
    vi.stubGlobal('document', undefined)
    setActivePinia(createPinia())

    const store = useUiStore()

    expect(store.theme).toBe('light')
    expect(() => store.initTheme()).not.toThrow()
    expect(() => store.setTheme('dark')).not.toThrow()
    expect(store.theme).toBe('dark')
  })

  it('keeps legacy color token aliases mapped to semantic tokens', () => {
    const tokens = readFileSync(tokensPath, 'utf8')

    expect(tokens).toContain('--color-primary: var(--brand-primary);')
    expect(tokens).toContain('--color-text-main: var(--text-primary);')
    expect(tokens).toContain('--color-text-secondary: var(--text-secondary);')
  })
})
