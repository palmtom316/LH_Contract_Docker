import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import InvoiceImportWorkbench from '../InvoiceImportWorkbench.vue'

const { deleteBatchMock, confirmMock } = vi.hoisted(() => ({
  deleteBatchMock: vi.fn().mockResolvedValue({}),
  confirmMock: vi.fn().mockResolvedValue('confirm'),
}))

vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    ElMessageBox: { confirm: confirmMock },
  }
})

vi.mock('@/api/invoiceImport', () => ({
  listBatches: vi.fn().mockResolvedValue([
    {
      id: 1,
      batch_code: 'INVIMP-202607080001',
      original_filename: 'batch.zip',
      status: 'completed',
      total_items: 2,
      parsed_items: 2,
      duplicate_items: 0,
      error_items: 0,
      confirmed_items: 0,
    },
  ]),
  listBatchItems: vi.fn().mockResolvedValue([]),
  createAllocation: vi.fn().mockResolvedValue({}),
  confirmItem: vi.fn().mockResolvedValue({}),
  deleteBatch: deleteBatchMock,
  uploadBatch: vi.fn().mockResolvedValue({}),
}))

vi.mock('@/api/contractUpstream', () => ({
  getContracts: vi.fn().mockResolvedValue({ items: [] }),
  getContract: vi.fn().mockResolvedValue({ id: 1, serial_number: 1, contract_name: '上游候选合同', contract_code: 'UP-001' }),
}))

vi.mock('@/api/contractDownstream', () => ({
  getContracts: vi.fn().mockResolvedValue({ items: [] }),
  getContract: vi.fn().mockResolvedValue({ id: 1, serial_number: 1, contract_name: '下游候选合同', contract_code: 'DOWN-001' }),
}))

describe('InvoiceImportWorkbench', () => {
  it('renders batch list title and loaded batch code', async () => {
    const wrapper = mount(InvoiceImportWorkbench)
    await Promise.resolve()
    await Promise.resolve()

    expect(wrapper.text()).toContain('电子发票导入')
    expect(wrapper.text()).toContain('INVIMP-202607080001')
    expect(wrapper.text()).toContain('上传压缩包')
    expect(wrapper.text()).toContain('刷新')
  })

  it('deletes an import batch from the operation column after confirmation', async () => {
    const wrapper = mount(InvoiceImportWorkbench)
    await Promise.resolve()
    await Promise.resolve()

    const deleteButton = wrapper.findAll('button').find((button) => button.text() === '删除')
    await deleteButton.trigger('click')
    await Promise.resolve()

    expect(confirmMock).toHaveBeenCalled()
    expect(deleteBatchMock).toHaveBeenCalledWith(1)
  })
})

it('shows item states after selecting a batch', async () => {
  const api = await import('@/api/invoiceImport')
  api.listBatchItems.mockResolvedValueOnce([
    {
      id: 10,
      invoice_number: 'INV-001',
      seller_name: '我方公司',
      buyer_name: '客户A',
      total_amount: '106.00',
      direction: 'upstream',
      parse_status: 'parsed',
      match_status: 'multiple_candidates',
      confirmation_status: 'draft',
      allocations: [],
      candidates: [],
    },
  ])

  const wrapper = mount(InvoiceImportWorkbench)
  await Promise.resolve()
  await Promise.resolve()
  const viewButton = wrapper.findAll('button').find((button) => button.text() === '查看')
  await viewButton.trigger('click')
  await Promise.resolve()

  expect(wrapper.text()).toContain('INV-001')
  expect(wrapper.text()).toContain('upstream')
})
