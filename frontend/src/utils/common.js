
/**
 * Common utility functions
 */

/**
 * Get full file URL from relative path
 * @param {string} path - Relative path (e.g. /uploads/...)
 * @returns {string} - Full URL
 */
export const getFileUrl = (path) => {
    if (!path) return ''
    if (path.startsWith('http') || path.startsWith('blob:')) return path

    // Use VITE_API_BASE_URL if available
    const apiUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'

    // Legacy local files (start with /uploads)
    if (path.startsWith('/uploads') || path.startsWith('uploads')) {
        // Strip '/api/v1' suffix to get the root URL
        const baseUrl = apiUrl.replace(/\/api\/v1\/?$/, '')
        const cleanPath = path.startsWith('/') ? path : `/${path}`
        return `${baseUrl}${cleanPath}`
    }

    // New MinIO files (served via API)
    // If path is a key like 'contracts/2026/...', use API endpoint
    // Endpoint: /api/v1/common/files/{path}
    // API URL is already included in axios base, but here we need full URL for href/window.open

    // Remove leading slash if present for cleaner join
    const cleanKey = path.startsWith('/') ? path.substring(1) : path

    // Construct API URL: http://host:8000/api/v1/common/files/contracts/...
    const url = `${apiUrl}/common/files/${cleanKey}`

    // Append token for authentication if available
    const token = localStorage.getItem('token')
    if (token) {
        return `${url}?token=${token}`
    }

    return url
}

/**
 * Format number as currency (CNY)
 * @param {number|string} val - Value to format
 * @returns {string} - Formatted string (e.g. "1,234.56")
 */
export const formatMoney = (val) => {
    if (val === undefined || val === null || val === '') return '0.00'
    return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/**
 * Get status type for Element Plus tag
 * @param {string} status 
 * @returns {string} - success/warning/danger/info/primary
 */
export const getStatusType = (status) => {
    if (status === '已完成' || status === '已完工' || status === '已结算') return 'success'
    if (status === '已终止' || status === '已归档' || status === '合同终止') return 'info'
    if (status === '已中止' || status === '合同中止') return 'danger'
    if (status === '待审核' || status === '质保到期') return 'warning'
    if (status === '执行中') return 'primary'
    return ''
}
