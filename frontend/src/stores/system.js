
import { defineStore } from 'pinia'
import request from '@/utils/request'
import { ref } from 'vue'
import { fetchNotifications as fetchNotificationsApi } from '@/api/notifications'

const NOTIFICATION_READ_KEY = 'lh_notifications_read'
const NOTIFICATION_DELETED_KEY = 'lh_notifications_deleted'
const NOTIFICATION_LOCAL_KEY = 'lh_notifications_local'

function getNotificationScope() {
    try {
        const user = JSON.parse(localStorage.getItem('user_info') || '{}')
        if (user.id !== undefined && user.id !== null && user.id !== '') {
            return `user-${user.id}`
        }
        if (user.username) {
            return `user-${user.username}`
        }
    } catch {
        // Fall back to anonymous scope.
    }
    return 'anonymous'
}

function scopedNotificationKey(baseKey, scope) {
    return `${baseKey}:${scope}`
}

function readJsonStorage(key, fallback) {
    try {
        const raw = localStorage.getItem(key)
        return raw ? JSON.parse(raw) : fallback
    } catch {
        return fallback
    }
}

function writeJsonStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value))
    } catch {
        // Ignore storage failures and keep in-memory state.
    }
}

function toEpoch(value) {
    const timestamp = new Date(value || 0).getTime()
    return Number.isNaN(timestamp) ? 0 : timestamp
}

function sortNotifications(items) {
    return [...items].sort((a, b) => toEpoch(b.createdAt) - toEpoch(a.createdAt))
}

