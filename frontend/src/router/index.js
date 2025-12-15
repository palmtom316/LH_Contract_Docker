import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    {
        path: '/',
        name: 'Layout',
        component: () => import('@/views/Layout.vue'),
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
                path: 'users',
                name: 'UserManagement',
                component: () => import('@/views/users/UserManagement.vue'),
                meta: { title: '用户管理', icon: 'User' }
            },
            {
                path: 'audit',
                name: 'AuditLog',
                component: () => import('@/views/audit/AuditLog.vue'),
                meta: { title: '审计日志', icon: 'Document' }
            },
            {
                path: 'test-api',
                name: 'TestAPI',
                component: () => import('@/views/TestAPI.vue'),
                meta: { title: 'API测试', hidden: true }
            },
            {
                path: 'simple-test',
                name: 'SimpleTest',
                component: () => import('@/views/SimpleTest.vue'),
                meta: { title: '简单测试', hidden: true }
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
