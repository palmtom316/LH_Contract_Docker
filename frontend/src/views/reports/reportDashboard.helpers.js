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
