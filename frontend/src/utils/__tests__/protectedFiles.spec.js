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
    const previewWindow = {
      opener: window,
      location: { replace: vi.fn() },
      close: vi.fn()
    }
    const openSpy = vi.spyOn(window, 'open').mockReturnValue(previewWindow)

    await openProtectedFile('contracts/2026/04/demo.pdf')

    expect(createObjectURL).toHaveBeenCalled()
    expect(openSpy).toHaveBeenCalledWith('about:blank', '_blank')
    expect(previewWindow.opener).toBeNull()
    expect(previewWindow.location.replace).toHaveBeenCalledWith(objectUrl)
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
    const previewWindow = {
      opener: window,
      location: { replace: vi.fn() },
      close: vi.fn()
    }
    const openSpy = vi.spyOn(window, 'open').mockReturnValue(previewWindow)

    await openProtectedFile('/api/v1/common/files/uploads/contracts/2026/04/demo.pdf')

    expect(request.get).toHaveBeenCalledWith(
      '/common/files/contracts/2026/04/demo.pdf',
      expect.objectContaining({ responseType: 'blob' })
    )
    expect(createObjectURL).toHaveBeenCalled()
    expect(openSpy).toHaveBeenCalledWith('about:blank', '_blank')
    expect(previewWindow.location.replace).toHaveBeenCalledWith('blob:demo')
  })

  it('opens the placeholder window before the protected request resolves', async () => {
    let resolveRequest
    request.get.mockReturnValue(new Promise((resolve) => {
      resolveRequest = resolve
    }))
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:deferred')
    const previewWindow = {
      opener: window,
      location: { replace: vi.fn() },
      close: vi.fn()
    }
    const openSpy = vi.spyOn(window, 'open').mockReturnValue(previewWindow)

    const opening = openProtectedFile('contracts/2026/04/deferred.pdf')

    expect(openSpy).toHaveBeenCalledWith('about:blank', '_blank')
    expect(request.get).toHaveBeenCalled()
    resolveRequest(new Blob(['demo'], { type: 'application/pdf' }))
    await opening
    expect(previewWindow.location.replace).toHaveBeenCalledWith('blob:deferred')
  })
})
