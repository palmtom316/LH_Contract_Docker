export interface ParsedFlexibleDate {
  isoValue: string
  displayValue: string
  year: number
  month: number
  day: number
}

const FLEXIBLE_SEPARATOR_RE = /[.\-。]/g

export function normalizeFlexibleDateInput(raw: string): string {
  return raw.trim().replace(/\s+/g, '').replace(FLEXIBLE_SEPARATOR_RE, '/')
}

export function isValidDateParts(year: number, month: number, day: number): boolean {
  if (!Number.isInteger(year) || !Number.isInteger(month) || !Number.isInteger(day)) return false
  if (month < 1 || month > 12 || day < 1) return false

  const candidate = new Date(year, month - 1, day)
  return (
    candidate.getFullYear() === year &&
    candidate.getMonth() === month - 1 &&
    candidate.getDate() === day
  )
}

export function formatDateInputDisplay(isoValue?: string | null): string {
  if (!isoValue) return ''

  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoValue.trim())
  if (!match) return ''

  return `${match[1]}/${match[2]}/${match[3]}`
}

export function parseFlexibleDateInput(raw?: string | null): ParsedFlexibleDate | null {
  if (!raw) return null

  const normalized = normalizeFlexibleDateInput(raw)
  const match = /^(\d{2}|\d{4})\/(\d{1,2})\/(\d{1,2})$/.exec(normalized)
  if (!match) return null

  const year = match[1].length === 2 ? 2000 + Number(match[1]) : Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])

  if (!isValidDateParts(year, month, day)) return null

  const yyyy = String(year).padStart(4, '0')
  const mm = String(month).padStart(2, '0')
  const dd = String(day).padStart(2, '0')

  return {
    isoValue: `${yyyy}-${mm}-${dd}`,
    displayValue: `${yyyy}/${mm}/${dd}`,
    year,
    month,
    day
  }
}
