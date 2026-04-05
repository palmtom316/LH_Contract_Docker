import request from '@/utils/request'
import { buildNotifications } from '@/utils/notificationAdapter'

function getPersistedAuthContext() {
    try {
        let userRaw = '{}'
        let permissionsRaw = '[]'
        if (typeof localStorage !== 'undefined') {
            userRaw = localStorage.getItem('user_info') || '{}'
            permissionsRaw = localStorage.getItem('user_permissions') || '[]'
        } else if (globalThis.window?.localStorage) {
            userRaw = globalThis.window.localStorage.getItem('user_info') || '{}'
            permissionsRaw = globalThis.window.localStorage.getItem('user_permissions') || '[]'
        } else if (globalThis.localStorage) {
            userRaw = globalThis.localStorage.getItem('user_info') || '{}'
            permissionsRaw = globalThis.localStorage.getItem('user_permissions') || '[]'
        }
        return {
            user: JSON.parse(userRaw),
            permissions: JSON.parse(permissionsRaw)
        }
    } catch {
        return { user: {}, permissions: [] }
    }
}

function isAdminUser() {
    const { user } = getPersistedAuthContext()
    const role = String(user.role || '').toUpperCase()
    return role === 'ADMIN' || user.is_superuser === true
}

function canViewUpstreamContracts() {
    const { user, permissions } = getPersistedAuthContext()
    if (user.is_superuser === true) return true
    return permissions.includes('view_upstream_contracts') || permissions.includes('view_upstream_basic_info')
}

function canViewDownstreamContracts() {
    const { user, permissions } = getPersistedAuthContext()
    if (user.is_superuser === true) return true
    return permissions.includes('view_downstream_contracts') || permissions.includes('view_downstream_basic_info')
}

function canViewManagementContracts() {
    const { user, permissions } = getPersistedAuthContext()
    if (user.is_superuser === true) return true
    return permissions.includes('view_management_contracts') || permissions.includes('view_management_basic_info')
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
    const includeUpstream = canViewUpstreamContracts()
    const includeDownstream = canViewDownstreamContracts()
    const includeManagement = canViewManagementContracts()
    const requests = []

    if (includeUpstream) {
        requests.push(request.get('/contracts/upstream/', { params: { page: 1, page_size: 10, status: '质保到期' } }))
    }
    if (includeDownstream) {
        requests.push(request.get('/contracts/downstream/', { params: { page: 1, page_size: 10, status: '质保到期' } }))
    }
    if (includeManagement) {
        requests.push(request.get('/contracts/management/', { params: { page: 1, page_size: 10, status: '质保到期' } }))
    }

    if (includeAudit) {
        requests.unshift(
            request.get('/audit/', {
                params: { page: 1, page_size: 10 },
                suppressGlobalErrorMessage: true
            })
        )
    }

    if (requests.length === 0) {
        return buildNotifications({ audits: [], reminders: [] })
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
    const fallbackResult = { status: 'rejected' }

    const audits = auditResult?.status === 'fulfilled' ? (auditResult.value.items || auditResult.value.results || []) : []
    const reminders = [
        ...((upstreamResult || fallbackResult).status === 'fulfilled' ? mapContractReminders(upstreamResult.value.items || upstreamResult.value.results || [], 'upstream') : []),
        ...((downstreamResult || fallbackResult).status === 'fulfilled' ? mapContractReminders(downstreamResult.value.items || downstreamResult.value.results || [], 'downstream') : []),
        ...((managementResult || fallbackResult).status === 'fulfilled' ? mapContractReminders(managementResult.value.items || managementResult.value.results || [], 'management') : [])
    ]

    return buildNotifications({
        audits,
        reminders
    })
}
