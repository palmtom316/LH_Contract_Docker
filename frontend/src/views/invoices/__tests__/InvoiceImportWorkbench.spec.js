import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import InvoiceImportWorkbench from '../InvoiceImportWorkbench.vue'

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
}))

describe('InvoiceImportWorkbench', () => {
  it('renders batch list title and loaded batch code', async () => {
    const wrapper = mount(InvoiceImportWorkbench)
    await Promise.resolve()
    await Promise.resolve()

    expect(wrapper.text()).toContain('电子发票导入')
    expect(wrapper.text()).toContain('INVIMP-202607080001')
  })
})
