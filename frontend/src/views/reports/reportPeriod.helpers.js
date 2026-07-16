export const REPORT_PERIODS = [
  { key: 'monthly', label: '月度' },
  { key: 'quarterly', label: '季度' },
  { key: 'half_yearly', label: '半年度' },
  { key: 'yearly', label: '年度' }
]

export function createPeriodSelection(date = new Date()) {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  return {
    month: `${year}-${String(month).padStart(2, '0')}`,
    quarterYear: String(year),
    quarter: Math.floor((month - 1) / 3) + 1,
    halfYear: String(year),
    half: month <= 6 ? 1 : 2,
    year: String(year)
  }
}

export function resolvePeriodAnchor(periodType, selection, fallbackDate = new Date()) {
  const fallback = createPeriodSelection(fallbackDate)
  if (periodType === 'monthly') {
    const [year, month] = String(selection.month || fallback.month).split('-').map(Number)
    return { year, month }
  }
  if (periodType === 'quarterly') {
    return {
      year: Number(selection.quarterYear || fallback.quarterYear),
      month: (Number(selection.quarter || fallback.quarter) - 1) * 3 + 1
    }
  }
  if (periodType === 'half_yearly') {
    return {
      year: Number(selection.halfYear || fallback.halfYear),
      month: Number(selection.half || fallback.half) === 1 ? 1 : 7
    }
  }
  return { year: Number(selection.year || fallback.year), month: 1 }
}

export function syncPeriodSelection(selection, year, month) {
  const normalizedMonth = Math.max(1, Math.min(12, Number(month)))
  const normalizedYear = Number(year)
  selection.month = `${normalizedYear}-${String(normalizedMonth).padStart(2, '0')}`
  selection.quarterYear = String(normalizedYear)
  selection.quarter = Math.floor((normalizedMonth - 1) / 3) + 1
  selection.halfYear = String(normalizedYear)
  selection.half = normalizedMonth <= 6 ? 1 : 2
  selection.year = String(normalizedYear)
}

export function formatPeriodLabel(periodType, year, month) {
  if (periodType === 'monthly') return `${year}年${month}月`
  if (periodType === 'quarterly') return `${year}年第${Math.floor((month - 1) / 3) + 1}季度`
  if (periodType === 'half_yearly') return `${year}年${month <= 6 ? '上半年' : '下半年'}`
  return `${year}年`
}
