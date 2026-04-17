import { createRouter, createWebHistory } from 'vue-router'

// Mobile route -> PC route redirect map (PC user lands on /m/* -> bounce to PC).
// Reverse direction is intentionally not enforced: mobile users can still open PC lists.
const mobileToPC = {
    '/m/contracts': '/contracts/upstream',
    '/m/expenses': '/expenses',
    '/m/reports': '/reports',
    '/m/profile': '/system'
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
                path: 'notifications',
                name: 'NotificationCenter',
                component: () => import('@/views/notifications/NotificationCenter.vue'),
                meta: { title: '系统通知' }
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
                path: 'expenses',
                name: 'MobileExpenseList',
                component: () => import('@/views/mobile/ExpenseListMobile.vue'),
                meta: { title: '费用管理' }
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
    document.title = to.meta.title ? `${to.meta.title} - 合同管理系统` : '合同管理系统'
    const token = localStorage.getItem('token')
    const whiteList = ['/login']

    if (token) {
        if (to.path === '/login') {
            next('/')
        } else {
            const isMobile = isMobileDevice()

            // PC user accessing mobile route -> redirect to PC equivalent
            if (!isMobile && to.path.startsWith('/m') && mobileToPC[to.path]) {
                next(mobileToPC[to.path])
                return
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
