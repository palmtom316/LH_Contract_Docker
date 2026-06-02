import { describe, expect, it } from 'vitest'
import { readdirSync, readFileSync } from 'node:fs'
import path from 'node:path'

const mainSource = readFileSync(
  path.resolve(process.cwd(), 'src/main.js'),
  'utf-8'
)

const stylesSource = readFileSync(
  path.resolve(process.cwd(), 'src/styles/index.scss'),
  'utf-8'
)

function collectVueFiles(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const entryPath = path.join(dir, entry.name)
    if (entry.isDirectory()) return collectVueFiles(entryPath)
    return entry.name.endsWith('.vue') ? [entryPath] : []
  })
}

const dialogFiles = [
  ...collectVueFiles(path.resolve(process.cwd(), 'src/components')),
  ...collectVueFiles(path.resolve(process.cwd(), 'src/views'))
]

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

  it('teleports dialogs to the document body so overlays are not clipped by workspace panels', () => {
    const dialogsWithoutAppendToBody = []

    for (const file of dialogFiles) {
      const source = readFileSync(file, 'utf-8')
      const dialogTags = source.match(/<el-dialog\b[\s\S]*?>/g) || []

      for (const tag of dialogTags) {
        if (!tag.includes('append-to-body')) {
          dialogsWithoutAppendToBody.push(path.relative(process.cwd(), file))
        }
      }
    }

    expect(dialogsWithoutAppendToBody).toEqual([])
  })
})
