import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
let sessionAccessToken = ''
let sessionRefreshToken = ''

if (typeof window !== 'undefined') {
    sessionAccessToken = sessionStorage.getItem('token') || ''
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('token_expires_at')
    localStorage.removeItem('user_info')
    localStorage.removeItem('user_permissions')
}

export function persistSession({ accessToken, refreshToken, expiresIn, user }) {
    sessionAccessToken = accessToken || ''
    sessionRefreshToken = refreshToken || ''
    sessionStorage.setItem('token', sessionAccessToken)
    localStorage.removeItem('refresh_token')

    if (typeof expiresIn === 'number' && !Number.isNaN(expiresIn)) {
        const expiresAt = Date.now() + (expiresIn * 1000)
        sessionStorage.setItem('token_expires_at', String(expiresAt))
    } else {
        sessionStorage.removeItem('token_expires_at')
    }

    sessionStorage.setItem('user_info', JSON.stringify(user || {}))
    sessionStorage.setItem('user_permissions', JSON.stringify((user && user.permissions) || []))
}

export function getAccessToken() {
    return sessionAccessToken || sessionStorage.getItem('token') || ''
}

export function clearSessionStorage() {
    sessionAccessToken = ''
    sessionRefreshToken = ''
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('token_expires_at')
    sessionStorage.removeItem('user_info')
    sessionStorage.removeItem('user_permissions')
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('token_expires_at')
    localStorage.removeItem('user_info')
    localStorage.removeItem('user_permissions')
}

export async function refreshSessionWithStoredToken() {
    const refreshToken = sessionRefreshToken
    if (!refreshToken) {
        throw new Error('No refresh token available')
    }

    const response = await axios.post(
        `${API_BASE_URL}/auth/refresh`,
        { refresh_token: refreshToken },
        {
            headers: {
                'Content-Type': 'application/json;charset=utf-8'
            },
            timeout: 60000
        }
    )

    const payload = response.data
    persistSession({
        accessToken: payload.access_token,
        refreshToken: payload.refresh_token || refreshToken,
        expiresIn: payload.expires_in,
        user: payload.user
    })

    return payload
}
