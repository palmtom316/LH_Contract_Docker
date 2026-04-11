import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const mobileShell = readFileSync(
  path.resolve(process.cwd(), 'src/views/mobile/MobileLayout.vue'),
  'utf-8'
)

describe('mobile shell visual contract', () => {
  it('aligns mobile shell radii and surfaces to the shared token values', () => {
    expect(mobileShell).not.toContain('border-radius: 24px')
    expect(mobileShell).toContain('border-radius: var(--radius-lg);')
    expect(mobileShell).toContain('background: hsl(var(--card));')
  })
})
