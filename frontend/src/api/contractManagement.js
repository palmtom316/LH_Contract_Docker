import request from '@/utils/request'

export function getContracts(params) {
    return request({
        url: '/contracts/management',
        method: 'get',
        params
    })
}

export function createContract(data) {
    return request({
        url: '/contracts/management',
        method: 'post',
        data
    })
}

export function getContract(id) {
    return request({
        url: `/contracts/management/${id}`,
        method: 'get'
    })
}

export function updateContract(id, data) {
    return request({
        url: `/contracts/management/${id}`,
        method: 'put',
        data
    })
}

export function deleteContract(id) {
    return request({
        url: `/contracts/management/${id}`,
        method: 'delete'
    })
}

// Sub-resources
export function getPayables(contractId) {
    return request({
        url: `/contracts/management/${contractId}/payables`,
        method: 'get'
    })
}

export function createPayable(contractId, data) {
    return request({
        url: `/contracts/management/${contractId}/payables`,
        method: 'post',
        data
    })
}

export function getInvoices(contractId) {
    return request({
        url: `/contracts/management/${contractId}/invoices`,
        method: 'get'
    })
}

export function createInvoice(contractId, data) {
    return request({
        url: `/contracts/management/${contractId}/invoices`,
        method: 'post',
        data
    })
}

export function getPayments(contractId) {
    return request({
        url: `/contracts/management/${contractId}/payments`,
        method: 'get'
    })
}

export function createPayment(contractId, data) {
    return request({
        url: `/contracts/management/${contractId}/payments`,
        method: 'post',
        data
    })
}

export function getSettlements(contractId) {
    return request({
        url: `/contracts/management/${contractId}/settlements`,
        method: 'get'
    })
}

export function createSettlement(contractId, data) {
    return request({
        url: `/contracts/management/${contractId}/settlements`,
        method: 'post',
        data
    })
}
