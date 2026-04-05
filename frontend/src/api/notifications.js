import request from '@/utils/request'
import { buildNotifications } from '@/utils/notificationAdapter'

function isAdminUser() {
    try {
        let raw = '{}'
        if (typeof localStorage !== 'undefined') {
            raw = localStorage.getItem('user_info') || '{}'
        } else if (globalThis.window?.localStorage) {
            raw = globalThis.window.localStorage.getItem('user_info') || '{}'
        } else if (globalThis.localStorage) {
            raw = globalThis.localStorage.getItem('user_info') || '{}'
        }
        const user = JSON.parse(raw)
        const role = String(user.role || '').toUpperCase()
        return role === 'ADMIN' || user.is_superuser === true
    } catch {
        return false
    }
}

function mapContractReminders(items = [], source = 'contract') {
    return items.map(item => ({
        id: `${source}-${item.id}`,
        type: 'contract_expiry',
        title: item.contract_name || item.contract_code || '合同质保到期提醒',
        subtitle: item.status || '质保到期',
        due_at: item.updated_at || item.created_at || item.end_date
    }))
}

export async function fetchNotifications() {
    const includeAudit = isAdminUser()
    const requests = [
        request.get('/contracts/upstream/', { params: { page: 1, page_size: 10, status: '质保到期' } }),
        request.get('/contracts/downstream/', { params: { page: 1, page_size: 10, status: '质保到期' } }),
        request.get('/contracts/management/', { params: { page: 1, page_size: 10, status: '质保到期' } })
    ]

    if (includeAudit) {
        requests.unshift(
            request.get('/audit/', {
                params: { page: 1, page_size: 10 },
                suppressGlobalErrorMessage: true
            })
        )
    }

    const results = await Promise.allSettled(requests)
    const allFailed = results.every(result => result.status === 'rejected')
    if (allFailed) {
        throw new Error('Failed to load notifications')
    }

    const auditResult = includeAudit ? results[0] : null
    const upstreamResult = includeAudit ? results[1] : results[0]
    const downstreamResult = includeAudit ? results[2] : results[1]
    const managementResult = includeAudit ? results[3] : results[2]

    const audits = auditResult?.status === 'fulfilled' ? (auditResult.value.items || auditResult.value.results || []) : []
    const reminders = [
        ...(upstreamResult.status === 'fulfilled' ? mapContractReminders(upstreamResult.value.items || upstreamResult.value.results || [], 'upstream') : []),
        ...(downstreamResult.status === 'fulfilled' ? mapContractReminders(downstreamResult.value.items || downstreamResult.value.results || [], 'downstream') : []),
        ...(managementResult.status === 'fulfilled' ? mapContractReminders(managementResult.value.items || managementResult.value.results || [], 'management') : [])
    ]

    return buildNotifications({
        audits,
        reminders
    })
}
