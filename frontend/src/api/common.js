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
 * @param {string|object} options - Target directory or upload options
 * @returns {Promise} - Upload response with file path
 */
export function uploadFile(file, options = 'contracts') {
    const formData = new FormData()
    formData.append('file', file)
    if (typeof options === 'string') {
        formData.append('upload_dir', options)
    } else if (options && typeof options === 'object') {
        if (options.uploadDir) formData.append('upload_dir', options.uploadDir)
        if (options.upload_dir) formData.append('upload_dir', options.upload_dir)
        if (options.subdir) formData.append('subdir', options.subdir)
        if (options.custom_filename) formData.append('custom_filename', options.custom_filename)
    }
    return request({
        url: '/common/upload',
        method: 'post',
        data: formData,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}
