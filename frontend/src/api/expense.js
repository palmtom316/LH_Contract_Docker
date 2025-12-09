import request from '@/utils/request'

export function getExpenses(params) {
    return request({
        url: '/expenses',
        method: 'get',
        params
    })
}

export function createExpense(data) {
    return request({
        url: '/expenses',
        method: 'post',
        data
    })
}

export function getExpense(id) {
    return request({
        url: `/expenses/${id}`,
        method: 'get'
    })
}

export function updateExpense(id, data) {
    return request({
        url: `/expenses/${id}`,
        method: 'put',
        data
    })
}

export function deleteExpense(id) {
    return request({
        url: `/expenses/${id}`,
        method: 'delete'
    })
}

export function approveExpense(id, approved) {
    return request({
        url: `/expenses/${id}/approve`,
        method: 'post',
        params: { approved }
    })
}
