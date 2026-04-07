import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const mobileLayoutSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/mobile/MobileLayout.vue'),
  'utf-8'
)

const contractListMobileSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/mobile/ContractListMobile.vue'),
  'utf-8'
)

const expenseListMobileSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/mobile/ExpenseListMobile.vue'),
  'utf-8'
)

describe('Mobile adaptation', () => {
  it('adapts the mobile shell for narrow phones and dynamic drawer widths', () => {
    expect(mobileLayoutSource).toContain(':style="{ width: drawerWidth, height: \'100%\' }"')
    expect(mobileLayoutSource).toContain('@media (max-width: 480px)')
    expect(mobileLayoutSource).toContain('border-radius: 0;')
    expect(mobileLayoutSource).toContain('padding: 0;')
  })

  it('reflows mobile contract cards into a denser tablet grid while preserving phone stacking', () => {
    expect(contractListMobileSource).toContain('@media (min-width: 768px)')
    expect(contractListMobileSource).toContain('grid-template-columns: repeat(2, minmax(0, 1fr));')
  })

  it('reflows mobile expense cards into a denser tablet grid while preserving phone stacking', () => {
    expect(expenseListMobileSource).toContain('@media (min-width: 768px)')
    expect(expenseListMobileSource).toContain('grid-template-columns: repeat(2, minmax(0, 1fr));')
  })
})
