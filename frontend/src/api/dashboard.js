import request from '@/utils/request'

export function getStats() {
    return request({
        url: '/dashboard/stats',
        method: 'get'
    })
}
