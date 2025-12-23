import request from '@/utils/request'

export function login(data) {
    // Use JSON login endpoint to avoid Content-Type issues
    return request({
        url: '/auth/login/json',
        method: 'post',
        data // plain object, axios sends as JSON
    })
}

export function register(data) {
    return request({
        url: '/auth/register',
        method: 'post',
        data
    })
}

export function getInfo() {
    return request({
        url: '/auth/me',
        method: 'get'
    })
}

export function initAdmin() {
    return request({
        url: '/auth/init-admin',
        method: 'post'
    })
}

export function logout() {
    return Promise.resolve()
}

export function refreshToken(refreshToken) {
    return request({
        url: '/auth/refresh',
        method: 'post',
        data: { refresh_token: refreshToken }
    })
}
