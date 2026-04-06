import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AppFilterBar from '@/components/ui/AppFilterBar.vue'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { compileString } from 'sass'

const appFilterBarSource = readFileSync(
  path.resolve(process.cwd(), 'src/components/ui/AppFilterBar.vue'),
  'utf-8'
)

const styleMatch = appFilterBarSource.match(/<style\b[^>]*lang="scss"[^>]*>([\s\S]*?)<\/style>/)
if (!styleMatch) {
  throw new Error('AppFilterBar styles could not be read')
}

const compiledAppFilterBarStyles = compileString(styleMatch[1]).css

const getBlockContent = (source, startIndex) => {
  let depth = 0
  let i = startIndex
  for (; i < source.length; i += 1) {
    if (source[i] === '{') {
      depth += 1
      break
    }
  }
  if (depth === 0) return ''
  const blockStart = i + 1
  for (i = blockStart; i < source.length; i += 1) {
    if (source[i] === '{') depth += 1
    if (source[i] === '}') depth -= 1
    if (depth === 0) {
      return source.slice(blockStart, i)
    }
  }
  return ''
}

const getMediaBlock = (source, query) => {
  const mediaIndex = source.indexOf(query)
  if (mediaIndex !== -1) return getBlockContent(source, mediaIndex)
  const mediaMatch = source.match(/@media\s*\(max-width:\s*1280px\)/)
  if (!mediaMatch) return ''
  const matchIndex = source.indexOf(mediaMatch[0])
  if (matchIndex === -1) return ''
  return getBlockContent(source, matchIndex)
}

const getSelectorDeclarations = (source, selector) => {
  const selectorIndex = source.indexOf(selector)
  if (selectorIndex === -1) return {}
  const block = getBlockContent(source, selectorIndex + selector.length)
  if (!block) return {}
  return block
    .split(';')
    .map((declaration) => declaration.trim())
    .filter(Boolean)
    .reduce((acc, declaration) => {
      const [property, ...valueParts] = declaration.split(':')
      if (!property || valueParts.length === 0) return acc
      acc[property.trim()] = valueParts.join(':').trim()
      return acc
    }, {})
}

describe('AppFilterBar', () => {
  it('renders inline actions after filter controls', () => {
    const wrapper = mount(AppFilterBar, {
      props: { inlineActions: true },
      slots: {
        default:
          '<div class="filter-control--search">keyword</div><div class="filter-control--time">range</div>',
        actions: '<button>查询</button>'
      }
    })

    expect(wrapper.find('.app-filter-bar__actions--inline').exists()).toBe(true)
  })

  it('keeps controls in order and renders inline actions at the end', () => {
    const wrapper = mount(AppFilterBar, {
      props: { inlineActions: true },
      slots: {
        default:
          [
            '<div class="filter-control--search">keyword</div>',
            '<div class="filter-control--time">range</div>',
            '<div class="filter-control--range-wide">日期</div>',
            '<div class="filter-control--wide">状态</div>'
          ].join(''),
        actions: '<button>查询</button>'
      }
    })

    const items = wrapper.find('.app-filter-bar__main').findAll(':scope > *')
    expect(items[0].classes()).toContain('filter-control--search')
    expect(items[1].classes()).toContain('filter-control--time')
    expect(items[2].classes()).toContain('filter-control--range-wide')
    expect(items[3].classes()).toContain('filter-control--wide')
    const inlineActions = items[4]
    expect(inlineActions.classes()).toContain('app-filter-bar__actions--inline')
    expect(inlineActions.text()).toBe('查询')
  })

  it('keeps medium breakpoint layout compact without reordering inline actions', () => {
    const mediaBlock = getMediaBlock(compiledAppFilterBarStyles, '@media (max-width: 1280px)')
    expect(mediaBlock).not.toBe('')

    const mainGrid = getSelectorDeclarations(mediaBlock, '.app-filter-bar__main')
    expect(mainGrid['grid-template-columns']).toBe('repeat(8, minmax(0, 1fr))')

    const searchRule = getSelectorDeclarations(mediaBlock, '.app-filter-bar__main :deep(.filter-control--search)')
    const timeRule = getSelectorDeclarations(mediaBlock, '.app-filter-bar__main :deep(.filter-control--time)')
    const rangeRule = getSelectorDeclarations(
      mediaBlock,
      '.app-filter-bar__main :deep(.filter-control--range-wide)'
    )
    const actionsRule = getSelectorDeclarations(mediaBlock, '.app-filter-bar__actions--inline')

    expect(searchRule['grid-column']).toBe('span 3')
    expect(timeRule['grid-column']).toBe('span 3')
    expect(rangeRule['grid-column']).toBe('span 4')
    expect(rangeRule['grid-row']).toBeUndefined()
    expect(actionsRule['grid-column']).toBe('span 3')
    expect(actionsRule['grid-row']).toBeUndefined()
  })

  it('uses the dashboard workspace chrome for radius, padding, and grid spacing', () => {
    const wrapper = mount(AppFilterBar, {
      props: { inlineActions: true },
      slots: {
        default: '<div class="filter-control--search">keyword</div>',
        actions: '<button>查询</button>'
      }
    })

    expect(wrapper.find('.app-filter-bar').classes()).toContain('app-filter-bar')

    const shellRule = getSelectorDeclarations(compiledAppFilterBarStyles, '.app-filter-bar')
    const mainGrid = getSelectorDeclarations(compiledAppFilterBarStyles, '.app-filter-bar__main')

    expect(shellRule.padding).toBe('16px')
    expect(shellRule['border-radius']).toBe('16px')
    expect(shellRule['box-shadow']).toBe('none')
    expect(mainGrid.gap).toBe('10px')
  })
})