export const useSystemStore = defineStore('system', () => {
    // State
    const config = ref({
        system_name: '合同管理系统',
        system_logo: null
    })

    const dictionaries = ref({}) // key: category, value: Array of options
    const remoteNotifications = ref([])
    const notificationScope = ref(getNotificationScope())
    const localNotifications = ref([])
    const readNotificationIds = ref([])
    const deletedNotificationIds = ref([])
    const notifications = ref([])
    const notificationsError = ref('')

    function loadNotificationState(scope = notificationScope.value) {
        localNotifications.value = readJsonStorage(scopedNotificationKey(NOTIFICATION_LOCAL_KEY, scope), [])
        readNotificationIds.value = readJsonStorage(scopedNotificationKey(NOTIFICATION_READ_KEY, scope), [])
        deletedNotificationIds.value = readJsonStorage(scopedNotificationKey(NOTIFICATION_DELETED_KEY, scope), [])
    }

    function ensureNotificationScope() {
        const scope = getNotificationScope()
        if (scope === notificationScope.value) {
            return
        }

        notificationScope.value = scope
        remoteNotifications.value = []
        notificationsError.value = ''
        loadNotificationState(scope)
        rebuildNotifications()
    }

    function rebuildNotifications() {
        const deletedSet = new Set(deletedNotificationIds.value)
        const readSet = new Set(readNotificationIds.value)
        const merged = [...localNotifications.value, ...remoteNotifications.value]
        const deduped = merged.filter((item, index) =>
            index === merged.findIndex(candidate => candidate.id === item.id)
        )

        notifications.value = sortNotifications(
            deduped
                .filter(item => !deletedSet.has(item.id))
                .map(item => ({
                    ...item,
                    unread: item.unread !== false && !readSet.has(item.id)
                }))
        )
    }

    function persistNotificationState() {
        writeJsonStorage(scopedNotificationKey(NOTIFICATION_LOCAL_KEY, notificationScope.value), localNotifications.value)
        writeJsonStorage(scopedNotificationKey(NOTIFICATION_READ_KEY, notificationScope.value), readNotificationIds.value)
        writeJsonStorage(scopedNotificationKey(NOTIFICATION_DELETED_KEY, notificationScope.value), deletedNotificationIds.value)
    }

    function resetNotificationState() {
        notificationScope.value = getNotificationScope()
        remoteNotifications.value = []
        notificationsError.value = ''
        loadNotificationState(notificationScope.value)
        rebuildNotifications()
    }

    // Actions
    async function fetchConfig() {
        try {
            const res = await request.get('/system/config')
            config.value = res
            // If logo logic is split, fetch logo too
            if (!config.value.system_logo) {
                const logoRes = await request.get('/system/logo')
                config.value.system_logo = logoRes.path
            }
        } catch (e) {
            console.error('Failed to fetch system config', e)
        }
    }

    async function updateConfig(newConfig) {
        try {
            const res = await request.post('/system/config', newConfig)
            await fetchConfig()
            return res
        } catch (e) {
            throw e
        }
    }

    async function fetchOptions(category) {
        // Return from cache if exists
        // if (dictionaries.value[category]) return dictionaries.value[category]

        try {
            const res = await request.get('/system/options', { params: { category } })
            dictionaries.value[category] = res
            return res
        } catch (e) {
            console.error(`Failed to fetch options for ${category}`, e)
            return []
        }
    }

    async function fetchAllOptions() {
        try {
            const res = await request.get('/system/options')
            // Group by category
            const grouped = {}
            res.forEach(opt => {
                if (!grouped[opt.category]) grouped[opt.category] = []
                grouped[opt.category].push(opt)
            })
            dictionaries.value = grouped
        } catch (e) {
            console.error('Failed to fetch all options', e)
        }
    }

    // CRUD for options (Admin)
    async function addOption(option) {
        await request.post('/system/options', option)
        await fetchOptions(option.category) // Refresh
    }

    async function updateOption(id, data, category) {
        await request.put(`/system/options/${id}`, data)
        if (category) await fetchOptions(category)
    }

    async function deleteOption(id, category) {
        await request.delete(`/system/options/${id}`)
        if (category) await fetchOptions(category)
    }

    function getOptions(category) {
        return dictionaries.value[category] || []
    }

    async function fetchNotifications() {
        ensureNotificationScope()
        notificationsError.value = ''
        try {
            remoteNotifications.value = await fetchNotificationsApi()
            rebuildNotifications()
            return notifications.value
        } catch (error) {
            notificationsError.value = error?.message || '通知加载失败'
            remoteNotifications.value = []
            rebuildNotifications()
            throw error
        }
    }

    function pushNotification(notification) {
        ensureNotificationScope()
        const normalized = {
            id: notification.id || `local-${Date.now()}`,
            type: notification.type || 'general',
            title: notification.title || '系统通知',
            subtitle: notification.subtitle || '系统通知',
            content: notification.content || '',
            relatedGroups: notification.relatedGroups || [],
            createdAt: notification.createdAt || new Date().toISOString(),
            unread: notification.unread !== false
        }

        localNotifications.value = [
            normalized,
            ...localNotifications.value.filter(item => item.id !== normalized.id)
        ]
        deletedNotificationIds.value = deletedNotificationIds.value.filter(id => id !== normalized.id)
        readNotificationIds.value = normalized.unread
            ? readNotificationIds.value.filter(id => id !== normalized.id)
            : Array.from(new Set([...readNotificationIds.value, normalized.id]))
        persistNotificationState()
        rebuildNotifications()
        return normalized
    }

    function markNotificationRead(notificationId) {
        ensureNotificationScope()
        if (!readNotificationIds.value.includes(notificationId)) {
            readNotificationIds.value = [...readNotificationIds.value, notificationId]
            persistNotificationState()
            rebuildNotifications()
        }
    }

    function removeNotification(notificationId) {
        ensureNotificationScope()
        if (!deletedNotificationIds.value.includes(notificationId)) {
            deletedNotificationIds.value = [...deletedNotificationIds.value, notificationId]
        }
        localNotifications.value = localNotifications.value.filter(item => item.id !== notificationId)
        persistNotificationState()
        rebuildNotifications()
    }

    loadNotificationState()
    rebuildNotifications()

    return {
        config,
        dictionaries,
        notifications,
        notificationsError,
        pushNotification,
        markNotificationRead,
        removeNotification,
        resetNotificationState,
        fetchConfig,
        updateConfig,
        fetchOptions,
        fetchAllOptions,
        getOptions,
        fetchNotifications,
        addOption,
        updateOption,
        deleteOption
    }
})
