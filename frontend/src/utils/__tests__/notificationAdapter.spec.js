import { describe, expect, it } from 'vitest'
import { buildNotifications } from '../notificationAdapter'

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
