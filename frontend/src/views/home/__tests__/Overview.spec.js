import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const overviewSource = readFileSync(
  path.resolve(process.cwd(), 'src/views/home/Overview.vue'),
  'utf-8'
)

describe('Overview metric cards', () => {
  it('does not include eyebrow copy in the top four summary cards', () => {
    expect(overviewSource).toContain("eyebrow: ''")
    expect(overviewSource).not.toContain("eyebrow: '年度经营'")
    expect(overviewSource).toContain(":eyebrow=\"item.eyebrow\"")
  })
})
