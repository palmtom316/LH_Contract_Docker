import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'


// Create Axios instance
const service = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
    timeout: 60000,
    headers: {
        'Content-Type': 'application/json;charset=utf-8'
    }
})

// Request interceptor
service.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`
        }
        return config
    },
    error => {
        return Promise.reject(error)
    }
)

// Response interceptor
service.interceptors.response.use(
    response => {
        // For blob responses (file downloads), return the full response data
        if (response.config.responseType === 'blob') {
            return response.data
        }
        return response.data
    },
    async error => {
        console.error('Response error:', error)
        const { response } = error
        if (response) {

            // Handle Blob errors (response.data is Blob, not JSON)
            let errorMsg = response.data.detail
            if (response.data instanceof Blob && response.data.type === 'application/json') {
                try {
                    const text = await response.data.text()
                    const json = JSON.parse(text)
                    errorMsg = json.detail
                } catch (e) {
                    // If parse fails, fallback
                }
            } else if (response.data instanceof Blob) {
                // Determine if it looks like text
                try {
                    const text = await response.data.text()
                    // If it is short text (like 429 body), might use it
                    if (text.length < 200) errorMsg = text
                } catch (e) { }
            }

            switch (response.status) {
                case 401:
                    if (response.config.url.includes('/login')) {
                        ElMessage.error(errorMsg || '用户名或密码错误')
                    } else {
                        localStorage.removeItem('token')
                        localStorage.removeItem('user')
                        router.push('/login')
                        ElMessage.error('登录已过期，请重新登录')
                    }
                    break
                case 403:
                    ElMessage.error(errorMsg || '权限不足')
                    break
                case 404:
                    ElMessage.error(errorMsg || '请求的资源不存在')
                    break
                case 429:
                    ElMessage.error('请求过于频繁，请稍后再试')
                    break
                case 500:
                    ElMessage.error(errorMsg || '服务器内部错误')
                    break
                case 422:
                    ElMessage.error(typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : (errorMsg || '参数验证错误'))
                    break
                default:
                    ElMessage.error(errorMsg || '发生未知错误')
            }
        } else {
            ElMessage.error('网络连接错误: ' + error.message)
        }
        return Promise.reject(error)
    }
)

export default service
