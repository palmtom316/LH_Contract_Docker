import { describe, expect, it } from 'vitest'
import { resolveHomePath } from '@/utils/homePath'

describe('resolveHomePath', () => {
  it('sends company storekeepers to the warehouse workspace', () => {
    expect(resolveHomePath({
      role: 'COMPANY_STOREKEEPER',
      permissions: ['view_warehouse_inventory'],
      isMobile: true
    })).toBe('/m/warehouse')
    expect(resolveHomePath({
      role: 'COMPANY_STOREKEEPER',
      permissions: ['view_warehouse_inventory'],
      isMobile: false
    })).toBe('/warehouse/overview')
  })

  it('keeps contract users on the existing home path', () => {
    expect(resolveHomePath({
      role: 'FINANCE',
      permissions: ['view_dashboard'],
      isMobile: false
    })).toBe('/')
  })
})
