import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const appPageHeaderSource = readFileSync(
  path.resolve(process.cwd(), 'src/components/ui/AppPageHeader.vue'),
  'utf-8'
)

const appWorkspacePanelSource = readFileSync(
  path.resolve(process.cwd(), 'src/components/ui/AppWorkspacePanel.vue'),
  'utf-8'
)

describe('AppPageHeader', () => {
  it('renders the title even when no actions slot is provided', () => {
    const wrapper = mount(AppPageHeader, {
      props: {
        title: '系统设置'
      }
    })

    expect(wrapper.find('.app-page-header').exists()).toBe(true)
    expect(wrapper.text()).toContain('系统设置')
    expect(wrapper.find('.app-page-header__side').exists()).toBe(false)
  })

  it('renders a compact title row with only actions in the side wrapper', () => {
    const wrapper = mount(AppPageHeader, {
      props: {
        eyebrow: 'Contracts',
        title: 'Upstream Contracts',
        description: 'Manage upstream contract records.',
        meta: '12 active contracts'
      },
      slots: {
        actions: '<button type="button" class="header-action">New Contract</button>'
      }
    })

    expect(wrapper.find('.app-page-header').exists()).toBe(true)
    expect(wrapper.text()).toContain('Upstream Contracts')
    expect(wrapper.find('.app-page-header__side').exists()).toBe(true)
    expect(wrapper.find('.app-page-header__actions').text()).toContain('New Contract')
    expect(wrapper.find('.app-page-header__copy').text()).not.toContain('Manage upstream contract records.')
    expect(wrapper.find('.app-page-header__side').text()).not.toContain('12 active contracts')
  })

  it('keeps the page header flat while workspace panels remain elevated containers', () => {
    expect(appPageHeaderSource).toContain('border-b border-border pb-3')
    expect(appPageHeaderSource).not.toContain('padding: var(--panel-padding);')
    expect(appWorkspacePanelSource).toContain('gap: 16px;')
    expect(appWorkspacePanelSource).toContain('border-radius: var(--workspace-panel-radius);')
    expect(appWorkspacePanelSource).toContain('background: var(--surface-panel-elevated);')
  })
})
