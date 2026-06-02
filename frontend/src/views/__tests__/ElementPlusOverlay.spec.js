import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const mainSource = readFileSync(
  path.resolve(process.cwd(), 'src/main.js'),
  'utf-8'
)

const stylesSource = readFileSync(
  path.resolve(process.cwd(), 'src/styles/index.scss'),
  'utf-8'
)

describe('Element Plus overlay positioning', () => {
  it('loads Element Plus base styles before project overrides', () => {
    const elementPlusIndex = mainSource.indexOf("import 'element-plus/dist/index.css'")
    const projectStylesIndex = mainSource.indexOf("import '@/styles/index.scss'")

    expect(elementPlusIndex).toBeGreaterThan(-1)
    expect(projectStylesIndex).toBeGreaterThan(elementPlusIndex)
  })

  it('keeps confirmation message boxes centered in the viewport', () => {
    expect(stylesSource).toContain('.el-overlay-message-box {')
    expect(stylesSource).toContain('display: flex;')
    expect(stylesSource).toContain('align-items: center;')
    expect(stylesSource).toContain('justify-content: center;')
    expect(stylesSource).toContain('.el-message-box {')
    expect(stylesSource).toContain('max-width: calc(100vw - 32px);')
  })
})
