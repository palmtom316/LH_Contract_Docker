<template>
  <div class="system-management-shell">
    <AppWorkspacePanel panel-class="system-management-panel">
    <AppSectionCard>
      <template #header>系统工作台</template>
      <el-tabs v-model="activeTab" class="app-tabs--line system-management__tabs">
        <el-tab-pane label="用户管理" name="users">
          <UserManagement />
        </el-tab-pane>

        <el-tab-pane label="系统配置" name="settings">
          <SystemSettings />
        </el-tab-pane>

        <el-tab-pane label="系统运维" name="operations">
          <section class="operation-grid">
            <AppSectionCard class="operation-panel">
              <template #header>
                <div class="operation-panel__title">
                  <el-icon><Upload /></el-icon>
                  <span>系统备份</span>
                </div>
              </template>
              <el-button type="primary" :loading="backupLoading" @click="handleSystemBackup">立即备份</el-button>
            </AppSectionCard>

            <AppSectionCard class="operation-panel">
              <template #header>
                <div class="operation-panel__title">
                  <el-icon><Download /></el-icon>
                  <span>系统恢复</span>
                </div>
              </template>
              <el-upload
                action="#"
                :auto-upload="false"
                :on-change="handleRestoreUpload"
                :show-file-list="false"
                accept=".zip,.tar.gz"
                class="operation-panel__upload"
              >
                <el-button>选择备份文件</el-button>
              </el-upload>
            </AppSectionCard>

            <AppSectionCard class="operation-panel">
              <template #header>
                <div class="operation-panel__title">
                  <el-icon><Coin /></el-icon>
                  <span>数据库备份</span>
                </div>
              </template>
              <el-button type="primary" :loading="dbBackupLoading" @click="handleDbBackup">导出数据库</el-button>
            </AppSectionCard>

            <AppSectionCard class="operation-panel">
              <template #header>
                <div class="operation-panel__title">
                  <el-icon><CircleCheck /></el-icon>
                  <span>数据库恢复</span>
                </div>
              </template>
              <el-upload
                action="#"
                :auto-upload="false"
                :on-change="handleDbRestoreUpload"
                :show-file-list="false"
                accept=".sql,.dump"
                class="operation-panel__upload"
              >
                <el-button>选择数据库文件</el-button>
              </el-upload>
            </AppSectionCard>

            <AppSectionCard class="operation-panel operation-panel--danger">
              <template #header>
                <div class="operation-panel__title">
                  <el-icon><RefreshLeft /></el-icon>
                  <span>系统重置</span>
                </div>
              </template>
              <el-button type="danger" :loading="resetLoading" @click="handleSystemReset">重置系统</el-button>
            </AppSectionCard>

            <AppSectionCard class="operation-panel operation-panel--warning">
              <template #header>
                <div class="operation-panel__title">
                  <el-icon><Delete /></el-icon>
                  <span>审计日志清理</span>
                </div>
              </template>
              <div class="operation-panel__field">
                <el-date-picker
                  v-model="auditDeleteDate"
                  type="date"
                  placeholder="选择日期"
                  value-format="YYYY-MM-DD"
                />
                <el-button
                  type="warning"
                  :loading="auditDeleteLoading"
                  :disabled="!auditDeleteDate"
                  @click="handleAuditDelete"
                >
                  删除日志
                </el-button>
              </div>
            </AppSectionCard>
          </section>
        </el-tab-pane>
      </el-tabs>
    </AppSectionCard>
    </AppWorkspacePanel>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Download, Coin, CircleCheck, RefreshLeft, Delete } from '@element-plus/icons-vue'
import AppSectionCard from '@/components/ui/AppSectionCard.vue'
import AppWorkspacePanel from '@/components/ui/AppWorkspacePanel.vue'
import UserManagement from '@/views/users/UserManagement.vue'
import SystemSettings from './SystemSettings.vue'
import { deleteAuditLogsBefore } from '@/api/audit'
import { backupSystem, backupDatabase, resetSystem } from '@/api/system'

const activeTab = ref('users')
const backupLoading = ref(false)
const dbBackupLoading = ref(false)
const resetLoading = ref(false)
const auditDeleteLoading = ref(false)
const auditDeleteDate = ref('')

