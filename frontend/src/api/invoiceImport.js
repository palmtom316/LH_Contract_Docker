import request from '@/utils/request'

export function uploadBatch(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/invoice-imports/batches',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function listBatches() {
  return request({ url: '/invoice-imports/batches', method: 'get' })
}

export function listBatchItems(batchId) {
  return request({ url: `/invoice-imports/batches/${batchId}/items`, method: 'get' })
}

export function deleteBatch(batchId) {
  return request({ url: `/invoice-imports/batches/${batchId}`, method: 'delete' })
}

export function createAllocation(itemId, data) {
  return request({ url: `/invoice-imports/items/${itemId}/allocations`, method: 'post', data })
}

export function updateAllocation(allocationId, data) {
  return request({ url: `/invoice-imports/allocations/${allocationId}`, method: 'put', data })
}

export function confirmItem(itemId, data = { override_duplicate: false }) {
  return request({ url: `/invoice-imports/items/${itemId}/confirm`, method: 'post', data })
}
