import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const layoutSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/Layout.vue'),
  'utf-8'
)

const themeToggleSource = readFileSync(
  path.resolve(process.cwd(), 'src/components/ui/AppThemeToggle.vue'),
  'utf-8'
)

const notificationBellSource = readFileSync(
  path.resolve(process.cwd(), 'src/components/layout/AppNotificationBell.vue'),
  'utf-8'
)

const topbarActionsSource = readFileSync(
  path.resolve(process.cwd(), 'src/components/layout/AppTopbarActions.vue'),
  'utf-8'
)

const globalStylesSource = readFileSync(
  path.resolve(process.cwd(), 'src/styles/index.scss'),
  'utf-8'
)

describe('Layout topbar icon actions', () => {
  it('uses the shared chrome icon button style for the topbar icon controls', () => {
    expect(layoutSource).toContain('class="menu-btn app-chrome-icon-button"')
    expect(themeToggleSource).toContain('class="theme-toggle app-chrome-icon-button"')
    expect(notificationBellSource).toContain('notification-bell--has-unread')
    expect(topbarActionsSource).toContain('padding: 4px;')
    expect(topbarActionsSource).toContain('border-radius: 16px;')
    expect(topbarActionsSource).toContain('backdrop-filter: blur(14px);')
    expect(globalStylesSource).toContain('.app-chrome-icon-button {')
    expect(globalStylesSource).toContain('border: 1px solid var(--workspace-panel-border);')
    expect(globalStylesSource).toContain('background: var(--surface-panel-elevated);')
    expect(globalStylesSource).toContain('box-shadow: var(--shadow-soft);')
    expect(globalStylesSource).toContain('border-radius: 12px;')
    expect(globalStylesSource).toContain('.app-chrome-icon-button::after {')
    expect(globalStylesSource).toContain('prefers-reduced-motion: reduce')
  })
})
