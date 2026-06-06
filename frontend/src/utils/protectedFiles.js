import request from '@/utils/request'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

function isBrowserFileUrl(path) {
  return /^(blob:|data:|https?:)/.test(path) || path.startsWith('/api/')
}

function revokeObjectUrlLater(url) {
  if (!url || !url.startsWith('blob:')) return
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
}

function normalizeProtectedPath(path) {
  let cleanPath = String(path || '').trim()

  if (!cleanPath) return ''
  if (cleanPath.startsWith(`${API_BASE_URL}/common/files/`)) {
    cleanPath = cleanPath.slice(`${API_BASE_URL}/common/files/`.length)
  } else if (cleanPath.startsWith('/common/files/')) {
    cleanPath = cleanPath.slice('/common/files/'.length)
  }

  cleanPath = cleanPath.replace(/^\/+/, '')
  cleanPath = cleanPath.replace(/^uploads\//, '')

  return cleanPath
}

function buildProtectedFileUrl(path) {
  const cleanPath = normalizeProtectedPath(path)
  if (!cleanPath) {
    throw new Error('缺少受保护文件路径')
  }
  return `/common/files/${cleanPath}`
}

function buildDownloadFilename(path, fallback = 'download') {
  const cleanPath = normalizeProtectedPath(path)
  return cleanPath.split('/').pop() || fallback
}

export async function fetchProtectedFileBlob(path) {
  return request.get(buildProtectedFileUrl(path), {
    responseType: 'blob',
    suppressGlobalErrorMessage: true
  })
}

export async function createProtectedObjectUrl(path) {
  if (!path) {
    throw new Error('缺少受保护文件路径')
  }

  if (isBrowserFileUrl(path)) {
    return path
  }

  const blob = await fetchProtectedFileBlob(path)
  return URL.createObjectURL(blob)
}

export async function openProtectedFile(path) {
  const objectUrl = await createProtectedObjectUrl(path)
  window.open(objectUrl, '_blank', 'noopener')
  revokeObjectUrlLater(objectUrl)
  return objectUrl
}

export async function downloadProtectedFile(path, filename) {
  const objectUrl = await createProtectedObjectUrl(path)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename || buildDownloadFilename(path)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  revokeObjectUrlLater(objectUrl)
  return objectUrl
}
