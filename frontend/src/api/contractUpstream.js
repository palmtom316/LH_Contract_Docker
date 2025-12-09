import request from '@/utils/request'

export function getContracts(params) {
    return request({
        url: '/contracts/upstream',
        method: 'get',
        params
    })
}

export function createContract(data) {
    return request({
        url: '/contracts/upstream',
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

export function deleteContract(id) {
    return request({
        url: `/contracts/upstream/${id}`,
        method: 'delete'
    })
}

// Sub-resources
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

export function exportContracts(params) {
    return request({
        url: '/contracts/upstream/export/excel',
        method: 'get',
        params,
        responseType: 'blob'
    })
}

export function getContractSummary(id) {
    return request({
        url: `/contracts/upstream/${id}/summary`,
        method: 'get'
    })
}
