import { defineStore } from 'pinia'

const THEME_KEY = 'lh-theme'
const DEFAULT_THEME = 'light'
const VALID_THEMES = new Set(['light', 'dark'])

function normalizeTheme(theme) {
  return VALID_THEMES.has(theme) ? theme : DEFAULT_THEME
}

function getStorage() {
  return typeof globalThis.localStorage === 'undefined' ? null : globalThis.localStorage
}

function readStoredTheme() {
  const storage = getStorage()
  if (!storage) return DEFAULT_THEME

  try {
    return normalizeTheme(storage.getItem(THEME_KEY))
  } catch {
    return DEFAULT_THEME
  }
}

function persistTheme(theme) {
  const storage = getStorage()
  if (!storage) return

  try {
    storage.setItem(THEME_KEY, theme)
  } catch {
    // Ignore storage persistence failures (e.g. restricted runtimes).
  }
}

function applyTheme(theme) {
  if (typeof globalThis.document === 'undefined') return
  globalThis.document.documentElement.dataset.theme = theme
}

export const useUiStore = defineStore('ui', {
  state: () => ({
    theme: readStoredTheme(),
    notificationDrawerOpen: false
  }),
  actions: {
    initTheme() {
      applyTheme(this.theme)
    },
    setTheme(theme) {
      const normalizedTheme = normalizeTheme(theme)
      this.theme = normalizedTheme
      persistTheme(normalizedTheme)
      applyTheme(normalizedTheme)
    },
    toggleTheme() {
      this.setTheme(this.theme === 'light' ? 'dark' : 'light')
    }
  }
})
