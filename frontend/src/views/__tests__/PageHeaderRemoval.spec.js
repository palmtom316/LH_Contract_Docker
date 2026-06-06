import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const viewsRoot = path.resolve(__dirname, '..')

const targets = [
  { label: 'Dashboard', file: 'Dashboard.vue' },
  { label: 'Report dashboard', file: 'reports/ReportDashboard.vue' },
  { label: 'Expense list', file: 'expenses/ExpenseList.vue' },
  { label: 'System management', file: 'system/SystemManagement.vue' },
  { label: 'System settings', file: 'system/SystemSettings.vue' },
  { label: 'Upstream list', file: 'contracts/UpstreamList.vue' },
  { label: 'Downstream list', file: 'contracts/DownstreamList.vue' },
  { label: 'Management list', file: 'contracts/ManagementList.vue' },
  { label: 'Upstream detail', file: 'contracts/UpstreamDetail.vue' },
  { label: 'Downstream detail', file: 'contracts/DownstreamDetail.vue' },
  { label: 'Management detail', file: 'contracts/ManagementDetail.vue' },
  { label: 'Notification center', file: 'notifications/NotificationCenter.vue' },
  { label: 'Audit log', file: 'audit/AuditLog.vue' }
]

const forbiddenPatterns = [/import\s+AppPageHeader\b/, /<AppPageHeader\b/]

describe('Page header removal regression coverage', () => {
  it.each(targets)('removes AppPageHeader from $label source', ({ file }) => {
    const source = fs.readFileSync(path.join(viewsRoot, file), 'utf8')

    forbiddenPatterns.forEach((pattern) => {
      expect(source).not.toMatch(pattern)
    })
  })
})
