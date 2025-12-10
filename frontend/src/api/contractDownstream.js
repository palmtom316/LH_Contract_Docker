import request from '@/utils/request'

export function getContracts(params) {
    return request({
        url: '/contracts/downstream/',
        method: 'get',
        params
    })
}

export function createContract(data) {
    return request({
        url: '/contracts/downstream/',
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

// Payables (应付款)
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

export function updatePayable(contractId, payableId, data) {
    return request({
        url: `/contracts/downstream/${contractId}/payables/${payableId}`,
        method: 'put',
        data
    })
}

export function deletePayable(contractId, payableId) {
    return request({
        url: `/contracts/downstream/${contractId}/payables/${payableId}`,
        method: 'delete'
    })
}

// Invoices (收票)
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

export function updateInvoice(contractId, invoiceId, data) {
    return request({
        url: `/contracts/downstream/${contractId}/invoices/${invoiceId}`,
        method: 'put',
        data
    })
}

export function deleteInvoice(contractId, invoiceId) {
    return request({
        url: `/contracts/downstream/${contractId}/invoices/${invoiceId}`,
        method: 'delete'
    })
}

// Payments (付款)
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

export function updatePayment(contractId, paymentId, data) {
    return request({
        url: `/contracts/downstream/${contractId}/payments/${paymentId}`,
        method: 'put',
        data
    })
}

export function deletePayment(contractId, paymentId) {
    return request({
        url: `/contracts/downstream/${contractId}/payments/${paymentId}`,
        method: 'delete'
    })
}

// Settlements (结算)
export function getSettlements(contractId) {
    return request({
        url: `/contracts/downstream/${contractId}/settlements`,
        method: 'get'
    })
}

export function createSettlement(contractId, data) {
    return request({
        url: `/contracts/downstream/${contractId}/settlements`,
        method: 'post',
        data
    })
}

export function updateSettlement(contractId, settlementId, data) {
    return request({
        url: `/contracts/downstream/${contractId}/settlements/${settlementId}`,
        method: 'put',
        data
    })
}

export function deleteSettlement(contractId, settlementId) {
    return request({
        url: `/contracts/downstream/${contractId}/settlements/${settlementId}`,
        method: 'delete'
    })
}
