import { describe, expect, it, vi, beforeEach } from 'vitest'
import request from '@/utils/request'
import { uploadFile } from '@/api/common'

vi.mock('@/utils/request', () => ({
  default: vi.fn(() => Promise.resolve({ ok: true }))
}))

describe('common api uploadFile', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('sends legacy string upload_dir option', () => {
    const file = new File(['demo'], 'demo.pdf', { type: 'application/pdf' })

    uploadFile(file, 'expenses')

    const config = request.mock.calls[0][0]
    expect(config.url).toBe('/common/upload')
    expect(config.method).toBe('post')
    expect(config.data).toBeInstanceOf(FormData)
    expect(config.data.get('file')).toBe(file)
    expect(config.data.get('upload_dir')).toBe('expenses')
  })

  it('sends controlled subdir and custom filename object options', () => {
    const file = new File(['demo'], 'contract.pdf', { type: 'application/pdf' })

    uploadFile(file, {
      subdir: 'upstream/contract',
      custom_filename: '001_contract.pdf'
    })

    const formData = request.mock.calls[0][0].data
    expect(formData.get('file')).toBe(file)
    expect(formData.get('subdir')).toBe('upstream/contract')
    expect(formData.get('custom_filename')).toBe('001_contract.pdf')
    expect(formData.has('upload_dir')).toBe(false)
  })
})
