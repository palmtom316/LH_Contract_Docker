import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const layoutSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/Layout.vue'),
  'utf-8'
)

describe('Layout sidebar shell', () => {
  it('uses a flat sidebar navigation without section headers or project stack card', () => {
    expect(layoutSource).toContain('sidebar-nav')
    expect(layoutSource).toContain('sidebar-nav__group')
    expect(layoutSource).toContain('sidebar-nav__group--secondary')
    expect(layoutSource).toContain('gap: 18px;')
    expect(layoutSource).toContain('gap: 2px;')
    expect(layoutSource).toContain('align-content: start;')
    expect(layoutSource).not.toContain('.sidebar-nav-item::after')
    expect(layoutSource).toContain('border-radius: var(--radius);')
    expect(layoutSource).toContain('background: var(--surface-sidebar-hover);')
    expect(layoutSource).toContain('min-height: var(--shell-header-band-height, var(--header-height));')
    expect(layoutSource).toContain('min-height: 40px;')
    expect(layoutSource).toContain('min-height: 44px;')
    expect(layoutSource).not.toContain('sidebar-section__label')
    expect(layoutSource).not.toContain('sidebar-stack-card')
    expect(layoutSource).not.toContain('Project Stack')
    expect(layoutSource).not.toContain('AppDeveloperIcon')
  })

  it('exposes the invoice import workbench from the primary navigation', () => {
    expect(layoutSource).toContain("index: '/invoice-imports'")
    expect(layoutSource).toContain("label: '发票挂账'")
    expect(layoutSource).toContain('userStore.canViewInvoices')
  })

  it('exposes warehouse management from the primary navigation', () => {
    expect(layoutSource).toContain("index: '/warehouse/overview'")
    expect(layoutSource).toContain("label: '库房管理'")
    expect(layoutSource).toContain('userStore.canViewWarehouseInventory')
  })
})
