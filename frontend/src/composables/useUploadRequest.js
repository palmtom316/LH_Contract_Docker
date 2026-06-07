import { uploadFile } from '@/api/common'
import { ElMessage } from 'element-plus'

const resolveValue = (value, context) => {
  return typeof value === 'function' ? value(context) : value
}

const assignField = (target, field, value, context) => {
  const resolvedField = resolveValue(field, context)
  if (!target || !resolvedField) return
  target[resolvedField] = value
}

const updateFileList = (fileListRef, context) => {
  const resolvedFileListRef = resolveValue(fileListRef, context)
  if (!resolvedFileListRef) return

  resolvedFileListRef.value = [{
    name: context.option.file?.name || '附件',
    url: context.result.path
  }]
}

const logUploadError = (logError, error) => {
  if (!logError) return
  console.error(logError === true ? 'Upload error:' : logError, error)
}

export function createUploadRequestHandler(config = {}) {
  return async (option, overrides = {}) => {
    const settings = {
      uploadOptions: 'contracts',
      pathField: 'file_path',
      keyField: 'file_key',
      successMessage: '上传成功',
      errorMessage: '上传失败',
      callOptionSuccess: false,
      callOptionError: true,
      logError: false,
      ...config,
      ...overrides
    }

    const context = {
      option,
      target: undefined,
      result: undefined
    }

    const loadingRef = resolveValue(settings.loadingRef, context)
    if (loadingRef) loadingRef.value = true

    try {
      const target = resolveValue(settings.target, context)
      context.target = target

      const uploadOptions = resolveValue(settings.uploadOptions, context)
      const result = await uploadFile(option.file, uploadOptions)
      if (!result?.path) {
        throw new Error('上传返回路径为空')
      }

      context.result = result
      assignField(target, settings.pathField, result.path, context)
      if (result.key) {
        assignField(target, settings.keyField, result.key, context)
      }
      updateFileList(settings.fileListRef, context)

      if (typeof settings.onSuccess === 'function') {
        await settings.onSuccess(context)
      }
      if (settings.callOptionSuccess) {
        option.onSuccess?.(result)
      }
      if (settings.successMessage) {
        ElMessage.success(settings.successMessage)
      }

      return result
    } catch (error) {
      logUploadError(settings.logError, error)
      if (settings.errorMessage) {
        ElMessage.error(settings.errorMessage)
      }
      if (typeof settings.onError === 'function') {
        await settings.onError(error, context)
      }
      if (settings.callOptionError) {
        option.onError?.(error)
      }
      return undefined
    } finally {
      if (loadingRef) loadingRef.value = false
    }
  }
}
