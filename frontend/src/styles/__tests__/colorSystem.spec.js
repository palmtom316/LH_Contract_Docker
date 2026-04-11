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
  it('keeps a compact radius ladder and removes ornate shell gradients', () => {
    expect(tokens).toContain('--radius: 0.75rem;')
    expect(tokens).toContain('--radius-lg: 1rem;')
    expect(tokens).toContain(
      '--surface-page-gradient: linear-gradient(180deg, hsl(var(--background)), hsl(var(--background)));'
    )
    expect(tokens).not.toContain('radial-gradient(circle at top left')
    expect(tokens).not.toContain('--workspace-panel-highlight:')
    expect(tokens).not.toContain('0 14px 34px')
    expect(tokens).not.toContain('0 20px 52px')
    expect(tokens).not.toContain('0.625rem')
  })

  it('binds Element Plus controls to token-driven radius and surface values', () => {
    expect(globals).toContain('--el-box-shadow: var(--shadow-card);')
    expect(globals).toContain('border-radius: var(--radius);')
    expect(globals).not.toContain('border-radius: 10px;')
    expect(globals).not.toContain('background: var(--surface-panel-elevated);')
  })
})
