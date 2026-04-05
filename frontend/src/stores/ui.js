import { defineStore } from 'pinia'

const THEME_KEY = 'lh-theme'

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme
}

export const useUiStore = defineStore('ui', {
  state: () => ({
    theme: localStorage.getItem(THEME_KEY) || 'light',
    notificationDrawerOpen: false
  }),
  actions: {
    initTheme() {
      applyTheme(this.theme)
    },
    setTheme(theme) {
      this.theme = theme
      localStorage.setItem(THEME_KEY, theme)
      applyTheme(theme)
    },
    toggleTheme() {
      this.setTheme(this.theme === 'light' ? 'dark' : 'light')
    }
  }
})
