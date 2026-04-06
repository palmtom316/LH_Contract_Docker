import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import UpstreamDetail from '@/views/contracts/UpstreamDetail.vue'

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
  createReceivable: vi.fn(),
  updateReceivable: vi.fn(),
  deleteReceivable: vi.fn(),
  getInvoices: vi.fn().mockResolvedValue([]),
  createInvoice: vi.fn(),
  updateInvoice: vi.fn(),
  deleteInvoice: vi.fn(),
  getReceipts: vi.fn().mockResolvedValue([]),
  createReceipt: vi.fn(),
  updateReceipt: vi.fn(),
  deleteReceipt: vi.fn(),
  getSettlements: vi.fn().mockResolvedValue([]),
  createSettlement: vi.fn(),
  updateSettlement: vi.fn(),
  deleteSettlement: vi.fn(),
  getContractSummary: vi.fn().mockResolvedValue({})
}))

vi.mock('@/api/common', () => ({
  uploadFile: vi.fn()
}))

vi.mock('@/utils/common', () => ({
  getFileUrl: vi.fn(() => ''),
  formatMoney: (value) => String(value),
  getStatusType: () => 'success'
}))

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn() },
  ElMessageBox: { confirm: vi.fn().mockResolvedValue() }
}))

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    canManageReceivables: false,
    canManageInvoices: false,
    canManagePayments: false,
    canManageSettlements: false
  })
}))

vi.mock('@element-plus/icons-vue', () => ({
  Document: { template: '<i />' },
  ArrowLeft: { template: '<i />' },
  Wallet: { template: '<i />' },
  Money: { template: '<i />' },
  Tickets: { template: '<i />' },
  CircleCheck: { template: '<i />' }
}))

const mountPage = () =>
  mount(UpstreamDetail, {
    global: {
      stubs: {
        DictSelect: true,
        SmartDateInput: true,
        FormulaInput: true,
        StatCard: true,
        ElRow: true,
        ElCol: true,
        ElTag: true,
        ElTabs: { template: '<div><slot /></div>' },
        ElTabPane: { template: '<div><slot /></div>' },
        ElDescriptions: { template: '<div><slot /></div>' },
        ElDescriptionsItem: { template: '<div><slot /></div>' },
        ElLink: { template: '<a><slot /></a>' },
        ElButton: { template: '<button type="button"><slot /></button>' },
        ElTable: { template: '<table><slot /></table>' },
        ElTableColumn: { template: '<col />' },
        ElDialog: { template: '<div><slot /></div>' },
        ElForm: { template: '<form><slot /></form>' },
        ElFormItem: { template: '<div><slot /></div>' },
        ElInput: { template: '<input />' },
        ElInputNumber: { template: '<input />' },
        ElUpload: { template: '<div><slot /></div>' },
        ElIcon: { template: '<i><slot /></i>' },
        ElCard: { template: '<div><slot /></div>' },
        ElTooltip: { template: '<div><slot /></div>' },
        ElDivider: { template: '<div />' }
      }
    }
  })

describe('Contract detail workspace shell', () => {
  it('wraps contract detail content in the new detail workspace shell', () => {
    const wrapper = mountPage()

    expect(wrapper.find('.detail-workspace').exists()).toBe(true)
  })
})
