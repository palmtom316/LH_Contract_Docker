import { beforeEach, describe, expect, it, vi } from 'vitest'
import { buildNotifications } from '../notificationAdapter'
import request from '@/utils/request'
import { fetchNotifications } from '@/api/notifications'

vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn()
  }
}))

describe('buildNotifications', () => {
  it('maps audit and contract reminders into sorted notification items', () => {
    const result = buildNotifications({
      audits: [
        { id: 1, action: 'LOGIN', description: '管理员登录', created_at: '2026-04-05T08:00:00Z' }
      ],
      reminders: [
        { id: 'exp-1', type: 'contract_expiry', title: '合同将到期', due_at: '2026-04-06T08:00:00Z' }
      ]
    })

    expect(result[0]).toMatchObject({
      type: 'contract_expiry',
      title: '合同将到期'
    })
    expect(result[1]).toMatchObject({
      type: 'audit',
      title: '管理员登录'
    })
  })
})

describe('fetchNotifications API facade', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.clearAllMocks()
    localStorage.clear()
    localStorage.setItem('user_permissions', JSON.stringify([
      'view_upstream_basic_info',
      'view_downstream_basic_info',
      'view_management_basic_info'
    ]))
  })

  it('uses contract reminder endpoints', async () => {
    request.get
      .mockResolvedValueOnce({
        items: [{ id: 22, contract_name: 'A合同', status: '质保到期', updated_at: '2026-04-06T08:00:00Z' }]
      })
      .mockResolvedValueOnce({ items: [] })
      .mockResolvedValueOnce({ items: [] })

    await fetchNotifications()

    expect(request.get).toHaveBeenNthCalledWith(1, '/contracts/upstream/', {
      params: { page: 1, page_size: 10, status: '质保到期' }
    })
    expect(request.get).toHaveBeenNthCalledWith(2, '/contracts/downstream/', {
      params: { page: 1, page_size: 10, status: '质保到期' }
    })
    expect(request.get).toHaveBeenNthCalledWith(3, '/contracts/management/', {
      params: { page: 1, page_size: 10, status: '质保到期' }
    })
  })

  it('skips audit endpoint for non-admin users', async () => {
    localStorage.setItem('user_info', JSON.stringify({ role: 'BIDDING' }))

    request.get
      .mockResolvedValueOnce({ items: [] })
      .mockResolvedValueOnce({ items: [] })
      .mockResolvedValueOnce({ items: [] })

    await fetchNotifications()

    expect(request.get).toHaveBeenCalledTimes(3)
    expect(request.get).toHaveBeenNthCalledWith(1, '/contracts/upstream/', {
      params: { page: 1, page_size: 10, status: '质保到期' }
    })
    expect(request.get).toHaveBeenNthCalledWith(2, '/contracts/downstream/', {
      params: { page: 1, page_size: 10, status: '质保到期' }
    })
    expect(request.get).toHaveBeenNthCalledWith(3, '/contracts/management/', {
      params: { page: 1, page_size: 10, status: '质保到期' }
    })
  })

  it('only fetches reminder sources the role can view', async () => {
    localStorage.setItem('user_info', JSON.stringify({ role: 'BIDDING' }))
    localStorage.setItem('user_permissions', JSON.stringify(['view_upstream_basic_info']))
    request.get.mockResolvedValueOnce({ items: [] })

    await fetchNotifications()

    expect(request.get).toHaveBeenCalledTimes(1)
    expect(request.get).toHaveBeenCalledWith('/contracts/upstream/', {
      params: { page: 1, page_size: 10, status: '质保到期' }
    })
  })

  it('throws when all notification sources fail', async () => {
    request.get.mockRejectedValue(new Error('network error'))

    await expect(fetchNotifications()).rejects.toThrow('Failed to load notifications')
  })

  it('maps contract reminder timestamp from updated_at fallback', async () => {
    request.get
      .mockResolvedValueOnce({
        items: [
          {
            id: 33,
            contract_name: 'B合同',
            status: '质保到期',
            updated_at: '2026-04-01T08:00:00Z'
          }
        ]
      })
      .mockResolvedValueOnce({ items: [] })
      .mockResolvedValueOnce({ items: [] })

    const result = await fetchNotifications()

    expect(result[0]).toMatchObject({
      id: 'upstream-33',
      type: 'contract_expiry',
      title: 'B合同',
      createdAt: '2026-04-01T08:00:00Z'
    })
  })

  it('scopes reminder ids by source and falls back timestamp from created_at then end_date', async () => {
    request.get
      .mockResolvedValueOnce({
        items: [{ id: 1, contract_name: '上游合同', status: '质保到期', created_at: '2026-04-02T08:00:00Z' }]
      })
      .mockResolvedValueOnce({
        items: [{ id: 1, contract_name: '下游合同', status: '质保到期', end_date: '2026-04-03' }]
      })
      .mockResolvedValueOnce({
        items: [{ id: 1, contract_name: '管理合同', status: '质保到期', updated_at: '2026-04-04T09:00:00Z' }]
      })

    const result = await fetchNotifications()

    const ids = result.map(item => item.id)
    expect(ids).toContain('upstream-1')
    expect(ids).toContain('downstream-1')
    expect(ids).toContain('management-1')
    expect(result.find(item => item.id === 'upstream-1')?.createdAt).toBe('2026-04-02T08:00:00Z')
    expect(result.find(item => item.id === 'downstream-1')?.createdAt).toBe('2026-04-03')
    expect(result.find(item => item.id === 'management-1')?.createdAt).toBe('2026-04-04T09:00:00Z')
  })
})
