import { defineStore } from 'pinia'
import { login, getInfo, logout } from '@/api/auth'

export const useUserStore = defineStore('user', {
    state: () => ({
        token: localStorage.getItem('token') || '',
        user: JSON.parse(localStorage.getItem('user_info') || '{}'),
        roles: []
    }),

    getters: {
        isLoggedIn: (state) => !!state.token,
        isAdmin: (state) => state.user.role === 'admin'
    },

    actions: {
        async login(userInfo) {
            try {
                const res = await login(userInfo)
                const { access_token, user } = res

                this.token = access_token
                this.user = user
                localStorage.setItem('token', access_token)
                localStorage.setItem('user_info', JSON.stringify(user))

                return res
            } catch (error) {
                throw error
            }
        },

        async getUserInfo() {
            try {
                const res = await getInfo()
                this.user = res
                localStorage.setItem('user_info', JSON.stringify(res))
                return res
            } catch (error) {
                throw error
            }
        },

        async logout() {
            try {
                await logout()
                this.token = ''
                this.user = {}
                this.roles = []
                localStorage.removeItem('token')
                localStorage.removeItem('user_info')
            } catch (error) {
                throw error
            }
        }
    }
})
