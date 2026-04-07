import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useSystemStore } from '../system'

const { fetchNotificationsMock } = vi.hoisted(() => ({
  fetchNotificationsMock: vi.fn()
}))

vi.mock('@/api/notifications', () => ({
  fetchNotifications: fetchNotificationsMock
}))

describe('system store notifications', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    fetchNotificationsMock.mockReset()
    fetchNotificationsMock.mockResolvedValue([
      {
        id: 'remote-1',
        type: 'general',
        title: '远端通知',
        subtitle: '远端副标题',
        createdAt: '2026-04-07T09:00:00.000Z',
        unread: true
      }
    ])
  })

  it('supports local notification creation, read, and delete actions', async () => {
    const store = useSystemStore()

    await store.fetchNotifications()
    store.pushNotification({
      id: 'local-blocked-delete',
      type: 'general',
      title: '删除受阻',
      subtitle: '有关联数据',
      createdAt: '2026-04-07T10:00:00.000Z',
      unread: true
    })

    expect(store.notifications.map(item => item.id)).toContain('local-blocked-delete')
    expect(store.notifications.find(item => item.id === 'local-blocked-delete')?.unread).toBe(true)

    store.markNotificationRead('local-blocked-delete')
    expect(store.notifications.find(item => item.id === 'local-blocked-delete')?.unread).toBe(false)

    store.removeNotification('local-blocked-delete')
    expect(store.notifications.map(item => item.id)).not.toContain('local-blocked-delete')
  })
})
