import { describe, expect, it } from 'vitest'
import {
  buildExportParams,
  buildSettlementSummaries
} from '@/views/reports/reportDashboard.helpers'

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

  it('includes company category and upstream contract filters when provided', () => {
    expect(buildExportParams({
      dateRange: ['2026-04-01', '2026-04-30'],
      companyCategory: '市政工程',
      upstreamContractName: '上游合同一',
      status: '全部'
    })).toEqual({
      start_date: '2026-04-01',
      end_date: '2026-04-30',
      company_category: '市政工程',
      upstream_contract_name: '上游合同一'
    })
  })
})

describe('buildSettlementSummaries', () => {
  it('labels the first cell and totals only configured amount columns', () => {
    const columns = [
      { property: 'serial_number' },
      { property: 'contract_name' },
      { property: 'contract_amount' },
      { property: 'settlement_amount' }
    ]
    const data = [
      { contract_amount: 1000.5, settlement_amount: 900 },
      { contract_amount: '2000', settlement_amount: null },
      { contract_amount: 'invalid', settlement_amount: 850.25 }
    ]

    expect(buildSettlementSummaries(
      columns,
      data,
      ['contract_amount', 'settlement_amount']
    )).toEqual(['合计', '', '3,000.50', '1,750.25'])
  })
})
