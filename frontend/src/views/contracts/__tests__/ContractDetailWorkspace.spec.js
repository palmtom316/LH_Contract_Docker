import { shallowMount } from '@vue/test-utils'
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
  getInvoices: vi.fn().mockResolvedValue([]),
  getReceipts: vi.fn().mockResolvedValue([]),
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

const mountPage = () =>
  shallowMount(UpstreamDetail, {
    global: {
      stubs: {
        ElIcon: true,
        ElTag: true,
        ElCol: true,
        ElRow: true,
        ElDescriptions: true,
        ElDescriptionsItem: true,
        ElLink: true,
        ElButton: true,
        ElTabs: true,
        ElTabPane: true,
        ElTable: true,
        ElTableColumn: { template: '<div class="el-table-column-stub" />' },
        ElForm: true,
        ElFormItem: true,
        ElInput: true,
        ElUpload: true,
        ElSelect: true,
        ElOption: true,
        ElDialog: true
      }
    }
  })

describe('Contract detail workspace shell', () => {
  it('wraps contract detail content in the new detail workspace shell', () => {
    const wrapper = mountPage()

    expect(wrapper.find('.detail-workspace-shell').exists()).toBe(true)
  })
})
