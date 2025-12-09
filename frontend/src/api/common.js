import request from '@/utils/request'

export function getCompanies(query) {
    return request({
        url: '/common/companies',
        method: 'get',
        params: { query }
    })
}

export function uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request({
        url: '/common/upload',
        method: 'post',
        data: formData,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}
