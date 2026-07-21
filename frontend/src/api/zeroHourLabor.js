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
export const getZeroHourLaborDetail = id => request.get(`/zero-hour-labor/${id}/detail`)
export const createZeroHourFinance = (id,kind,data) => request.post(`/zero-hour-labor/${id}/${kind}`,data)
export const updateZeroHourFinance = (id,kind,recordId,data) => request.put(`/zero-hour-labor/${id}/finance/${kind}/${recordId}`,data)
export const deleteZeroHourFinance = (id,kind,recordId) => request.delete(`/zero-hour-labor/${id}/finance/${kind}/${recordId}`)
export const fetchZeroHourFinanceFile = key => request.get(`/common/files/${key}`, { responseType: 'blob' })
