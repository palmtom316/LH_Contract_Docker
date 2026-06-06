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
  it('renders eyebrow, description, and meta when those props are provided', () => {
    const wrapper = mount(AppPageHeader, {
      props: {
        eyebrow: '财务工作台',
        title: '系统设置',
        description: '统一管理系统参数与提醒规则',
        meta: '最近同步于 5 分钟前'
      }
    })

    expect(wrapper.text()).toContain('财务工作台')
    expect(wrapper.text()).toContain('统一管理系统参数与提醒规则')
    expect(wrapper.text()).toContain('最近同步于 5 分钟前')
  })

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
    expect(wrapper.find('.app-page-header__copy').text()).toContain('Manage upstream contract records.')
    expect(wrapper.find('.app-page-header__side').text()).toContain('12 active contracts')
  })

  it('keeps the page header flat while workspace panels remain shared surface containers', () => {
    expect(appPageHeaderSource).toContain('border-b border-border/80 pb-4')
    expect(appPageHeaderSource).toContain('class="app-page-header__eyebrow"')
    expect(appPageHeaderSource).toContain('class="app-page-header__description"')
    expect(appPageHeaderSource).toContain('class="app-page-header__meta"')
    expect(appPageHeaderSource).not.toContain('padding: var(--panel-padding);')
    expect(appWorkspacePanelSource).toContain('gap: 18px;')
    expect(appWorkspacePanelSource).toContain('border-radius: var(--workspace-panel-radius);')
    expect(appWorkspacePanelSource).toContain('background: var(--workspace-panel-background);')
  })
})
