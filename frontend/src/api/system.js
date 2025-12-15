import request from '@/utils/request'

export function backupDatabase() {
    return request({
        url: '/system/backup/db',
        method: 'get',
        responseType: 'blob',
        timeout: 300000 // 5 minutes
    })
}

export function backupSystem() {
    return request({
        url: '/system/backup/full',
        method: 'get',
        responseType: 'blob',
        timeout: 300000 // 5 minutes
    })
}
