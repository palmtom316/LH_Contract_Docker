/**
 * Composable for Finance Records operations
 * Handles receivables, payables, invoices, payments, and settlements
 * Reduces code duplication across contract detail pages
 */
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

/**
 * Create reusable finance record composable
 * @param {Object} options - Configuration options
 * @param {Object} options.api - API module with CRUD operations
 * @param {string} options.recordType - Type name for messages (e.g., '应收款')
 * @param {string} options.idField - ID field name in record (default: 'id')
 */
export function useFinanceRecords(options) {
    const { api, recordType = '记录', idField = 'id' } = options

    // State
    const loading = ref(false)
    const saving = ref(false)
    const records = ref([])
    const dialogVisible = ref(false)
    const isEditing = ref(false)
    const currentRecord = ref(null)

    // Form data (to be customized per record type)
    const formData = reactive({})

    /**
     * Calculate total amount from records
     */
    const totalAmount = computed(() => {
        return records.value.reduce((sum, record) => {
            return sum + (parseFloat(record.amount) || 0)
        }, 0)
    })

    /**
     * Fetch records for a contract
     * @param {number} contractId - Contract ID
     */
    const fetchRecords = async (contractId) => {
        if (!contractId) return
        loading.value = true
        try {
            const res = await api.getRecords(contractId)
            records.value = Array.isArray(res) ? res : (res.items || [])
        } catch (e) {
            console.error(`Failed to fetch ${recordType}:`, e)
            ElMessage.error(`获取${recordType}列表失败`)
        } finally {
            loading.value = false
        }
    }

    /**
     * Open dialog for creating new record
     * @param {Object} defaultValues - Default form values
     */
    const openCreateDialog = (defaultValues = {}) => {
        isEditing.value = false
        currentRecord.value = null
        Object.keys(formData).forEach(key => {
            formData[key] = defaultValues[key] !== undefined ? defaultValues[key] : null
        })
        dialogVisible.value = true
    }

    /**
     * Open dialog for editing existing record
     * @param {Object} record - Record to edit
     */
    const openEditDialog = (record) => {
        isEditing.value = true
        currentRecord.value = record
        Object.keys(formData).forEach(key => {
            formData[key] = record[key] !== undefined ? record[key] : null
        })
        dialogVisible.value = true
    }

    /**
     * Save record (create or update)
     * @param {number} contractId - Contract ID
     */
    const saveRecord = async (contractId) => {
        saving.value = true
        try {
            const data = { ...formData, contract_id: contractId }

            if (isEditing.value && currentRecord.value) {
                await api.updateRecord(contractId, currentRecord.value[idField], data)
                ElMessage.success(`${recordType}更新成功`)
            } else {
                await api.createRecord(contractId, data)
                ElMessage.success(`${recordType}创建成功`)
            }

            dialogVisible.value = false
            await fetchRecords(contractId)
            return true
        } catch (e) {
            console.error(`Failed to save ${recordType}:`, e)
            ElMessage.error(`保存${recordType}失败: ` + (e.response?.data?.message || e.message || '未知错误'))
            return false
        } finally {
            saving.value = false
        }
    }

    /**
     * Delete record with confirmation
     * @param {Object} record - Record to delete
     * @param {number} contractId - Contract ID
     */
    const deleteRecord = async (record, contractId) => {
        try {
            await ElMessageBox.confirm(
                `确认删除此${recordType}记录吗？`,
                '警告',
                {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }
            )

            await api.deleteRecord(contractId, record[idField])
            ElMessage.success(`${recordType}删除成功`)
            await fetchRecords(contractId)
            return true
        } catch (e) {
            if (e !== 'cancel') {
                console.error(`Failed to delete ${recordType}:`, e)
                ElMessage.error(`删除${recordType}失败`)
            }
            return false
        }
    }

    /**
     * Reset form data
     * @param {Object} defaultValues - Default values to reset to
     */
    const resetForm = (defaultValues = {}) => {
        Object.keys(formData).forEach(key => {
            formData[key] = defaultValues[key] !== undefined ? defaultValues[key] : null
        })
    }

    return {
        // State
        loading,
        saving,
        records,
        dialogVisible,
        isEditing,
        currentRecord,
        formData,

        // Computed
        totalAmount,

        // Methods
        fetchRecords,
        openCreateDialog,
        openEditDialog,
        saveRecord,
        deleteRecord,
        resetForm
    }
}

/**
 * Composable for PDF file handling
 * Handles upload, preview, and download of PDF files
 */
