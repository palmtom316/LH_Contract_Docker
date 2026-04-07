import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const viewFiles = [
  'src/views/contracts/UpstreamDetail.vue',
  'src/views/contracts/DownstreamDetail.vue',
  'src/views/contracts/ManagementDetail.vue',
  'src/views/expenses/OrdinaryExpenseList.vue',
  'src/views/expenses/ZeroHourLaborList.vue'
]

describe('Feishu approval cleanup', () => {
  it('removes feishu approval sections from contract and expense pages', () => {
    for (const file of viewFiles) {
      const source = readFileSync(path.resolve(process.cwd(), file), 'utf-8')

      expect(source).not.toContain('飞书审批实例')
      expect(source).not.toContain('审批状态')
      expect(source).not.toContain('审批单')
      expect(source).not.toContain('查看审批单')
    }
  })
})
