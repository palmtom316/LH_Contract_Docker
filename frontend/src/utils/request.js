import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// Log the env var
console.log('VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL)

// Create Axios instance
const service = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
    timeout: 15000,
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
        return response.data
    },
    error => {
        console.error('Response error:', error)
        const { response } = error
        if (response) {
            switch (response.status) {
                case 401:
                    if (response.config.url.includes('/login')) {
                        ElMessage.error(response.data.detail || '用户名或密码错误')
                    } else {
                        localStorage.removeItem('token')
                        localStorage.removeItem('user')
                        router.push('/login')
                        ElMessage.error('登录已过期，请重新登录')
                    }
                    break
                case 403:
                    ElMessage.error('权限不足')
                    break
                case 404:
                    ElMessage.error('请求的资源不存在')
                    break
                case 500:
                    ElMessage.error('服务器内部错误')
                    break
                case 422:
                    ElMessage.error(JSON.stringify(response.data.detail))
                    break
                default:
                    ElMessage.error(response.data.detail || '发生未知错误')
            }
        } else {
            ElMessage.error('网络连接错误: ' + error.message)
        }
        return Promise.reject(error)
    }
)

export default service
