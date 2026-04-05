import { computed } from 'vue'
import { useUiStore } from '@/stores/ui'

export function useTheme() {
  const uiStore = useUiStore()

  return {
    theme: computed(() => uiStore.theme),
    isDark: computed(() => uiStore.theme === 'dark'),
    setTheme: uiStore.setTheme,
    toggleTheme: uiStore.toggleTheme
  }
}
