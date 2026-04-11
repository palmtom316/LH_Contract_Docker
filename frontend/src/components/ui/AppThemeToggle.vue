<template>
  <button
    type="button"
    class="theme-toggle app-chrome-icon-button"
    :aria-label="isDark ? '切换为浅色模式' : '切换为深色模式'"
    @click="uiStore.toggleTheme()"
  >
    <span class="theme-toggle__glyph" aria-hidden="true">
      <svg
        v-if="isDark"
        class="theme-toggle__icon"
        viewBox="0 0 20 20"
        fill="none"
      >
        <circle cx="10" cy="10" r="3.4" />
        <path d="M10 1.75v2.1" />
        <path d="M10 16.15v2.1" />
        <path d="M4.16 4.16l1.48 1.48" />
        <path d="M14.36 14.36l1.48 1.48" />
        <path d="M1.75 10h2.1" />
        <path d="M16.15 10h2.1" />
        <path d="M4.16 15.84l1.48-1.48" />
        <path d="M14.36 5.64l1.48-1.48" />
      </svg>
      <svg
        v-else
        class="theme-toggle__icon"
        viewBox="0 0 20 20"
        fill="none"
      >
        <path d="M12.92 2.72a6.68 6.68 0 1 0 4.36 11.74 7.18 7.18 0 0 1-4.62 1.65 7.18 7.18 0 0 1-7.17-7.17 7.18 7.18 0 0 1 7.43-7.22Z" />
        <path d="M14.4 4.3h2.1" />
        <path d="M15.45 3.25v2.1" />
      </svg>
      <span class="theme-toggle__orbit" />
    </span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()
const isDark = computed(() => uiStore.theme === 'dark')
</script>

<style scoped lang="scss">
.theme-toggle {
  cursor: pointer;
  position: relative;
}

.theme-toggle__glyph {
  position: relative;
  display: grid;
  place-items: center;
  width: 18px;
  height: 18px;
}

.theme-toggle__icon {
  position: relative;
  z-index: 1;
  width: 18px;
  height: 18px;
  stroke: color-mix(in srgb, var(--text-primary) 88%, var(--brand-primary-strong) 12%);
  stroke-width: 1.55;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.theme-toggle__orbit {
  position: absolute;
  inset: -2px;
  border: 1px solid color-mix(in srgb, var(--workspace-panel-border) 82%, var(--brand-primary-soft) 18%);
  border-radius: 999px;
  transition: transform 0.24s ease, border-color 0.24s ease, opacity 0.24s ease;
}

.theme-toggle:hover .theme-toggle__orbit,
.theme-toggle:focus-visible .theme-toggle__orbit {
  opacity: 1;
  transform: scale(1.08);
  border-color: color-mix(in srgb, var(--brand-primary) 28%, var(--workspace-panel-border) 72%);
}
</style>
