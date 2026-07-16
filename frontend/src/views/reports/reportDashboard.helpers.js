export function buildExportParams(filters = {}) {
  const params = {}

  const dateRange = filters.dateRange || []
  if (dateRange[0]) {
    params.start_date = dateRange[0]
  }
  if (dateRange[1]) {
    params.end_date = dateRange[1]
  }

  if (filters.status && filters.status !== '全部') {
    params.status = filters.status
  }

  if (filters.companyCategory) {
    params.company_category = filters.companyCategory
  }

  if (filters.upstreamContractName) {
    params.upstream_contract_name = filters.upstreamContractName
  }

  return params
}

export function buildSettlementSummaries(columns = [], data = [], amountFields = []) {
  const amountFieldSet = new Set(amountFields)

  return columns.map((column, index) => {
    if (index === 0) return '合计'
    if (!amountFieldSet.has(column.property)) return ''

    const total = data.reduce((sum, row) => {
      const value = Number(row[column.property])
      return Number.isFinite(value) ? sum + value : sum
    }, 0)

    return total.toLocaleString('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })
  })
}
