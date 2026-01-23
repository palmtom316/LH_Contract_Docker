import { defineStore } from 'pinia'
import { login, getInfo, logout, refreshToken as refreshTokenApi } from '@/api/auth'

export const useUserStore = defineStore('user', {
    state: () => ({
        token: localStorage.getItem('token') || '',
        refreshToken: localStorage.getItem('refresh_token') || '',
        tokenExpiresAt: localStorage.getItem('token_expires_at') || null,
        user: JSON.parse(localStorage.getItem('user_info') || '{}'),
        permissions: JSON.parse(localStorage.getItem('user_permissions') || '[]')
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

                // Calculate token expiration time
                if (expires_in) {
                    const expiresAt = Date.now() + (expires_in * 1000)
                    this.tokenExpiresAt = expiresAt
                    localStorage.setItem('token_expires_at', expiresAt.toString())
                }

                localStorage.setItem('token', access_token)
                if (refresh_token) {
                    localStorage.setItem('refresh_token', refresh_token)
                }
                localStorage.setItem('user_info', JSON.stringify(user))
                localStorage.setItem('user_permissions', JSON.stringify(user.permissions || []))

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

                return res
            } catch (error) {
                throw error
            }
        },

        async logout() {
            try {
                await logout()
                this.token = ''
                this.refreshToken = ''
                this.tokenExpiresAt = null
                this.user = {}
                this.permissions = []
                localStorage.removeItem('token')
                localStorage.removeItem('refresh_token')
                localStorage.removeItem('token_expires_at')
                localStorage.removeItem('user_info')
                localStorage.removeItem('user_permissions')
            } catch (error) {
                throw error
            }
        },

        async refreshAccessToken() {
            if (!this.refreshToken) {
                throw new Error('No refresh token available')
            }

            try {
                const res = await refreshTokenApi(this.refreshToken)
                const { access_token, expires_in, user } = res

                this.token = access_token
                this.user = user
                this.permissions = user.permissions || []

                if (expires_in) {
                    const expiresAt = Date.now() + (expires_in * 1000)
                    this.tokenExpiresAt = expiresAt
                    localStorage.setItem('token_expires_at', expiresAt.toString())
                }

                localStorage.setItem('token', access_token)
                localStorage.setItem('user_info', JSON.stringify(user))
                localStorage.setItem('user_permissions', JSON.stringify(user.permissions || []))

                return res
            } catch (error) {
                // If refresh fails, logout the user
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
