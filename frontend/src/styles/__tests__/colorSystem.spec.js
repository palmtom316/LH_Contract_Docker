import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const tokensSource = readFileSync(
  path.resolve(process.cwd(), 'src/styles/tokens.scss'),
  'utf-8'
)

const layoutSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/Layout.vue'),
  'utf-8'
)

const sectionCardSource = readFileSync(
  path.resolve(process.cwd(), 'src/components/ui/AppSectionCard.vue'),
  'utf-8'
)

const metricCardSource = readFileSync(
  path.resolve(process.cwd(), 'src/components/ui/AppMetricCard.vue'),
  'utf-8'
)

describe('Color system refinement', () => {
  it('adds purposeful shell and card color tokens instead of leaving the chrome mostly neutral', () => {
    expect(tokensSource).toContain('--surface-topbar:')
    expect(tokensSource).toContain('--surface-sidebar-accent:')
    expect(tokensSource).toContain('--sidebar-active-rail:')
    expect(tokensSource).toContain('--workspace-panel-highlight:')
    expect(layoutSource).toContain('background: var(--surface-topbar);')
    expect(layoutSource).not.toContain('inset 3px 0 0 var(--sidebar-active-rail)')
    expect(layoutSource).toContain('background: var(--surface-sidebar-active);')
    expect(sectionCardSource).toContain('var(--workspace-panel-highlight)')
    expect(metricCardSource).toContain('var(--workspace-panel-highlight)')
  })
})
