const CATEGORY_MAP = {
    contract_expiry: 'contract_expiry',
    audit: 'audit'
}

const CATEGORY_ORDER = {
    contract_expiry: 0,
    audit: 1,
    general: 2
}

function toEpoch(value) {
    if (!value) return 0
    const time = new Date(value).getTime()
    return Number.isNaN(time) ? 0 : time
}

function normalizeType(type) {
    return CATEGORY_MAP[type] || 'general'
}

export function buildNotifications({ audits = [], reminders = [] }) {
    const auditItems = audits.map(item => ({
        id: `audit-${item.id}`,
        type: 'audit',
        title: item.description || item.action || '系统审计事件',
        subtitle: '系统审计事件',
        createdAt: item.created_at,
        unread: true
    }))

    const reminderItems = reminders.map(item => {
        const type = normalizeType(item.type)
        return {
            id: String(item.id),
            type,
            title: item.title || '业务提醒',
            subtitle: item.subtitle || '业务提醒',
            createdAt: item.due_at || item.created_at,
            unread: true
        }
    })

    return [...auditItems, ...reminderItems].sort((a, b) => {
        const timeDiff = toEpoch(b.createdAt) - toEpoch(a.createdAt)
        if (timeDiff !== 0) return timeDiff
        const categoryDiff = (CATEGORY_ORDER[a.type] ?? 99) - (CATEGORY_ORDER[b.type] ?? 99)
        if (categoryDiff !== 0) return categoryDiff
        return String(a.id).localeCompare(String(b.id))
    })
}
