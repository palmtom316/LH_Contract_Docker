import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useUserStore } from '@/stores/user'

describe('user store bootstrap', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    setActivePinia(createPinia())
  })

  it('falls back when persisted auth json is invalid', () => {
    sessionStorage.setItem('token', 'abc')
    sessionStorage.setItem('token_expires_at', '123456')
    sessionStorage.setItem('user_info', '{bad-json')
    sessionStorage.setItem('user_permissions', 'undefined')

    const store = useUserStore()

    expect(store.token).toBe('abc')
    expect(store.tokenExpiresAt).toBe('123456')
    expect(store.user).toEqual({})
    expect(store.permissions).toEqual([])
  })

  it('falls back when persisted auth json has unexpected shapes', () => {
    sessionStorage.setItem('user_info', '[]')
    sessionStorage.setItem('user_permissions', '{"admin":true}')

    const store = useUserStore()

    expect(store.user).toEqual({})
    expect(store.permissions).toEqual([])
  })

  it('allows invoice viewers and invoice operators to open the import workbench', () => {
    const store = useUserStore()

    store.permissions = ['view_invoices']
    expect(store.canViewInvoices).toBe(true)

    store.permissions = ['create_invoices']
    expect(store.canViewInvoices).toBe(true)

    store.permissions = []
    expect(store.canViewInvoices).toBe(false)

    store.user = { is_superuser: true }
    expect(store.canViewInvoices).toBe(true)
  })
})