const downloadBlob = (blob, filename) => {
  if (!blob) return
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

const handleSystemBackup = async () => {
  try {
    await ElMessageBox.confirm('确定要备份系统吗？此操作可能需要几分钟。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    backupLoading.value = true
    const blob = await backupSystem()
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    downloadBlob(blob, `lh_system_backup_${timestamp}.zip`)
    ElMessage.success('系统备份下载成功')
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
      const msg = e.response?.data?.detail || e.message || '系统备份失败'
      if (!document.querySelector('.el-message')) {
        ElMessage.error(msg)
      }
    }
  } finally {
    backupLoading.value = false
  }
}

const handleRestoreUpload = async () => {
  try {
    await ElMessageBox.confirm('确定要从备份文件恢复系统吗？此操作将覆盖当前数据！', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error'
    })
    ElMessage.warning('当前版本尚未接入系统恢复接口，请联系后端完成恢复能力后再执行。')
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
      ElMessage.error('系统恢复失败')
    }
  }
}

const handleDbBackup = async () => {
  try {
    await ElMessageBox.confirm('确定要备份数据库吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    dbBackupLoading.value = true
    const blob = await backupDatabase()
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    downloadBlob(blob, `lh_contract_db_${timestamp}.sql`)
    ElMessage.success('数据库备份下载成功')
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
      const msg = e.response?.data?.detail || e.message || '数据库备份失败'
      if (!document.querySelector('.el-message')) {
        ElMessage.error(msg)
      }
    }
  } finally {
    dbBackupLoading.value = false
  }
}

const handleDbRestoreUpload = async () => {
  try {
    await ElMessageBox.confirm('确定要从备份文件恢复数据库吗？此操作将覆盖当前数据！', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error'
    })
    ElMessage.warning('当前版本尚未接入数据库恢复接口，请确认后端实现后再执行。')
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
      ElMessage.error('数据库恢复失败')
    }
  }
}

const handleSystemReset = async () => {
  try {
    await ElMessageBox.confirm(
      '此操作将清空所有数据，仅保留管理员账户，且不可恢复。请输入 "RESET" 确认操作。',
      '危险操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error',
        inputPattern: /^RESET$/,
        inputPlaceholder: '请输入 RESET',
        inputErrorMessage: '输入错误，请输入 RESET'
      }
    )

    resetLoading.value = true
    await resetSystem('RESET')
    ElMessage.success('系统重置成功，请重新登录')

    setTimeout(() => {
      window.location.href = '/login'
    }, 1500)
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
      ElMessage.error('系统重置失败')
    }
  } finally {
    resetLoading.value = false
  }
}

const handleAuditDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${auditDeleteDate.value} 之前的所有审计日志吗？此操作不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    auditDeleteLoading.value = true
    const res = await deleteAuditLogsBefore(auditDeleteDate.value)
    ElMessage.success(res.message || '审计日志删除成功')
    auditDeleteDate.value = ''
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
      ElMessage.error(e.response?.data?.detail || '审计日志删除失败')
    }
  } finally {
    auditDeleteLoading.value = false
  }
}
</script>

<style scoped lang="scss">
.system-management-shell {
  display: grid;
  gap: var(--space-5);
}

.system-management-panel {
  gap: var(--space-4);
}

.operation-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.operation-panel {
  height: 100%;
}

.operation-panel :deep(.el-card__body) {
  display: grid;
  gap: 16px;
}

.operation-panel--warning {
  border-color: color-mix(in srgb, var(--border-subtle) 60%, var(--status-warning) 40%);
}

.operation-panel--danger {
  border-color: color-mix(in srgb, var(--border-subtle) 55%, var(--status-danger) 45%);
}

.operation-panel__title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
}

.operation-panel__field {
  display: grid;
  gap: 12px;
}

.operation-panel__upload,
.operation-panel__upload :deep(.el-upload) {
  width: 100%;
}

.operation-panel__upload :deep(.el-button),
.operation-panel__field :deep(.el-button) {
  width: 100%;
}

@media (max-width: 900px) {
  .operation-grid {
    grid-template-columns: 1fr;
  }
}
</style>
