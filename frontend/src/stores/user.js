import { defineStore } from 'pinia'
import { login, getInfo, logout, refreshToken as refreshTokenApi } from '@/api/auth'
import { persistSession, clearSessionStorage } from '@/utils/authSession'
import { useSystemStore } from '@/stores/system'

function getStorage() {
    try {
        return typeof globalThis.localStorage === 'undefined' ? null : globalThis.localStorage
    } catch {
        return null
    }
}

function readStorageValue(key, fallback = '') {
    const storage = getStorage()
    if (!storage) return fallback

    try {
        const value = storage.getItem(key)
        return value ?? fallback
    } catch {
        return fallback
    }
}

function readStorageJson(key, fallback, validator = () => true) {
    const storage = getStorage()
    if (!storage) return fallback

    try {
        const raw = storage.getItem(key)
        if (!raw) return fallback
        const parsed = JSON.parse(raw)
        return validator(parsed) ? parsed : fallback
    } catch {
        return fallback
    }
}

export const useUserStore = defineStore('user', {
    state: () => ({
        token: readStorageValue('token', ''),
        refreshToken: '',
        tokenExpiresAt: readStorageValue('token_expires_at', null),
        user: readStorageJson('user_info', {}, (value) => value && typeof value === 'object' && !Array.isArray(value)),
        permissions: readStorageJson('user_permissions', [], Array.isArray)
    }),

    getters: {
        isLoggedIn: (state) => !!state.token,
        isAdmin: (state) => state.user.role === 'ADMIN' || state.user.is_superuser,
        userRole: (state) => state.user.role || '',
        roleDisplay: (state) => state.user.role_display || state.user.role || '',

        // Permission checkers
        hasPermission: (state) => (permission) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes(permission)
        },
        hasAnyPermission: (state) => (permissions) => {
            if (state.user.is_superuser) return true
            return permissions.some(p => state.permissions.includes(p))
        },

        // Dashboard & Reports
        canViewDashboard: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('view_dashboard')
        },
        canViewReports: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('view_reports')
        },
        canDownloadReports: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('download_reports')
        },

        // Upstream Contracts
        canViewUpstreamContracts: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('view_upstream_contracts') ||
                state.permissions.includes('view_upstream_basic_info')
        },
        canManageUpstreamContracts: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('create_upstream_contracts')
        },

        // Downstream Contracts
        canViewDownstreamContracts: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('view_downstream_contracts') ||
                state.permissions.includes('view_downstream_basic_info')
        },
        canManageDownstreamContracts: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('create_downstream_contracts')
        },

        // Management Contracts
        canViewManagementContracts: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('view_management_contracts') ||
                state.permissions.includes('view_management_basic_info')
        },
        canManageManagementContracts: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('create_management_contracts')
        },

        // Financial Records
        canManageReceivables: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('create_receivables')
        },
        canManagePayables: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('create_payables')
        },
        canManageInvoices: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('create_invoices')
        },
        canManagePayments: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('create_payments')
        },
        canManageSettlements: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('create_settlements')
        },

        // Expenses
        canViewExpenses: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('view_expenses')
        },
        canManageExpenses: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('create_expenses')
        },

        // User Management
        canManageUsers: (state) => {
            if (state.user.is_superuser) return true
            return state.permissions.includes('create_users')
        }
    },

    actions: {
        async login(userInfo) {
            try {
                const res = await login(userInfo)
                const { access_token, refresh_token, expires_in, user } = res

                this.token = access_token
                this.refreshToken = refresh_token || ''
                this.user = user
                this.permissions = user.permissions || []

                if (expires_in) {
                    const expiresAt = Date.now() + (expires_in * 1000)
                    this.tokenExpiresAt = expiresAt
                }

                persistSession({
                    accessToken: access_token,
                    refreshToken: refresh_token,
                    expiresIn: expires_in,
                    user
                })

                useSystemStore().resetNotificationState()

                return res
            } catch (error) {
                throw error
            }
        },

        async getUserInfo() {
            try {
                const res = await getInfo()
                this.user = res
                this.permissions = res.permissions || []

                localStorage.setItem('user_info', JSON.stringify(res))
                localStorage.setItem('user_permissions', JSON.stringify(res.permissions || []))
                useSystemStore().resetNotificationState()

                return res
            } catch (error) {
                throw error
            }
        },

        async logout() {
            try {
                await logout()
            } catch (error) {
                throw error
            } finally {
                this.token = ''
                this.refreshToken = ''
                this.tokenExpiresAt = null
                this.user = {}
                this.permissions = []
                clearSessionStorage()
                useSystemStore().resetNotificationState()
            }
        },

        async refreshAccessToken() {
            if (!this.refreshToken) {
                throw new Error('No refresh token available')
            }

            try {
                const res = await refreshTokenApi(this.refreshToken)
                const { access_token, refresh_token, expires_in, user } = res

                this.token = access_token
                this.refreshToken = refresh_token || this.refreshToken
                this.user = user
                this.permissions = user.permissions || []

                if (expires_in) {
                    const expiresAt = Date.now() + (expires_in * 1000)
                    this.tokenExpiresAt = expiresAt
                }

                persistSession({
                    accessToken: access_token,
                    refreshToken: refresh_token || this.refreshToken,
                    expiresIn: expires_in,
                    user
                })

                useSystemStore().resetNotificationState()

                return res
            } catch (error) {
                await this.logout()
                throw error
            }
        },

        // Check if token needs refresh (within 5 minutes of expiry)
        shouldRefreshToken() {
            if (!this.tokenExpiresAt) return false
            const fiveMinutes = 5 * 60 * 1000
            return (this.tokenExpiresAt - Date.now()) < fiveMinutes
        },

        // Check specific permission
        checkPermission(permission) {
            if (this.user.is_superuser) return true
            return this.permissions.includes(permission)
        },

        // Check any of the permissions
        checkAnyPermission(permissions) {
            if (this.user.is_superuser) return true
            return permissions.some(p => this.permissions.includes(p))
        }
    }
})
