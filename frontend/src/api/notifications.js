import request from '@/utils/request'
import { buildNotifications } from '@/utils/notificationAdapter'

export async function fetchNotifications() {
    const [audits, dashboardStats] = await Promise.all([
        request.get('/audit/logs', { params: { page: 1, page_size: 10 } }).catch(() => ({ items: [] })),
        request.get('/dashboard/stats').catch(() => ({ reminders: [] }))
    ])

    return buildNotifications({
        audits: audits.items || audits.results || [],
        reminders: dashboardStats.reminders || []
    })
}
