import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { mount } from '@vue/test-utils'
import { useUiStore } from '../ui'
import AppMetricCard from '@/components/ui/AppMetricCard.vue'

const testDir = dirname(fileURLToPath(import.meta.url))
const tokensPath = resolve(testDir, '../../styles/tokens.scss')
const stylesPath = resolve(testDir, '../../styles/index.scss')
const loginViewPath = resolve(testDir, '../../views/Login.vue')
const sectionCardPath = resolve(testDir, '../../components/ui/AppSectionCard.vue')
const metricCardPath = resolve(testDir, '../../components/ui/AppMetricCard.vue')
const rangeFieldPath = resolve(testDir, '../../components/ui/AppRangeField.vue')

describe('ui store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    document.documentElement.removeAttribute('data-theme')
    document.documentElement.classList.remove('dark')
    document.documentElement.style.colorScheme = ''
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
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('rehydrates persisted theme and applies it during initTheme', () => {
    localStorage.setItem('lh-theme', 'dark')

    const store = useUiStore()

    expect(store.theme).toBe('dark')
    expect(document.documentElement.dataset.theme).toBeUndefined()

    store.initTheme()

    expect(document.documentElement.dataset.theme).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
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

  it('manages notification drawer open state through dedicated actions', () => {
    const store = useUiStore()

    expect(store.notificationDrawerOpen).toBe(false)

    store.openNotificationDrawer()
    expect(store.notificationDrawerOpen).toBe(true)

    store.closeNotificationDrawer()
    expect(store.notificationDrawerOpen).toBe(false)

    store.toggleNotificationDrawer()
    expect(store.notificationDrawerOpen).toBe(true)

    store.setNotificationDrawerOpen(false)
    expect(store.notificationDrawerOpen).toBe(false)
  })

  it('keeps legacy color token aliases mapped to semantic tokens', () => {
    const tokens = readFileSync(tokensPath, 'utf8')

    expect(tokens).toContain('--color-primary: var(--brand-primary);')
    expect(tokens).toContain('--color-text-main: var(--text-primary);')
    expect(tokens).toContain('--color-text-secondary: var(--text-secondary);')
  })

  it('keeps element-plus bridge and login theme surfaces tokenized', () => {
    const styles = readFileSync(stylesPath, 'utf8')
    const loginView = readFileSync(loginViewPath, 'utf8')

    expect(styles).toContain('--el-color-primary: hsl(var(--primary));')
    expect(styles).toContain('--el-bg-color: hsl(var(--card));')
    expect(styles).toContain('--el-text-color-primary: hsl(var(--foreground));')
    expect(styles).toContain('--el-border-color: hsl(var(--border));')

    expect(loginView).toContain('hsl(var(--background))')
    expect(loginView).toContain('hsl(var(--card))')
    expect(loginView).toContain('hsl(var(--muted)')
  })

  it('removes visible range separators from global date-range inputs', () => {
    const styles = readFileSync(stylesPath, 'utf8')
    const rangeField = readFileSync(rangeFieldPath, 'utf8')

    expect(styles).toContain('.el-date-editor .el-range-separator')
    expect(styles).toContain('font-size: 0;')
    expect(styles).toContain('padding-inline: 0;')
    expect(styles).toContain('width: 0;')
    expect(rangeField).not.toContain('border-right: 1px solid')
    expect(rangeField).not.toContain('height: 1px;')
  })

  it('defines elevated workspace surfaces for the premium light theme', () => {
    const tokens = readFileSync(tokensPath, 'utf8')
    const styles = readFileSync(stylesPath, 'utf8')
    const sectionCard = readFileSync(sectionCardPath, 'utf8')
    const metricCard = readFileSync(metricCardPath, 'utf8')

    expect(tokens).toContain('--surface-page-gradient:')
    expect(tokens).toContain('--surface-panel-elevated:')
    expect(tokens).toContain('--workspace-panel-shadow:')

    expect(styles).toContain('background: var(--surface-page-gradient);')
    expect(sectionCard).toContain('var(--surface-panel-elevated)')
    expect(sectionCard).toContain('var(--workspace-panel-shadow)')
    expect(metricCard).toContain('var(--surface-panel-elevated)')
    expect(metricCard).toContain('var(--workspace-panel-shadow)')
  })

  it('renders metric title and value content', () => {
    const wrapper = mount(AppMetricCard, {
      props: {
        title: '年度上游签约',
        value: '12 单'
      }
    })

    expect(wrapper.text()).toContain('年度上游签约')
    expect(wrapper.text()).toContain('12 单')
  })
})
