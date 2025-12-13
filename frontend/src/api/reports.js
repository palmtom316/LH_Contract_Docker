import request from '@/utils/request'

export function getContractSummary(year, month) {
    return request({
        url: '/reports/contracts/summary',
        method: 'get',
        params: { year, month }
    })
}

export function getFinanceTrend(year, month) {
    return request({
        url: '/reports/finance/trend',
        method: 'get',
        params: { year, month }
    })
}

export function getExpenseBreakdown(year, month) {
    return request({
        url: '/reports/expenses/breakdown',
        method: 'get',
        params: { year, month }
    })
}

export function getArApStats(year, month) {
    return request({
        url: '/reports/finance/receivables-payables',
        method: 'get',
        params: { year, month }
    })
}

export function downloadComprehensiveReport(params) {
    return request({
        url: '/reports/export/comprehensive',
        method: 'get',
        params,
        responseType: 'blob'
    })
}

export function downloadReceivablesReport(params) {
    return request({
        url: '/reports/export/receivables',
        method: 'get',
        params,
        responseType: 'blob'
    })
}

export function downloadPayablesReport(params) {
    return request({
        url: '/reports/export/payables',
        method: 'get',
        params,
        responseType: 'blob'
    })
}

export function downloadUpstreamInvoicesReport(params) {
    return request({
        url: '/reports/export/invoices/upstream',
        method: 'get',
        params,
        responseType: 'blob'
    })
}

export function downloadDownstreamInvoicesReport(params) {
    return request({
        url: '/reports/export/invoices/downstream',
        method: 'get',
        params,
        responseType: 'blob'
    })
}

export function downloadUpstreamReceiptsReport(params) {
    return request({
        url: '/reports/export/receipts/upstream',
        method: 'get',
        params,
        responseType: 'blob'
    })
}

export function downloadDownstreamPaymentsReport(params) {
    return request({
        url: '/reports/export/payments/downstream',
        method: 'get',
        params,
        responseType: 'blob'
    })
}

export function downloadExpensePaymentsReport(params) {
    return request({
        url: '/reports/export/payments/expenses',
        method: 'get',
        params,
        responseType: 'blob'
    })
}

export function downloadUpstreamSettlementsReport(params) {
    return request({
        url: '/reports/export/settlements/upstream',
        method: 'get',
        params,
        responseType: 'blob'
    })
}

export function downloadDownstreamSettlementsReport(params) {
    return request({
        url: '/reports/export/settlements/downstream',
        method: 'get',
        params,
        responseType: 'blob'
    })
}

export function downloadAssociationReport(params) {
    return request({
        url: '/reports/export/association',
        method: 'get',
        params,
        responseType: 'blob'
    })
}
