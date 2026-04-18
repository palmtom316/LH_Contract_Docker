import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const desktopShell = readFileSync(
  path.resolve(process.cwd(), 'src/views/Layout.vue'),
  'utf-8'
)

describe('workspace shell visual contract', () => {
  it('keeps the shell flat so page content owns its own surface hierarchy', () => {
    expect(desktopShell).not.toContain('translateX(-18%)')
    expect(desktopShell).not.toContain('.sidebar-nav-item::after')
    expect(desktopShell).toContain('background: var(--surface-page-gradient);')
    expect(desktopShell).toContain('box-shadow: var(--shadow-soft);')
    expect(desktopShell).toContain('border-radius: var(--radius);')
    expect(desktopShell).not.toMatch(/\.app-main__frame\s*\{[^}]*box-shadow/)
    expect(desktopShell).not.toMatch(/\.app-main__frame\s*\{[^}]*border:\s*1px/)
  })
})
