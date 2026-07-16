import { describe, expect, it } from 'vitest'
import {
  createPeriodSelection,
  formatPeriodLabel,
  resolvePeriodAnchor,
  syncPeriodSelection
} from '@/views/reports/reportPeriod.helpers'

describe('report period helpers', () => {
  const date = new Date(2026, 6, 16)

  it('resolves month, quarter, half-year and year selections to report anchors', () => {
    const selection = createPeriodSelection(date)
    selection.month = '2025-12'
    selection.quarterYear = '2024'
    selection.quarter = 2
    selection.halfYear = '2023'
    selection.half = 2
    selection.year = '2022'

    expect(resolvePeriodAnchor('monthly', selection, date)).toEqual({ year: 2025, month: 12 })
    expect(resolvePeriodAnchor('quarterly', selection, date)).toEqual({ year: 2024, month: 4 })
    expect(resolvePeriodAnchor('half_yearly', selection, date)).toEqual({ year: 2023, month: 7 })
    expect(resolvePeriodAnchor('yearly', selection, date)).toEqual({ year: 2022, month: 1 })
  })

  it('keeps every period selector aligned to the queried anchor', () => {
    const selection = createPeriodSelection(date)
    syncPeriodSelection(selection, 2027, 10)

    expect(selection).toEqual({
      month: '2027-10',
      quarterYear: '2027',
      quarter: 4,
      halfYear: '2027',
      half: 2,
      year: '2027'
    })
    expect(formatPeriodLabel('quarterly', 2027, 10)).toBe('2027年第4季度')
    expect(formatPeriodLabel('half_yearly', 2027, 10)).toBe('2027年下半年')
  })
})
