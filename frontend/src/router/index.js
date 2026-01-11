import { createRouter, createWebHistory } from 'vue-router'

// Mobile route to PC route mapping (for auto-redirect)
const mobileToPC = {
    '/m/contracts': '/contracts/upstream',
    '/m/reports': '/reports',
    '/m/profile': '/system'
}

// PC route to mobile route mapping
const pcToMobile = {
    '/contracts/upstream': '/m/contracts',
    '/contracts/downstream': '/m/contracts',
    '/contracts/management': '/m/contracts',
    '/reports': '/m/reports',
    '/system': '/m/profile'
}

const routes = [
    // PC Routes (Element Plus)
    {
        path: '/',
        name: 'Layout',
        component: () => import('@/views/Layout.vue'),
        meta: { platform: 'pc' },
        children: [
            {
                path: '',
                name: 'Dashboard',
                component: () => import('@/views/Dashboard.vue'),
                meta: { title: '首页', icon: 'HomeFilled' }
            },
            {
                path: 'contracts/upstream',
                name: 'UpstreamList',
                component: () => import('../views/contracts/UpstreamList.vue'),
                meta: { title: '上游合同列表' }
            },
            {
                path: 'contracts/upstream/:id',
                name: 'UpstreamDetail',
                component: () => import('../views/contracts/UpstreamDetail.vue'),
                meta: { title: '上游合同详情', hidden: true }
            },
            {
                path: 'contracts/management',
                name: 'ManagementList',
                component: () => import('@/views/contracts/ManagementList.vue'),
                meta: { title: '管理合同', icon: 'FolderChecked' }
            },
            {
                path: 'contracts/management/:id',
                name: 'ManagementDetail',
                component: () => import('@/views/contracts/ManagementDetail.vue'),
                meta: { title: '管理合同详情', hidden: true }
            },
            {
                path: 'contracts/downstream',
                name: 'DownstreamContracts',
                component: () => import('@/views/contracts/DownstreamList.vue'),
                meta: { title: '下游合同', icon: 'DocumentCopy' }
            },
            {
                path: 'contracts/downstream/:id',
                name: 'DownstreamDetail',
                component: () => import('@/views/contracts/DownstreamDetail.vue'),
                meta: { title: '下游合同详情', hidden: true }
            },
            {
                path: 'expenses',
                name: 'Expenses',
                component: () => import('@/views/expenses/ExpenseList.vue'),
                meta: { title: '无合同费用', icon: 'Money' }
            },
            {
                path: 'reports',
                name: 'Reports',
                component: () => import('@/views/reports/ReportDashboard.vue'),
                meta: { title: '报表统计', icon: 'DataAnalysis' }
            },
            {
                path: 'system',
                name: 'SystemManagement',
                component: () => import('@/views/system/SystemManagement.vue'),
                meta: { title: '系统管理', icon: 'Setting' }
            },
            {
                path: 'audit',
                name: 'AuditLog',
                component: () => import('@/views/audit/AuditLog.vue'),
                meta: { title: '审计日志', icon: 'Document' }
            }
        ]
    },
    // Mobile Routes (Vant UI)
    {
        path: '/m',
        name: 'MobileLayout',
        component: () => import('@/views/mobile/MobileLayout.vue'),
        meta: { platform: 'mobile' },
        children: [
            {
                path: 'contracts',
                name: 'MobileContractList',
                component: () => import('@/views/mobile/ContractListMobile.vue'),
                meta: { title: '合同列表' }
            },
            {
                path: 'reports',
                name: 'MobileReports',
                component: () => import('@/views/reports/ReportDashboard.vue'),
                meta: { title: '报表' }
            },
            {
                path: 'profile',
                name: 'MobileProfile',
                component: () => import('@/views/system/SystemManagement.vue'),
                meta: { title: '我的' }
            }
        ]
    },
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/Login.vue'),
        meta: { title: '登录' }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// Helper: Check if mobile device
const isMobileDevice = () => window.innerWidth < 768

// Navigation guards
router.beforeEach((to, from, next) => {
    // Set page title
    document.title = to.meta.title ? `${to.meta.title} - 蓝海合同管理` : '蓝海合同管理系统'
    const token = localStorage.getItem('token')
    const whiteList = ['/login']

    if (token) {
        if (to.path === '/login') {
            next('/')
        } else {
            // Auto-redirect based on device type
            const isMobile = isMobileDevice()

            // Mobile user accessing PC route -> redirect to mobile
            // Disabled: User wants ability to view PC lists on mobile
            /*
            if (isMobile && !to.path.startsWith('/m') && to.path !== '/' && pcToMobile[to.path]) {
                next(pcToMobile[to.path])
                return
            }
            */

            // PC user accessing mobile route -> redirect to PC
            if (!isMobile && to.path.startsWith('/m') && mobileToPC[to.path]) {
                next(mobileToPC[to.path])
                return
            }

            // Handle root path based on device
            if (to.path === '/') {
                if (isMobile) {
                    next('/m/contracts')
                    return
                }
            }

            next()
        }
    } else {
        if (whiteList.includes(to.path)) {
            next()
        } else {
            next('/login')
        }
    }
})

export default router

