import request from '@/utils/request'

export function getStats() {
    return request({
        url: '/dashboard/stats',
        method: 'get'
    })
}

export function getPeriodStats() {
    return request({
        url: '/dashboard/stats/period',
        method: 'get'
    })
}

export function getPeriodTrend(period) {
    return request({
        url: '/dashboard/stats/trend/period',
        method: 'get',
        params: { period }
    })
}
