import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const desktopShell = readFileSync(
  path.resolve(process.cwd(), 'src/views/Layout.vue'),
  'utf-8'
)

describe('workspace shell visual contract', () => {
  it('removes glossy transform-based hover chrome from the desktop shell', () => {
    expect(desktopShell).not.toContain('translateX(-18%)')
    expect(desktopShell).not.toContain('.sidebar-nav-item::after')
    expect(desktopShell).toContain('border-radius: var(--radius);')
  })
})
