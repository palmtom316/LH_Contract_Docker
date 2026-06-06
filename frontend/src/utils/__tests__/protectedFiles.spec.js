import { beforeEach, describe, expect, it, vi } from 'vitest'
import request from '@/utils/request'
import { fetchProtectedFileBlob, openProtectedFile } from '@/utils/protectedFiles'

vi.mock('@/utils/request', () => ({
  default: { get: vi.fn() }
}))

describe('protectedFiles', () => {
  beforeEach(() => {
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
})
