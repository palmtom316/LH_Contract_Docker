import { describe, expect, it } from 'vitest'
import { getFileUrl } from '@/utils/common'

describe('common file URL helpers', () => {
  it('routes legacy upload paths through protected file endpoint', () => {
    expect(getFileUrl('/uploads/contracts/2026/04/demo.pdf')).toBe(
      '/api/v1/common/files/contracts/2026/04/demo.pdf'
    )
    expect(getFileUrl('/app/uploads/contracts/2026/04/demo.pdf')).toBe(
      '/api/v1/common/files/contracts/2026/04/demo.pdf'
    )
    expect(getFileUrl('contracts/2026/04/demo.pdf')).toBe(
      '/api/v1/common/files/contracts/2026/04/demo.pdf'
    )
  })

  it('keeps already-built API file URLs unchanged', () => {
    expect(getFileUrl('/api/v1/common/files/contracts/2026/04/demo.pdf')).toBe(
      '/api/v1/common/files/contracts/2026/04/demo.pdf'
    )
    expect(getFileUrl('https://example.test/api/v1/common/files/uploads/contracts/2026/04/demo.pdf')).toBe(
      '/api/v1/common/files/contracts/2026/04/demo.pdf'
    )
  })

  it('keeps non-file URLs unchanged', () => {
    expect(getFileUrl('https://example.test/public.pdf')).toBe('https://example.test/public.pdf')
  })
})
