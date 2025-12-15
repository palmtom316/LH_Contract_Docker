import request from '@/utils/request'

export function getAuditLogs(params) {
    return request({
        url: '/audit/',
        method: 'get',
        params
    })
}

export function getActionTypes() {
    return request({
        url: '/audit/actions',
        method: 'get'
    })
}

export function getResourceTypes() {
    return request({
        url: '/audit/resource-types',
        method: 'get'
    })
}

export function deleteAuditLogsBefore(beforeDate) {
    return request({
        url: '/audit/cleanup',
        method: 'delete',
        params: { before_date: beforeDate }
    })
}
