
import { defineStore } from 'pinia'
import request from '@/utils/request'
import { ref } from 'vue'
import { fetchNotifications as fetchNotificationsApi } from '@/api/notifications'

export const useSystemStore = defineStore('system', () => {
    // State
    const config = ref({
        system_name: 'Lanhai Contract System',
        system_logo: null
    })

    const dictionaries = ref({}) // key: category, value: Array of options
    const notifications = ref([])
    const notificationsError = ref('')

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
        notificationsError.value = ''
        try {
            notifications.value = await fetchNotificationsApi()
            return notifications.value
        } catch (error) {
            notifications.value = []
            notificationsError.value = error?.message || '通知加载失败'
            throw error
        }
    }

    return {
        config,
        dictionaries,
        notifications,
        notificationsError,
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
