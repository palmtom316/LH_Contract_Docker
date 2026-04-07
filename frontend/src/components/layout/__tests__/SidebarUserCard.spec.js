import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const sidebarUserCardSource = readFileSync(
  path.resolve(process.cwd(), 'src/components/layout/SidebarUserCard.vue'),
  'utf-8'
)

describe('SidebarUserCard', () => {
  it('uses the same flat navigation button language as the sidebar items', () => {
    expect(sidebarUserCardSource).toContain('class="user-menu__icon"')
    expect(sidebarUserCardSource).toContain('background: transparent;')
    expect(sidebarUserCardSource).toContain('border: 0;')
    expect(sidebarUserCardSource).toContain('min-height: 40px;')
    expect(sidebarUserCardSource).toContain('padding: 4px 10px;')
    expect(sidebarUserCardSource).toContain('.user-menu__trigger:hover')
    expect(sidebarUserCardSource).toContain('.user-menu__trigger.is-open')
    expect(sidebarUserCardSource).toContain('.user-menu__icon {')
    expect(sidebarUserCardSource).toContain('width: 32px;')
    expect(sidebarUserCardSource).toContain('height: 32px;')
    expect(sidebarUserCardSource).not.toContain('box-shadow: var(--shadow-soft);')
  })
})
