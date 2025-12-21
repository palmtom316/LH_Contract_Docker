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

export function uploadLogo(data) {
    return request({
        url: '/system/logo',
        method: 'post',
        data,
        headers: { 'Content-Type': 'multipart/form-data' }
    })
}

export function getLogo() {
    return request({
        url: '/system/logo',
        method: 'get'
    })
}

export function resetSystem(confirm_code) {
    return request({
        url: '/system/reset',
        method: 'post',
        params: { confirm_code }
    })
}
