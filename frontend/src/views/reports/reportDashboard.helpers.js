export function buildExportParams(filters = {}) {
  const params = {}

  const dateRange = filters.dateRange || []
  if (dateRange[0] && dateRange[1]) {
    params.start_date = dateRange[0]
    params.end_date = dateRange[1]
  }

  if (filters.status && filters.status !== '全部') {
    params.status = filters.status
  }

  return params
}
