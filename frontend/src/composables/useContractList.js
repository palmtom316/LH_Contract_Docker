/**
 * Composable for contract list operations
 * Reduces code duplication across UpstreamList, DownstreamList, ManagementList
 */
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { downloadExcel, generateFilename } from '@/utils/download'
import { getFileUrl, formatMoney, getStatusType } from '@/utils/common'

/**
 * Create a reusable contract list composable
 * @param {Object} options - Configuration options
 * @param {Object} options.api - API module with getContracts, deleteContract, exportContracts
 * @param {string} options.contractType - Type name for messages (e.g., '上游合同')
 * @param {string} options.exportPrefix - Prefix for export filename
 */
export function useContractList(options) {
    const { api, contractType = '合同', exportPrefix = '合同导出' } = options

    // State
    const loading = ref(false)
    const exporting = ref(false)
    const list = ref([])
    const total = ref(0)

    // Query parameters
    const queryParams = reactive({
        page: 1,
        page_size: 10,
        keyword: '',
        status: ''
    })

    /**
     * Fetch contract list
     */
    const getList = async () => {
        loading.value = true
        try {
            const res = await api.getContracts(queryParams)
            list.value = res.items || []
            total.value = res.total || 0
        } catch (e) {
            console.error('Failed to fetch list:', e)
            ElMessage.error(`获取${contractType}列表失败`)
        } finally {
            loading.value = false
        }
    }

    /**
     * Handle search query
     */
    const handleQuery = () => {
        queryParams.page = 1
        getList()
    }

    /**
     * Reset query parameters
     */
    const resetQuery = () => {
        queryParams.keyword = ''
        queryParams.status = ''
        handleQuery()
    }

    /**
     * Handle delete with confirmation
     * @param {Object} row - Contract row data
     * @param {string} nameField - Field name for display (default: 'contract_name')
     */
    const handleDelete = async (row, nameField = 'contract_name') => {
        try {
            await ElMessageBox.confirm(
                `确认删除${contractType} "${row[nameField]}" 吗?`,
                '警告',
                {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }
            )
            await api.deleteContract(row.id)
            ElMessage.success('删除成功')
            getList()
        } catch (e) {
            if (e !== 'cancel') {
                console.error('Delete failed:', e)
                ElMessage.error('删除失败')
            }
        }
    }

    /**
     * Handle Excel export
     */
    const handleExport = async () => {
        exporting.value = true
        try {
            ElMessage.info('正在导出...')
            const res = await api.exportContracts(queryParams)
            const filename = generateFilename(exportPrefix, 'xlsx')
            downloadExcel(res, filename)
            ElMessage.success('导出成功')
        } catch (e) {
            console.error('Export failed:', e)
            ElMessage.error('导出失败: ' + (e.message || e))
        } finally {
            exporting.value = false
        }
    }


    return {
        // State
        loading,
        exporting,
        list,
        total,
        queryParams,

        // Methods
        getList,
        handleQuery,
        resetQuery,
        handleDelete,
        handleExport,

        // Utilities
        getStatusType,
        formatMoney,
        getFileUrl
    }
}

/**
 * Composable for mobile detection
 */
export function useMobileDetection() {
    const isMobile = ref(false)

    const checkIsMobile = () => {
        isMobile.value = window.innerWidth < 768
    }

    return {
        isMobile,
        checkIsMobile
    }
}

/**
 * Composable for table summary row
 */
export function useTableSummary() {
    /**
     * Generate summary row for table
     * @param {Object} param - Element Plus summary params
     * @param {Array} sumColumns - Column properties to sum
     * @returns {Array} Summary row values
     */
    const getSummaries = (param, sumColumns = ['contract_amount']) => {
        const { columns, data } = param
        const sums = []

        columns.forEach((column, index) => {
            if (index === 0) {
                sums[index] = '合计'
                return
            }

            if (sumColumns.includes(column.property)) {
                const values = data.map(item => Number(item[column.property]))
                if (!values.every(value => Number.isNaN(value))) {
                    const sum = values.reduce((prev, curr) => {
                        const value = Number(curr)
                        return Number.isNaN(value) ? prev : prev + curr
                    }, 0)
                    sums[index] = '¥ ' + sum.toLocaleString('zh-CN', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })
                } else {
                    sums[index] = '0.00'
                }
            } else {
                sums[index] = ''
            }
        })

        return sums
    }

    const footerCellStyle = () => ({
        backgroundColor: '#FFFF00',
        color: '#000000',
        fontWeight: 'bold',
        fontSize: '16px'
    })

    return {
        getSummaries,
        footerCellStyle
    }
}
