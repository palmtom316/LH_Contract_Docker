import axios from 'axios'

const ACCESS_TOKEN_COOKIE_NAME = 'lh_access_token'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export function syncAccessTokenCookie(token) {
    if (typeof document === 'undefined') return

    if (!token) {
        document.cookie = `${ACCESS_TOKEN_COOKIE_NAME}=; Max-Age=0; path=/; SameSite=Lax`
        return
    }

    document.cookie = `${ACCESS_TOKEN_COOKIE_NAME}=${encodeURIComponent(token)}; path=/; SameSite=Lax`
}

export function persistSession({ accessToken, refreshToken, expiresIn, user }) {
    localStorage.setItem('token', accessToken)
    syncAccessTokenCookie(accessToken)

    if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken)
    } else {
        localStorage.removeItem('refresh_token')
    }

    if (typeof expiresIn === 'number' && !Number.isNaN(expiresIn)) {
        const expiresAt = Date.now() + (expiresIn * 1000)
        localStorage.setItem('token_expires_at', String(expiresAt))
    } else {
        localStorage.removeItem('token_expires_at')
    }

    if (user) {
        localStorage.setItem('user_info', JSON.stringify(user))
        localStorage.setItem('user_permissions', JSON.stringify(user.permissions || []))
    }
}

export function clearSessionStorage() {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('token_expires_at')
    localStorage.removeItem('user_info')
    localStorage.removeItem('user_permissions')
    syncAccessTokenCookie('')
}

export async function refreshSessionWithStoredToken() {
    const refreshToken = localStorage.getItem('refresh_token')
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
