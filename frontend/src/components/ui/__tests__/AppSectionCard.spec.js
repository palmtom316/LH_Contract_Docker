import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import AppSectionCard from '@/components/ui/AppSectionCard.vue'

const sectionCardSource = readFileSync(
  path.resolve(process.cwd(), 'src/components/ui/AppSectionCard.vue'),
  'utf-8'
)

describe('AppSectionCard', () => {
  it('renders section cards with shared surface framing and slot-based header actions', () => {
    const wrapper = mount(AppSectionCard, {
      slots: {
        header: '<span>合同列表</span>',
        actions: '<button>导出</button>',
        default: '<div class="body">content</div>'
      }
    })

    expect(wrapper.find('.app-section-card').exists()).toBe(true)
    expect(wrapper.find('.app-section-card__header').exists()).toBe(true)
    expect(wrapper.find('.body').exists()).toBe(true)
    expect(sectionCardSource).toContain('background: var(--surface-panel);')
    expect(sectionCardSource).toContain('padding: 18px;')
    expect(sectionCardSource).toContain('border-radius: calc(var(--radius) + 2px);')
    expect(sectionCardSource).toContain('transform 180ms ease')
    expect(sectionCardSource).not.toContain('::before')
  })
})
