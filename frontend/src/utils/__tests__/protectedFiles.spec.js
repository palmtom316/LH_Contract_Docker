import { beforeEach, describe, expect, it, vi } from 'vitest'
import request from '@/utils/request'
import { buildProtectedFileUrl, fetchProtectedFileBlob, openProtectedFile } from '@/utils/protectedFiles'

vi.mock('@/utils/request', () => ({
  default: { get: vi.fn() }
}))

describe('protectedFiles', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.clearAllMocks()
    if (!URL.createObjectURL) {
      URL.createObjectURL = vi.fn()
    }
    if (!URL.revokeObjectURL) {
      URL.revokeObjectURL = vi.fn()
    }
  })

  it('uses authenticated blob fetch instead of raw URL', async () => {
    request.get.mockResolvedValue(new Blob(['demo'], { type: 'application/pdf' }))

    const blob = await fetchProtectedFileBlob('contracts/2026/04/demo.pdf')

    expect(blob).toBeInstanceOf(Blob)
    expect(request.get).toHaveBeenCalledWith(
      '/common/files/contracts/2026/04/demo.pdf',
      expect.objectContaining({ responseType: 'blob' })
    )
  })

  it('opens object URL instead of business path', async () => {
    request.get.mockResolvedValue(new Blob(['demo'], { type: 'application/pdf' }))
    const objectUrl = 'blob:demo'
    const createObjectURL = vi.spyOn(URL, 'createObjectURL').mockReturnValue(objectUrl)
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)

    await openProtectedFile('contracts/2026/04/demo.pdf')

    expect(createObjectURL).toHaveBeenCalled()
    expect(openSpy).toHaveBeenCalledWith(objectUrl, '_blank', 'noopener')
  })

  it('normalizes legacy local upload prefixes', () => {
    expect(buildProtectedFileUrl('/uploads/contracts/2026/04/demo.pdf')).toBe(
      '/common/files/contracts/2026/04/demo.pdf'
    )
    expect(buildProtectedFileUrl('/app/uploads/contracts/2026/04/demo.pdf')).toBe(
      '/common/files/contracts/2026/04/demo.pdf'
    )
  })

  it('fetches already-built protected API URLs with auth transport', async () => {
    request.get.mockResolvedValue(new Blob(['demo'], { type: 'application/pdf' }))
    const createObjectURL = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:demo')
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)

    await openProtectedFile('/api/v1/common/files/uploads/contracts/2026/04/demo.pdf')

    expect(request.get).toHaveBeenCalledWith(
      '/common/files/contracts/2026/04/demo.pdf',
      expect.objectContaining({ responseType: 'blob' })
    )
    expect(createObjectURL).toHaveBeenCalled()
    expect(openSpy).toHaveBeenCalledWith('blob:demo', '_blank', 'noopener')
  })
})
