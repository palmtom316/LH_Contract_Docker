"""
Optimized Token Refresh with Lock Mechanism
Prevents multiple simultaneous refresh requests
"""
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const service = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
    timeout: 60000,
    headers: {
        'Content-Type': 'application/json;charset=utf-8'
    }
})

// Token refresh lock mechanism
let isRefreshing = false
let refreshSubscribers = []

function subscribeTokenRefresh(cb) {
    refreshSubscribers.push(cb)
}

function onRefreshed(token) {
    refreshSubscribers.forEach(cb => cb(token))
    refreshSubscribers = []
}

async function refreshToken() {
    if (isRefreshing) {
        return new Promise(resolve => {
            subscribeTokenRefresh(token => {
                resolve(token)
            })
        })
    }

    isRefreshing = true
    try {
        const { useUserStore } = await import('@/stores/user')
        const userStore = useUserStore()
        await userStore.refreshAccessToken()
        const newToken = localStorage.getItem('token')
        onRefreshed(newToken)
        return newToken
    } catch (error) {
        refreshSubscribers = []
        throw error
    } finally {
        isRefreshing = false
    }
}

// Request interceptor
service.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`
        }
        return config
    },
    error => Promise.reject(error)
)

// Response interceptor
service.interceptors.response.use(
    response => {
        if (response.config.responseType === 'blob') {
            return response.data
        }
        return response.data
    },
    async error => {
        const { response } = error
        if (!response) {
            ElMessage.error('网络连接错误: ' + error.message)
            return Promise.reject(error)
        }

        let errorMsg = response.data?.detail || response.data?.message

        // Handle Blob errors
        if (response.data instanceof Blob && response.data.type === 'application/json') {
            try {
                const text = await response.data.text()
                const json = JSON.parse(text)
                errorMsg = json.detail || json.message
            } catch (e) {}
        }

        // Handle 401 with token refresh
        if (response.status === 401) {
            if (response.config.url.includes('/login') || response.config.url.includes('/refresh')) {
                ElMessage.error(errorMsg || '用户名或密码错误')
            } else {
                const refreshTokenValue = localStorage.getItem('refresh_token')
                if (refreshTokenValue && !response.config._retry) {
                    response.config._retry = true
                    try {
                        const newToken = await refreshToken()
                        response.config.headers['Authorization'] = `Bearer ${newToken}`
                        return service(response.config)
                    } catch (refreshError) {
                        localStorage.clear()
                        router.push('/login')
                        ElMessage.error('登录已过期，请重新登录')
                    }
                } else {
                    localStorage.clear()
                    router.push('/login')
                    ElMessage.error('登录已过期，请重新登录')
                }
            }
        } else if (response.status === 403) {
            ElMessage.error(errorMsg || '权限不足')
        } else if (response.status === 404) {
            ElMessage.error(errorMsg || '请求的资源不存在')
        } else if (response.status === 429) {
            ElMessage.error('请求过于频繁，请稍后再试')
        } else if (response.status === 422) {
            ElMessage.error(typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : (errorMsg || '参数验证错误'))
        } else if (response.status >= 500) {
            ElMessage.error(errorMsg || '服务器错误，请稍后重试')
        } else {
            ElMessage.error(errorMsg || `发生错误 (HTTP ${response.status})`)
        }

        return Promise.reject(error)
    }
)

export default service
