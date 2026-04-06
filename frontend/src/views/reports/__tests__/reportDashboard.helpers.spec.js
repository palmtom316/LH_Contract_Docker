import { describe, expect, it } from 'vitest'
import { buildExportParams } from '@/views/reports/reportDashboard.helpers'

describe('buildExportParams', () => {
  it('includes normalized date range and status when valid', () => {
    expect(buildExportParams({ dateRange: ['2026-04-01', '2026-04-06'], status: '执行中' })).toEqual({
      start_date: '2026-04-01',
      end_date: '2026-04-06',
      status: '执行中'
    })
  })

  it('omits empty dates', () => {
    expect(buildExportParams({ dateRange: ['', ''], status: '全部' })).toEqual({})
  })

  it('keeps partial date ranges (start only)', () => {
    expect(buildExportParams({ dateRange: ['2026-04-01', ''], status: '全部' })).toEqual({
      start_date: '2026-04-01'
    })
  })

  it('keeps partial date ranges (end only)', () => {
    expect(buildExportParams({ dateRange: ['', '2026-04-30'] })).toEqual({
      end_date: '2026-04-30'
    })
  })
})
