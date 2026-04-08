import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const upstreamSource = readFileSync(path.resolve(process.cwd(), 'src/views/contracts/UpstreamList.vue'), 'utf-8')
const downstreamSource = readFileSync(path.resolve(process.cwd(), 'src/views/contracts/DownstreamList.vue'), 'utf-8')
const managementSource = readFileSync(path.resolve(process.cwd(), 'src/views/contracts/ManagementList.vue'), 'utf-8')

describe('contract desktop tables', () => {
  it('applies the shared dense table class to all three contract lists', () => {
    expect(upstreamSource).toContain('contract-table--dense')
    expect(downstreamSource).toContain('contract-table--dense')
    expect(managementSource).toContain('contract-table--dense')
  })

  it('uses shared wrapping hooks instead of inline white-space style objects', () => {
    expect(upstreamSource).toContain('contract-cell--wrap')
    expect(downstreamSource).toContain('contract-cell--wrap')
    expect(managementSource).toContain('contract-cell--wrap')
    expect(upstreamSource).not.toContain("whiteSpace: 'normal'")
    expect(downstreamSource).not.toContain("whiteSpace: 'normal'")
    expect(managementSource).not.toContain("whiteSpace: 'normal'")
  })
})
