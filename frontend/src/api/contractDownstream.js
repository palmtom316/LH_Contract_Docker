import request from '@/utils/request'

export function getContracts(params) {
    return request({
        url: '/contracts/downstream',
        method: 'get',
        params
    })
}

export function createContract(data) {
    return request({
        url: '/contracts/downstream',
        method: 'post',
        data
    })
}

export function getContract(id) {
    return request({
        url: `/contracts/downstream/${id}`,
        method: 'get'
    })
}

export function updateContract(id, data) {
    return request({
        url: `/contracts/downstream/${id}`,
        method: 'put',
        data
    })
}

export function deleteContract(id) {
    return request({
        url: `/contracts/downstream/${id}`,
        method: 'delete'
    })
}

// Sub-resources
export function getPayables(contractId) {
    return request({
        url: `/contracts/downstream/${contractId}/payables`,
        method: 'get'
    })
}

export function createPayable(contractId, data) {
    return request({
        url: `/contracts/downstream/${contractId}/payables`,
        method: 'post',
        data
    })
}

export function getInvoices(contractId) {
    return request({
        url: `/contracts/downstream/${contractId}/invoices`,
        method: 'get'
    })
}

export function createInvoice(contractId, data) {
    return request({
        url: `/contracts/downstream/${contractId}/invoices`,
        method: 'post',
        data
    })
}

export function getPayments(contractId) {
    return request({
        url: `/contracts/downstream/${contractId}/payments`,
        method: 'get'
    })
}

export function createPayment(contractId, data) {
    return request({
        url: `/contracts/downstream/${contractId}/payments`,
        method: 'post',
        data
    })
}

export function createSettlement(contractId, data) {
    return request({
        url: `/contracts/downstream/${contractId}/settlements`,
        method: 'post',
        data
    })
}
