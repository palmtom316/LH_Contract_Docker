import request from '@/utils/request'

function withIdempotency(data = {}, extraHeaders = {}) {
  const key = data.idempotency_key || (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`)
  return {
    data: { ...data, idempotency_key: key },
    headers: { 'Idempotency-Key': key, ...extraHeaders }
  }
}

export function listWarehouses(params) {
  return request({ url: '/warehouse/warehouses', method: 'get', params })
}

export function createWarehouse(data) {
  return request({ url: '/warehouse/warehouses', method: 'post', data })
}

export function updateWarehouse(id, data) {
  return request({ url: `/warehouse/warehouses/${id}`, method: 'put', data })
}

export function listLocations(warehouseId) {
  return request({ url: `/warehouse/warehouses/${warehouseId}/locations`, method: 'get' })
}

export function getLocation(id) {
  return request({ url: `/warehouse/locations/${id}`, method: 'get' })
}

export function createLocation(warehouseId, data) {
  return request({ url: `/warehouse/warehouses/${warehouseId}/locations`, method: 'post', data })
}

export function listProjects(params) {
  return request({ url: '/warehouse/projects', method: 'get', params })
}

export function searchUpstreamContracts(params) {
  return request({ url: '/warehouse/upstream-contracts', method: 'get', params })
}

export function createProject(data) {
  return request({ url: '/warehouse/projects', method: 'post', data })
}

export function updateProject(id, data) {
  return request({ url: `/warehouse/projects/${id}`, method: 'put', data })
}

export function listMaterials(params) {
  return request({ url: '/warehouse/materials', method: 'get', params })
}

export function searchMaterials(q) {
  return request({ url: '/warehouse/materials/search', method: 'get', params: { q } })
}

export function createMaterial(data) {
  return request({ url: '/warehouse/materials', method: 'post', data })
}

export function updateMaterial(id, data) {
  return request({ url: `/warehouse/materials/${id}`, method: 'put', data })
}

export function getMaterialQr(id) {
  return request({ url: `/warehouse/materials/${id}/qr`, method: 'get' })
}

export function getMyWarehouseScopes() {
  return request({ url: '/warehouse/me/warehouse-scopes', method: 'get' })
}

export function getUserWarehouseScopes(userId) {
  return request({ url: `/warehouse/users/${userId}/warehouse-scopes`, method: 'get' })
}

export function replaceUserWarehouseScopes(userId, scopes) {
  return request({ url: `/warehouse/users/${userId}/warehouse-scopes`, method: 'put', data: { scopes } })
}

export function listStockBalances(params) {
  return request({ url: '/warehouse/stock-balances', method: 'get', params })
}

export function getAvailableStock(params) {
  return request({ url: '/warehouse/stock-balances/available', method: 'get', params })
}

export function listLedger(params) {
  return request({ url: '/warehouse/ledger', method: 'get', params })
}

export function listDocuments(params) {
  return request({ url: '/warehouse/documents', method: 'get', params })
}

export function getDocument(id) {
  return request({ url: `/warehouse/documents/${id}`, method: 'get' })
}

export function voidDocument(id, data) {
  const packed = withIdempotency(data)
  return request({ url: `/warehouse/documents/${id}/void`, method: 'post', ...packed })
}

export function postInbound(data) {
  const packed = withIdempotency(data)
  return request({ url: '/warehouse/inbounds', method: 'post', ...packed })
}

export function postOutbound(data) {
  const packed = withIdempotency(data)
  return request({ url: '/warehouse/outbounds', method: 'post', ...packed })
}

export function postTransfer(data) {
  const packed = withIdempotency(data)
  return request({ url: '/warehouse/transfers', method: 'post', ...packed })
}

export function listCounts() {
  return request({ url: '/warehouse/counts', method: 'get' })
}

export function createCount(data) {
  const packed = withIdempotency(data)
  return request({ url: '/warehouse/counts', method: 'post', ...packed })
}

export function getCount(id) {
  return request({ url: `/warehouse/counts/${id}`, method: 'get' })
}

export function updateCountLines(id, data) {
  return request({ url: `/warehouse/counts/${id}/lines`, method: 'put', data })
}

export function confirmCount(id) {
  return request({ url: `/warehouse/counts/${id}/confirm`, method: 'post' })
}

export function exportStock() {
  return request({ url: '/warehouse/exports/stock.xlsx', method: 'get', responseType: 'blob' })
}

export function exportLedger() {
  return request({ url: '/warehouse/exports/ledger.xlsx', method: 'get', responseType: 'blob' })
}

export function exportMaterials() {
  return request({ url: '/warehouse/exports/materials.xlsx', method: 'get', responseType: 'blob' })
}
