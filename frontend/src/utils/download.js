/**
 * Utility functions for file downloads
 * Uses file-saver library for cross-browser compatibility
 */
// import { saveAs } from 'file-saver'

/**
 * Download a blob as a file
 * @param {Blob|ArrayBuffer} data - The data to download
 * @param {string} filename - The filename to save as
 * @param {string} mimeType - The MIME type of the file
 */
export function downloadBlob(data, filename, mimeType = 'application/octet-stream') {
    console.log('downloadBlob called with:', { data, filename, mimeType })

    if (!data) {
        console.error('downloadBlob: No data provided')
        throw new Error('下载数据为空')
    }

    try {
        // Create a new Blob with explicit type
        const blob = new Blob([data], { type: mimeType })
        console.log('downloadBlob: Created blob, size:', blob.size)

        // Native download
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.style.display = 'none'
        link.href = url
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        console.log('downloadBlob: Download initiated successfully')
    } catch (error) {
        console.error('downloadBlob error:', error)
        throw error
    }
}

/**
 * Download an Excel file
 * @param {Blob|ArrayBuffer} data - The Excel data
 * @param {string} filename - The filename (should end with .xlsx)
 */
export function downloadExcel(data, filename) {
    console.log('downloadExcel called with:', { dataType: data?.constructor?.name, filename })
    const mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    downloadBlob(data, filename, mimeType)
}

/**
 * Download a PDF file
 * @param {Blob|ArrayBuffer} data - The PDF data
 * @param {string} filename - The filename (should end with .pdf)
 */
export function downloadPdf(data, filename) {
    const mimeType = 'application/pdf'
    downloadBlob(data, filename, mimeType)
}

/**
 * Generate a timestamped filename
 * @param {string} prefix - Filename prefix
 * @param {string} extension - File extension (without dot)
 * @returns {string} Timestamped filename
 */
export function generateFilename(prefix, extension = 'xlsx') {
    const date = new Date().toISOString().slice(0, 10)
    return `${prefix}_${date}.${extension}`
}
