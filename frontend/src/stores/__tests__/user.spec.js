import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useUserStore } from '@/stores/user'

describe('user store bootstrap', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('falls back when persisted auth json is invalid', () => {
    localStorage.setItem('token', 'abc')
    localStorage.setItem('token_expires_at', '123456')
    localStorage.setItem('user_info', '{bad-json')
    localStorage.setItem('user_permissions', 'undefined')

    const store = useUserStore()

    expect(store.token).toBe('abc')
    expect(store.tokenExpiresAt).toBe('123456')
    expect(store.user).toEqual({})
    expect(store.permissions).toEqual([])
  })

  it('falls back when persisted auth json has unexpected shapes', () => {
    localStorage.setItem('user_info', '[]')
    localStorage.setItem('user_permissions', '{"admin":true}')

    const store = useUserStore()

    expect(store.user).toEqual({})
    expect(store.permissions).toEqual([])
  })
})
