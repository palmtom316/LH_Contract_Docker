import request from '@/utils/request'

export function getContracts(params) {
    return request({
        url: '/contracts/upstream/',
        method: 'get',
        params
    })
}

export function createContract(data) {
    return request({
        url: '/contracts/upstream/',
        method: 'post',
        data
    })
}

export function getContract(id) {
    return request({
        url: `/contracts/upstream/${id}`,
        method: 'get'
    })
}

export function updateContract(id, data) {
    return request({
        url: `/contracts/upstream/${id}`,
        method: 'put',
        data
    })
}

export function deleteContract(id, config = {}) {
    return request({
        url: `/contracts/upstream/${id}`,
        method: 'delete',
        ...config
    })
}

export function getReceivables(contractId) {
    return request({
        url: `/contracts/upstream/${contractId}/receivables`,
        method: 'get'
    })
}

export function createReceivable(contractId, data) {
    return request({
        url: `/contracts/upstream/${contractId}/receivables`,
        method: 'post',
        data
    })
}

export function updateReceivable(contractId, receivableId, data) {
    return request({
        url: `/contracts/upstream/${contractId}/receivables/${receivableId}`,
        method: 'put',
        data
    })
}

export function deleteReceivable(contractId, receivableId) {
    return request({
        url: `/contracts/upstream/${contractId}/receivables/${receivableId}`,
        method: 'delete'
    })
}

export function getInvoices(contractId) {
    return request({
        url: `/contracts/upstream/${contractId}/invoices`,
        method: 'get'
    })
}

export function createInvoice(contractId, data) {
    return request({
        url: `/contracts/upstream/${contractId}/invoices`,
        method: 'post',
        data
    })
}

export function updateInvoice(contractId, invoiceId, data) {
    return request({
        url: `/contracts/upstream/${contractId}/invoices/${invoiceId}`,
        method: 'put',
        data
    })
}

export function deleteInvoice(contractId, invoiceId) {
    return request({
        url: `/contracts/upstream/${contractId}/invoices/${invoiceId}`,
        method: 'delete'
    })
}

export function getReceipts(contractId) {
    return request({
        url: `/contracts/upstream/${contractId}/receipts`,
        method: 'get'
    })
}

export function createReceipt(contractId, data) {
    return request({
        url: `/contracts/upstream/${contractId}/receipts`,
        method: 'post',
        data
    })
}

export function updateReceipt(contractId, receiptId, data) {
    return request({
        url: `/contracts/upstream/${contractId}/receipts/${receiptId}`,
        method: 'put',
        data
    })
}

export function deleteReceipt(contractId, receiptId) {
    return request({
        url: `/contracts/upstream/${contractId}/receipts/${receiptId}`,
        method: 'delete'
    })
}

export function getSettlements(contractId) {
    return request({
        url: `/contracts/upstream/${contractId}/settlements`,
        method: 'get'
    })
}

export function createSettlement(contractId, data) {
    return request({
        url: `/contracts/upstream/${contractId}/settlements`,
        method: 'post',
        data
    })
}

export function updateSettlement(contractId, settlementId, data) {
    return request({
        url: `/contracts/upstream/${contractId}/settlements/${settlementId}`,
        method: 'put',
        data
    })
}

export function deleteSettlement(contractId, settlementId) {
    return request({
        url: `/contracts/upstream/${contractId}/settlements/${settlementId}`,
        method: 'delete'
    })
}

export function exportContracts(params) {
    return request({
        url: '/contracts/upstream/export/excel',
        method: 'get',
        params,
        responseType: 'blob'
    })
}

export function downloadImportTemplate() {
    return request({
        url: '/contracts/upstream/template/excel',
        method: 'get',
        responseType: 'blob'
    })
}

export function importContracts(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request({
        url: '/contracts/upstream/import/excel',
        method: 'post',
        data: formData,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

export function getContractSummary(id) {
    return request({
        url: `/contracts/upstream/${id}/summary`,
        method: 'get'
    })
}

export function getNextSerialNumber() {
    return request({
        url: '/contracts/upstream/next-serial-number',
        method: 'get'
    })
}
