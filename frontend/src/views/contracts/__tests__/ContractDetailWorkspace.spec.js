import { shallowMount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import UpstreamDetail from '@/views/contracts/UpstreamDetail.vue'
import ManagementDetail from '@/views/contracts/ManagementDetail.vue'
import DownstreamDetail from '@/views/contracts/DownstreamDetail.vue'

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    useRoute: () => ({
      params: { id: 'contract-1' },
      query: {},
      meta: { title: '合同详情' }
    }),
    useRouter: () => ({ push: vi.fn() })
  }
})

vi.mock('@/api/contractUpstream', () => ({
  getContract: vi.fn().mockResolvedValue({
    contract_name: 'Test Contract',
    status: 'DRAFT',
    contract_amount: 0
  }),
  getReceivables: vi.fn().mockResolvedValue([]),
  getInvoices: vi.fn().mockResolvedValue([]),
  getReceipts: vi.fn().mockResolvedValue([]),
  getSettlements: vi.fn().mockResolvedValue([])
}))

vi.mock('@/api/contractManagement', () => ({
  getContract: vi.fn().mockResolvedValue({
    contract_name: 'Test Management Contract',
    status: 'DRAFT',
    contract_amount: 0
  }),
  getPayables: vi.fn().mockResolvedValue([]),
  getInvoices: vi.fn().mockResolvedValue([]),
  getPayments: vi.fn().mockResolvedValue([]),
  getSettlements: vi.fn().mockResolvedValue([])
}))

vi.mock('@/api/contractDownstream', () => ({
  getContract: vi.fn().mockResolvedValue({
    contract_name: 'Test Downstream Contract',
    status: 'DRAFT',
    contract_amount: 0
  }),
  getPayables: vi.fn().mockResolvedValue([]),
  getInvoices: vi.fn().mockResolvedValue([]),
  getPayments: vi.fn().mockResolvedValue([]),
  getSettlements: vi.fn().mockResolvedValue([])
}))

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    canManageReceivables: false,
    canManageInvoices: false,
    canManagePayments: false,
    canManageSettlements: false
  })
}))

const elementStubNames = [
  'ElIcon',
  'ElTag',
  'ElCol',
  'ElRow',
  'ElDescriptions',
  'ElDescriptionsItem',
  'ElLink',
  'ElButton',
  'ElTabs',
  'ElTabPane',
  'ElForm',
  'ElFormItem',
  'ElInput',
  'ElUpload',
  'ElSelect',
  'ElOption',
  'ElDialog'
]

const elementStubs = elementStubNames.reduce((stubs, name) => {
  stubs[name] = true
  return stubs
}, {})

const mountPage = (component) =>
  shallowMount(component, {
    global: {
      stubs: {
        AppWorkspacePanel: {
          props: ['panelClass'],
          template: '<section class="app-workspace-panel-stub" :class="panelClass"><slot /></section>'
        },
        ...elementStubs,
        ElTable: { template: '<div class="el-table-stub" />' },
        ElTableColumn: { template: '<div class="el-table-column-stub" />' }
      }
    }
  })

describe('Contract detail workspace shell', () => {
  it.each([
    ['UpstreamDetail', UpstreamDetail],
    ['ManagementDetail', ManagementDetail],
    ['DownstreamDetail', DownstreamDetail]
  ])('wraps %s content in the shared detail workspace shell', (_name, component) => {
    const wrapper = mountPage(component)

    expect(wrapper.find('.detail-workspace').exists()).toBe(true)
    expect(wrapper.find('.detail-workspace__hero').exists()).toBe(false)
    expect(wrapper.find('.detail-workspace__sections').exists()).toBe(true)
    expect(wrapper.find('.detail-context').exists()).toBe(true)
    expect(wrapper.find('.detail-context__actions').exists()).toBe(true)
  })
})
