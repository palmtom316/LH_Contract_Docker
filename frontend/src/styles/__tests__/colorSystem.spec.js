import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const tokens = readFileSync(
  path.resolve(process.cwd(), 'src/styles/tokens.scss'),
  'utf-8'
)

const globals = readFileSync(
  path.resolve(process.cwd(), 'src/styles/index.scss'),
  'utf-8'
)

describe('visual token contract', () => {
  it('keeps a compact radius ladder with a cool minimalist SaaS neutral palette', () => {
    expect(tokens).toContain('--radius: 0.75rem;')
    expect(tokens).toContain('--radius-lg: 1rem;')
    expect(tokens).toContain('--background: 220 16% 97%;')
    expect(tokens).toContain('--card: 0 0% 100%;')
    expect(tokens).toContain('--muted: 220 14% 95%;')
    expect(tokens).toContain('--primary: 160 52% 39%;')
    expect(tokens).toContain('--workspace-control-height: 36px;')
    expect(tokens).toContain(
      '--surface-page-gradient: linear-gradient(180deg, hsl(var(--background)) 0%, color-mix(in srgb, hsl(var(--background)) 82%, hsl(var(--card)) 18%) 100%);'
    )
    expect(tokens).not.toContain('radial-gradient(circle at top left')
    expect(tokens).not.toContain('--workspace-panel-highlight:')
    expect(tokens).toContain('--shadow-frame: 0 8px 24px hsl(220 24% 14% / 0.06);')
    expect(tokens).not.toContain('0.625rem')
  })

  it('binds Element Plus controls to token-driven radius and surface values', () => {
    expect(globals).toContain('--el-box-shadow: var(--shadow-card);')
    expect(globals).toContain('border-radius: var(--radius);')
    expect(globals).toContain('min-height: var(--workspace-control-height);')
    expect(globals).toContain('transform 180ms ease')
    expect(globals).not.toContain('border-radius: 10px;')
    expect(globals).not.toContain('background: var(--surface-panel-elevated);')
  })
})
