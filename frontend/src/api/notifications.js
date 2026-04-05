import request from '@/utils/request'
import { buildNotifications } from '@/utils/notificationAdapter'

function mapContractReminders(items = []) {
    return items.map(item => ({
        id: `upstream-${item.id}`,
        type: 'contract_expiry',
        title: item.contract_name || item.contract_code || '合同质保到期提醒',
        subtitle: item.status || '质保到期',
        due_at: item.warranty_date || item.end_date || item.updated_at || item.created_at
    }))
}

export async function fetchNotifications() {
    const [auditsResult, remindersResult] = await Promise.allSettled([
        request.get('/audit/', { params: { page: 1, page_size: 10 } }),
        request.get('/contracts/upstream/', { params: { page: 1, page_size: 10, status: '质保到期' } })
    ])

    if (auditsResult.status === 'rejected' && remindersResult.status === 'rejected') {
        throw new Error('Failed to load notifications')
    }

    const audits = auditsResult.status === 'fulfilled' ? (auditsResult.value.items || auditsResult.value.results || []) : []
    const reminders = remindersResult.status === 'fulfilled'
        ? mapContractReminders(remindersResult.value.items || remindersResult.value.results || [])
        : []

    return buildNotifications({
        audits,
        reminders
    })
}
