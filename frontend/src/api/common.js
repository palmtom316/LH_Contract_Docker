import request from '@/utils/request'

export function getCompanies(query) {
    return request({
        url: '/common/companies',
        method: 'get',
        params: { query }
    })
}

/**
 * Upload a file to the server
 * @param {File} file - The file to upload
 * @param {string} uploadDir - Target directory: contracts, invoices, receipts, settlements, expenses
 * @returns {Promise} - Upload response with file path
 */
export function uploadFile(file, uploadDir = 'contracts') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('upload_dir', uploadDir)
    return request({
        url: '/common/upload',
        method: 'post',
        data: formData,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}
