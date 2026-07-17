import { beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive, ref } from 'vue'
import { uploadFile } from '@/api/common'
import { ElMessage } from 'element-plus'
import { createUploadRequestHandler } from '@/composables/useUploadRequest'

vi.mock('@/api/common', () => ({
  uploadFile: vi.fn()
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

const makeUploadOption = (name = 'demo.pdf') => ({
  file: new File(['demo'], name, { type: 'application/pdf' }),
  onSuccess: vi.fn(),
  onError: vi.fn()
})

describe('createUploadRequestHandler', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('uploads with default options and writes path, key, and file list', async () => {
    const option = makeUploadOption()
    const target = reactive({ file_path: '', file_key: '', storage_provider: '' })
    const fileList = ref([])
    uploadFile.mockResolvedValue({
      path: '/uploads/contracts/demo.pdf',
      key: 'contracts/demo.pdf',
      storage_provider: 'minio'
    })

    const result = await createUploadRequestHandler({
      target,
      fileListRef: fileList
    })(option)

    expect(result).toEqual({
      path: '/uploads/contracts/demo.pdf',
      key: 'contracts/demo.pdf',
      storage_provider: 'minio'
    })
    expect(uploadFile).toHaveBeenCalledWith(option.file, 'contracts')
    expect(target.file_path).toBe('/uploads/contracts/demo.pdf')
    expect(target.file_key).toBe('contracts/demo.pdf')
    expect(target.storage_provider).toBe('minio')
    expect(fileList.value).toEqual([{ name: 'demo.pdf', url: '/uploads/contracts/demo.pdf' }])
    expect(option.onSuccess).not.toHaveBeenCalled()
    expect(option.onError).not.toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('上传成功')
  })

  it('supports dynamic upload options, custom fields, loading state, and success callback', async () => {
    const option = makeUploadOption('contract.pdf')
    const target = reactive({ contract_file_path: '', contract_file_key: '' })
    const fileList = ref([])
    const loading = ref(false)
    let resolveUpload
    uploadFile.mockReturnValue(new Promise((resolve) => {
      resolveUpload = resolve
    }))

    const uploadPromise = createUploadRequestHandler({
      target,
      pathField: 'contract_file_path',
      keyField: 'contract_file_key',
      fileListRef: fileList,
      loadingRef: loading,
      uploadOptions: ({ option }) => ({
        subdir: 'upstream/contract',
        custom_filename: `001_${option.file.name}`
      }),
      callOptionSuccess: true
    })(option)

    expect(loading.value).toBe(true)
    resolveUpload({ path: '/uploads/upstream/contract/001_contract.pdf', key: 'upstream/contract/001_contract.pdf' })
    await expect(uploadPromise).resolves.toEqual({
      path: '/uploads/upstream/contract/001_contract.pdf',
      key: 'upstream/contract/001_contract.pdf'
    })

    expect(loading.value).toBe(false)
    expect(uploadFile).toHaveBeenCalledWith(option.file, {
      subdir: 'upstream/contract',
      custom_filename: '001_contract.pdf'
    })
    expect(target.contract_file_path).toBe('/uploads/upstream/contract/001_contract.pdf')
    expect(target.contract_file_key).toBe('upstream/contract/001_contract.pdf')
    expect(fileList.value).toEqual([{ name: 'contract.pdf', url: '/uploads/upstream/contract/001_contract.pdf' }])
    expect(option.onSuccess).toHaveBeenCalledWith({
      path: '/uploads/upstream/contract/001_contract.pdf',
      key: 'upstream/contract/001_contract.pdf'
    })
  })

  it('supports per-call overrides without writing a file key', async () => {
    const option = makeUploadOption('audit.pdf')
    const target = reactive({ file_path: '', audit_report_path: '' })
    const auditReportFileList = ref([])
    uploadFile.mockResolvedValue({ path: '/uploads/contracts/audit.pdf', key: 'contracts/audit.pdf' })
    const uploadFinanceFile = createUploadRequestHandler({
      target,
      keyField: null
    })

    await uploadFinanceFile(option, {
      pathField: 'audit_report_path',
      fileListRef: auditReportFileList
    })

    expect(target.file_path).toBe('')
    expect(target.audit_report_path).toBe('/uploads/contracts/audit.pdf')
    expect(target.file_key).toBeUndefined()
    expect(auditReportFileList.value).toEqual([{ name: 'audit.pdf', url: '/uploads/contracts/audit.pdf' }])
  })

  it('reports failures and calls upload error callback by default', async () => {
    const option = makeUploadOption()
    const target = reactive({ file_path: '' })
    const fileList = ref([])
    const error = new Error('network down')
    uploadFile.mockRejectedValue(error)

    const result = await createUploadRequestHandler({
      target,
      fileListRef: fileList,
      logError: false
    })(option)

    expect(result).toBeUndefined()
    expect(target.file_path).toBe('')
    expect(fileList.value).toEqual([])
    expect(option.onError).toHaveBeenCalledWith(error)
    expect(ElMessage.error).toHaveBeenCalledWith('上传失败')
  })

  it('can keep the upload error callback silent for legacy callers', async () => {
    const option = makeUploadOption()
    uploadFile.mockResolvedValue({})

    await createUploadRequestHandler({
      callOptionError: false
    })(option)

    expect(option.onError).not.toHaveBeenCalled()
    expect(ElMessage.error).toHaveBeenCalledWith('上传失败')
  })
})
