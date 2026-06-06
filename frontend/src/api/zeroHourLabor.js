import request from '@/utils/request'

export function getZeroHourLaborList(params) {
    return request({
        url: '/zero-hour-labor',
        method: 'get',
        params
    })
}

export function createZeroHourLabor(data) {
    return request({
        url: '/zero-hour-labor',
        method: 'post',
        data
    })
}

export function updateZeroHourLabor(id, data) {
    return request({
        url: '/zero-hour-labor/' + id,
        method: 'put',
        data
    })
}

export function deleteZeroHourLabor(id) {
    return request({
        url: '/zero-hour-labor/' + id,
        method: 'delete'
    })
}

export function exportZeroHourLabor(params) {
    return request({
        url: '/zero-hour-labor/export/excel',
        method: 'get',
        params,
        responseType: 'blob'
    })
}
