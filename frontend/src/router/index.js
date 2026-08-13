import { createRouter, createWebHistory } from 'vue-router'
import { getAccessToken } from '@/utils/authSession'
import { useUserStore } from '@/stores/user'
import { resolveHomePath } from '@/utils/homePath'

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
                path: 'invoice-imports',
                name: 'InvoiceImportWorkbench',
                component: () => import('@/views/invoices/InvoiceImportWorkbench.vue'),
                meta: { title: '发票挂账', icon: 'DocumentAdd' }
            },
            {
                path: 'expenses/zero-hour-labor/:id',
                name: 'ZeroHourLaborDetail',
                component: () => import('@/views/expenses/ZeroHourLaborDetail.vue'),
                meta: { title: '零星用工详情', hidden: true }
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
            },
            {
                path: 'warehouse/overview',
                name: 'WarehouseOverview',
                component: () => import('@/views/warehouse/WarehouseOverview.vue'),
                meta: { title: '库房总览' }
            },
            {
                path: 'warehouse/materials',
                name: 'WarehouseMaterials',
                component: () => import('@/views/warehouse/WarehouseMaterials.vue'),
                meta: { title: '物资档案' }
            },
            {
                path: 'warehouse/warehouses',
                name: 'WarehouseWarehouses',
                component: () => import('@/views/warehouse/WarehouseWarehouses.vue'),
                meta: { title: '库房与货位' }
            },
            {
                path: 'warehouse/projects',
                name: 'WarehouseProjects',
                component: () => import('@/views/warehouse/WarehouseProjects.vue'),
                meta: { title: '项目档案' }
            },
            {
                path: 'warehouse/inventory',
                name: 'WarehouseInventory',
                component: () => import('@/views/warehouse/WarehouseInventory.vue'),
                meta: { title: '库存查询' }
            },
            {
                path: 'warehouse/inbounds',
                name: 'WarehouseInbounds',
                component: () => import('@/views/warehouse/WarehouseDocuments.vue'),
                meta: { title: '入库单', documentType: 'INBOUND' }
            },
            {
                path: 'warehouse/outbounds',
                name: 'WarehouseOutbounds',
                component: () => import('@/views/warehouse/WarehouseDocuments.vue'),
                meta: { title: '出库单', documentType: 'OUTBOUND' }
            },
            {
                path: 'warehouse/transfers',
                name: 'WarehouseTransfers',
                component: () => import('@/views/warehouse/WarehouseDocuments.vue'),
                meta: { title: '调拨单', documentType: 'TRANSFER' }
            },
            {
                path: 'warehouse/counts',
                name: 'WarehouseCounts',
                component: () => import('@/views/warehouse/WarehouseCounts.vue'),
                meta: { title: '盘点' }
            },
            {
                path: 'warehouse/ledger',
                name: 'WarehouseLedger',
                component: () => import('@/views/warehouse/WarehouseLedger.vue'),
                meta: { title: '库存流水' }
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
            },
            {
                path: 'warehouse',
                name: 'MobileWarehouseHome',
                component: () => import('@/views/mobile/warehouse/WarehouseHome.vue'),
                meta: { title: '库房作业' }
            },
            {
                path: 'warehouse/scan',
                name: 'MobileWarehouseScan',
                component: () => import('@/views/mobile/warehouse/WarehouseScan.vue'),
                meta: { title: '扫码' }
            },
            {
                path: 'warehouse/inbound',
                name: 'MobileWarehouseInbound',
                component: () => import('@/views/mobile/warehouse/WarehouseInbound.vue'),
                meta: { title: '入库' }
            },
            {
                path: 'warehouse/outbound',
                name: 'MobileWarehouseOutbound',
                component: () => import('@/views/mobile/warehouse/WarehouseOutbound.vue'),
                meta: { title: '出库' }
            },
            {
                path: 'warehouse/transfer',
                name: 'MobileWarehouseTransfer',
                component: () => import('@/views/mobile/warehouse/WarehouseTransfer.vue'),
                meta: { title: '调拨' }
            },
            {
                path: 'warehouse/count',
                name: 'MobileWarehouseCount',
                component: () => import('@/views/mobile/warehouse/WarehouseCount.vue'),
                meta: { title: '盘点' }
            },
            {
                path: 'warehouse/inventory',
                name: 'MobileWarehouseInventory',
                component: () => import('@/views/mobile/warehouse/WarehouseInventory.vue'),
                meta: { title: '查库存' }
            },
            {
                path: 'warehouse/history',
                name: 'MobileWarehouseHistory',
                component: () => import('@/views/mobile/warehouse/WarehouseHistory.vue'),
                meta: { title: '最近流水' }
            },
            {
                path: 'warehouse/materials/:id',
                name: 'MobileWarehouseMaterial',
                component: () => import('@/views/mobile/warehouse/WarehouseInbound.vue'),
                meta: { title: '物资入库' }
            },
            {
                path: 'warehouse/locations/:id',
                name: 'MobileWarehouseLocation',
                component: () => import('@/views/mobile/warehouse/WarehouseLocation.vue'),
                meta: { title: '货位详情' }
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
    const token = getAccessToken()
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

            if (to.path === '/') {
                const userStore = useUserStore()
                const home = resolveHomePath({
                    role: userStore.userRole,
                    permissions: userStore.permissions,
                    isSuperuser: userStore.user?.is_superuser,
                    isMobile
                })
                if (home !== '/') {
                    next(home)
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
