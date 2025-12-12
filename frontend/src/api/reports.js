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