export function usePdfUpload(options = {}) {
    const { maxSize = 10 } = options // Max size in MB

    const uploading = ref(false)
    const pdfUrl = ref('')
    const pdfName = ref('')
    const previewVisible = ref(false)

    /**
     * Handle file upload
     * @param {File} file - File to upload
     * @param {Function} uploadFn - Upload function
     */
    const handleUpload = async (file, uploadFn) => {
        // Validate file type
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            ElMessage.error('只支持上传 PDF 文件')
            return false
        }

        // Validate file size
        if (file.size / 1024 / 1024 > maxSize) {
            ElMessage.error(`文件大小不能超过 ${maxSize}MB`)
            return false
        }

        uploading.value = true
        try {
            const result = await uploadFn(file)
            pdfUrl.value = result.path || result.url
            pdfName.value = file.name
            ElMessage.success('上传成功')
            return result
        } catch (e) {
            console.error('Upload failed:', e)
            ElMessage.error('上传失败: ' + (e.message || '未知错误'))
            return false
        } finally {
            uploading.value = false
        }
    }

    /**
     * Open PDF preview
     * @param {string} url - PDF URL
     */
    const openPreview = (url) => {
        if (url) {
            pdfUrl.value = url
            previewVisible.value = true
        }
    }

    /**
     * Download PDF file
     * @param {string} url - PDF URL
     * @param {string} filename - Downloaded file name
     */
    const downloadPdf = (url, filename = 'document.pdf') => {
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        link.target = '_blank'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
    }

    /**
     * Clear current PDF
     */
    const clearPdf = () => {
        pdfUrl.value = ''
        pdfName.value = ''
    }

    return {
        uploading,
        pdfUrl,
        pdfName,
        previewVisible,
        handleUpload,
        openPreview,
        downloadPdf,
        clearPdf
    }
}

/**
 * Composable for form validation
 * Provides common validation rules
 */
export function useFormValidation() {
    const rules = {
        required: (message = '此字段为必填项') => ({
            required: true,
            message,
            trigger: 'blur'
        }),

        requiredSelect: (message = '请选择') => ({
            required: true,
            message,
            trigger: 'change'
        }),

        minLength: (min, message) => ({
            min,
            message: message || `最少输入 ${min} 个字符`,
            trigger: 'blur'
        }),

        maxLength: (max, message) => ({
            max,
            message: message || `最多输入 ${max} 个字符`,
            trigger: 'blur'
        }),

        number: (message = '请输入有效数字') => ({
            type: 'number',
            message,
            trigger: 'blur',
            transform: (value) => Number(value)
        }),

        positiveNumber: (message = '请输入正数') => ({
            validator: (rule, value, callback) => {
                if (value !== '' && value !== null && value !== undefined) {
                    const num = Number(value)
                    if (isNaN(num) || num <= 0) {
                        callback(new Error(message))
                    } else {
                        callback()
                    }
                } else {
                    callback()
                }
            },
            trigger: 'blur'
        }),

        nonNegativeNumber: (message = '请输入非负数') => ({
            validator: (rule, value, callback) => {
                if (value !== '' && value !== null && value !== undefined) {
                    const num = Number(value)
                    if (isNaN(num) || num < 0) {
                        callback(new Error(message))
                    } else {
                        callback()
                    }
                } else {
                    callback()
                }
            },
            trigger: 'blur'
        }),

        email: (message = '请输入有效的邮箱地址') => ({
            type: 'email',
            message,
            trigger: 'blur'
        }),

        phone: (message = '请输入有效的手机号') => ({
            pattern: /^1[3-9]\d{9}$/,
            message,
            trigger: 'blur'
        }),

        date: (message = '请选择日期') => ({
            required: true,
            message,
            trigger: 'change'
        })
    }

    /**
     * Create contract amount validation rule
     * @param {boolean} required - Whether field is required
     */
    const amountRule = (required = true) => {
        const ruleList = [rules.nonNegativeNumber('金额不能为负')]
        if (required) {
            ruleList.unshift(rules.required('请输入金额'))
        }
        return ruleList
    }

    /**
     * Create contract code validation rule
     */
    const contractCodeRule = () => [
        rules.maxLength(50, '合同编号不能超过50个字符')
    ]

    /**
     * Create contract name validation rule
     */
    const contractNameRule = () => [
        rules.required('请输入合同名称'),
        rules.maxLength(200, '合同名称不能超过200个字符')
    ]

    return {
        rules,
        amountRule,
        contractCodeRule,
        contractNameRule
    }
}
