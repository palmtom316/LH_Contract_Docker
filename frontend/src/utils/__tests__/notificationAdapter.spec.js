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
    vi.clearAllMocks()
  })

  it('uses real audit and contract endpoints', async () => {
    request.get
      .mockResolvedValueOnce({
        items: [{ id: 10, description: '系统登录', created_at: '2026-04-05T08:00:00Z' }]
      })
      .mockResolvedValueOnce({
        items: [{ id: 22, contract_name: 'A合同', status: '质保到期', updated_at: '2026-04-06T08:00:00Z' }]
      })
      .mockResolvedValueOnce({ items: [] })
      .mockResolvedValueOnce({ items: [] })

    await fetchNotifications()

    expect(request.get).toHaveBeenNthCalledWith(1, '/audit/', {
      params: { page: 1, page_size: 10 },
      suppressGlobalErrorMessage: true
    })
    expect(request.get).toHaveBeenNthCalledWith(2, '/contracts/upstream/', {
      params: { page: 1, page_size: 10, status: '质保到期' }
    })
    expect(request.get).toHaveBeenNthCalledWith(3, '/contracts/downstream/', {
      params: { page: 1, page_size: 10, status: '质保到期' }
    })
    expect(request.get).toHaveBeenNthCalledWith(4, '/contracts/management/', {
      params: { page: 1, page_size: 10, status: '质保到期' }
    })
  })

  it('throws when all notification sources fail', async () => {
    request.get.mockRejectedValue(new Error('network error'))

    await expect(fetchNotifications()).rejects.toThrow('Failed to load notifications')
  })

  it('maps contract reminder timestamp from warranty_date', async () => {
    request.get
      .mockResolvedValueOnce({ items: [] })
      .mockResolvedValueOnce({
        items: [
          {
            id: 33,
            contract_name: 'B合同',
            status: '质保到期',
            warranty_date: '2026-05-01',
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
      createdAt: '2026-05-01'
    })
  })
})
