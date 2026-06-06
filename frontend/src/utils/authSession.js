import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
let sessionRefreshToken = ''

if (typeof window !== 'undefined') {
    localStorage.removeItem('refresh_token')
}

export function persistSession({ accessToken, refreshToken, expiresIn, user }) {
    localStorage.setItem('token', accessToken)
    sessionRefreshToken = refreshToken || ''
    localStorage.removeItem('refresh_token')

    if (typeof expiresIn === 'number' && !Number.isNaN(expiresIn)) {
        const expiresAt = Date.now() + (expiresIn * 1000)
        localStorage.setItem('token_expires_at', String(expiresAt))
    } else {
        localStorage.removeItem('token_expires_at')
    }

    localStorage.setItem('user_info', JSON.stringify(user || {}))
    localStorage.setItem('user_permissions', JSON.stringify((user && user.permissions) || []))
}

export function clearSessionStorage() {
    sessionRefreshToken = ''
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
