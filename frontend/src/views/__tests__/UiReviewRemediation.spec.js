import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { getStatusType } from '@/utils/common'

const readSource = (file) => readFileSync(path.resolve(process.cwd(), file), 'utf-8')

const userManagementSource = readSource('src/views/users/UserManagement.vue')
const ordinaryExpenseSource = readSource('src/views/expenses/OrdinaryExpenseList.vue')
const zeroHourSource = readSource('src/views/expenses/ZeroHourLaborList.vue')
const pdfViewerSource = readSource('src/components/PdfViewer.vue')
const globalStylesSource = readSource('src/styles/index.scss')
const statCardSource = readSource('src/components/StatCard.vue')
const sectionCardSource = readSource('src/components/ui/AppSectionCard.vue')
const systemManagementSource = readSource('src/views/system/SystemManagement.vue')
const layoutSource = readSource('src/views/Layout.vue')
const systemSettingsSource = readSource('src/views/system/SystemSettings.vue')

describe('UI review remediation', () => {
  it('uses valid Element Plus tag types for contract statuses and user roles', () => {
    const validElementTagTypes = ['primary', 'success', 'info', 'warning', 'danger']

    expect(validElementTagTypes).toContain(getStatusType('DRAFT'))
    expect(validElementTagTypes).toContain(getStatusType('UNKNOWN_STATUS'))
    expect(userManagementSource).not.toContain("'ENGINEERING': ''")
    expect(userManagementSource).not.toContain("'GENERAL_AFFAIRS': ''")
    expect(userManagementSource).toContain("return typeMap[role] || 'info'")
  })

  it('gives icon-only controls accessible names', () => {
    expect(ordinaryExpenseSource).toContain('aria-label="更多费用操作"')
    expect(zeroHourSource).toContain('aria-label="更多用工操作"')
    expect(pdfViewerSource).toContain('aria-label="缩小 PDF 预览"')
    expect(pdfViewerSource).toContain('aria-label="放大 PDF 预览"')
  })

  it('keeps compact desktop action buttons but expands touch targets on mobile', () => {
    expect(globalStylesSource).toContain('@media (max-width: 767px)')
    expect(globalStylesSource).toContain('.contract-list-action-button.el-button')
    expect(globalStylesSource).toContain('min-height: 44px;')
    expect(globalStylesSource).toContain('height: 44px;')
  })

  it('does not make non-interactive cards look clickable', () => {
    expect(statCardSource).not.toContain('cursor: pointer;')
    expect(statCardSource).not.toContain('&:hover')
    expect(sectionCardSource).not.toContain('.app-section-card:hover')
    expect(sectionCardSource).not.toContain('transform: translateY(-1px);')
  })

  it('keeps system management hierarchy flat and gives logos useful alt text', () => {
    expect(systemManagementSource).not.toContain('<template #header>系统工作台</template>')
    expect(layoutSource).toContain(':alt="displayName"')
    expect(layoutSource).not.toContain('alt="logo"')
    expect(systemSettingsSource).toContain('alt="系统 Logo 预览"')
  })
})
