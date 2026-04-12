import fs from 'node:fs'
import path from 'node:path'

import { beforeEach, describe, expect, it } from 'vitest'

import { clearSessionStorage, persistSession } from '../authSession'


const diagnosePath = path.resolve(process.cwd(), 'public/diagnose.html')


describe('authSession', () => {
  beforeEach(() => {
    localStorage.clear()
    clearSessionStorage()
  })

  it('persistSession does not write refresh token to localStorage', () => {
    persistSession({
      accessToken: 'access-token',
      refreshToken: 'refresh-token',
      expiresIn: 7200,
      user: { id: 1, username: 'alice', permissions: [] }
    })

    expect(localStorage.getItem('token')).toBe('access-token')
    expect(localStorage.getItem('refresh_token')).toBeNull()
  })

  it('diagnose page does not read auth material from localStorage', () => {
    const html = fs.readFileSync(diagnosePath, 'utf-8')

    expect(html.includes("localStorage.getItem('token')")).toBe(false)
    expect(html.includes("localStorage.getItem('user_info')")).toBe(false)
  })
})
