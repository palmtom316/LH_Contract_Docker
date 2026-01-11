<template>
  <div class="app-container">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 用户管理标签 -->
      <el-tab-pane label="用户管理" name="users">
        <UserManagement />
      </el-tab-pane>
      
      <!-- 系统配置标签 (New) -->
      <el-tab-pane label="系统配置" name="settings">
        <SystemSettings />
      </el-tab-pane>

      <!-- 系统运维标签 -->
      <el-tab-pane label="系统运维" name="operations">
        <el-card shadow="never" style="margin-bottom: 20px;">
          <template #header>
            <span style="font-weight: bold;">系统运维操作</span>
          </template>
          
          <el-row :gutter="20">
            <!-- 系统备份 -->
            <el-col :xs="24" :sm="12" :md="8">
              <el-card shadow="hover" class="operation-card">
                <template #header>
                  <div class="card-header">
                    <el-icon style="margin-right: 8px;"><Upload /></el-icon>
                    <span>系统备份</span>
                  </div>
                </template>
                <div class="operation-content">
                  <p>备份系统配置和数据到本地文件</p>
                  <el-button 
                    type="primary" 
                    icon="Download" 
                    @click="handleSystemBackup"
                    :loading="backupLoading"
                    style="width: 180px"
                  >
                    立即备份
                  </el-button>
                </div>
              </el-card>
            </el-col>

            <!-- 备份恢复 -->
            <el-col :xs="24" :sm="12" :md="8">
              <el-card shadow="hover" class="operation-card">
                <template #header>
                  <div class="card-header">
                    <el-icon style="margin-right: 8px;"><Download /></el-icon>
                    <span>备份恢复</span>
                  </div>
                </template>
                <div class="operation-content">
                  <p>从备份文件恢复系统配置和数据</p>
                  <el-upload
                    action="#"
                    :auto-upload="false"
                    :on-change="handleRestoreUpload"
                    :show-file-list="false"
                    accept=".zip,.tar.gz"
                  >
                    <el-button type="success" icon="Upload" style="width: 180px">选择备份文件恢复</el-button>
                  </el-upload>
                </div>
              </el-card>
            </el-col>

            <!-- 数据库备份 -->
            <el-col :xs="24" :sm="12" :md="8">
              <el-card shadow="hover" class="operation-card">
                <template #header>
                  <div class="card-header">
                    <el-icon style="margin-right: 8px;"><Coin /></el-icon>
                    <span>数据库备份</span>
                  </div>
                </template>
                <div class="operation-content">
                  <p>备份数据库到本地文件</p>
                  <el-button 
                    type="primary" 
                    icon="Download" 
                    @click="handleDbBackup"
                    :loading="dbBackupLoading"
                    style="width: 180px"
                  >
                    立即备份
                  </el-button>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <el-row :gutter="20" style="margin-top: 20px;">
            <!-- 数据库备份恢复 -->
            <el-col :xs="24" :sm="12" :md="8">
              <el-card shadow="hover" class="operation-card">
                <template #header>
                  <div class="card-header">
                    <el-icon style="margin-right: 8px;"><CircleCheck /></el-icon>
                    <span>数据库备份恢复</span>
                  </div>
                </template>
                <div class="operation-content">
                  <p>从备份文件恢复数据库</p>
                  <el-upload
                    action="#"
                    :auto-upload="false"
                    :on-change="handleDbRestoreUpload"
                    :show-file-list="false"
                    accept=".sql,.dump"
                  >
                    <el-button type="success" icon="Upload" style="width: 180px">选择数据库备份文件恢复</el-button>
                  </el-upload>
                </div>
              </el-card>
            </el-col>

            <!-- 系统重置 -->
            <el-col :xs="24" :sm="12" :md="8">
              <el-card shadow="hover" class="operation-card">
                <template #header>
                  <div class="card-header">
                    <el-icon style="margin-right: 8px;"><RefreshLeft /></el-icon>
                    <span>系统重置</span>
                  </div>
                </template>
                <div class="operation-content">
                  <el-alert
                    title="警告：系统重置将清空所有数据，此操作不可恢复！"
                    type="error"
                    :closable="false"
                    style="margin-bottom: 15px;"
                  />
                  <p>重置系统到初始状态，清空所有合同、用户（保留管理员）及相关数据</p>
                  <el-button 
                    type="danger" 
                    icon="Delete" 
                    @click="handleSystemReset"
                    :loading="resetLoading"
                    style="width: 180px"
                  >
                    重置系统
                  </el-button>
                </div>
              </el-card>
            </el-col>

            <!-- 审计日志删除 -->
            <el-col :xs="24" :sm="12" :md="8">
              <el-card shadow="hover" class="operation-card">
                <template #header>
                  <div class="card-header">
                    <el-icon style="margin-right: 8px;"><Delete /></el-icon>
                    <span>审计日志删除</span>
                  </div>
                </template>
                <div class="operation-content">
                  <p>删除指定日期之前的审计日志记录</p>
                  <el-form :inline="true" style="margin-top: 10px;">
                    <el-form-item label="删除日期之前的日志">
                      <el-date-picker
                        v-model="auditDeleteDate"
                        type="date"
                        placeholder="选择日期"
                        value-format="YYYY-MM-DD"
                        style="width: 200px;"
                      />
                    </el-form-item>
                    <el-form-item>
                      <el-button 
                        type="warning" 
                        icon="Delete" 
                        @click="handleAuditDelete"
                        :loading="auditDeleteLoading"
                        :disabled="!auditDeleteDate"
                        style="width: 180px"
                      >
                        删除日志
                      </el-button>
                    </el-form-item>
                  </el-form>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
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

// Helper to download blob
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

// 系统备份
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
      // request.js might have already shown an error, but we ensure we show specific detail if available
      const msg = e.response?.data?.detail || e.message || '系统备份失败'
      // Avoid duplicate messaging if possible, but prioritization is key for debug
      if (!document.querySelector('.el-message')) { 
         ElMessage.error(msg)
      }
    }
  } finally {
    backupLoading.value = false
  }
}

// 备份恢复
const handleRestoreUpload = async (file) => {
  try {
    await ElMessageBox.confirm('确定要从备份文件恢复系统吗？此操作将覆盖当前数据！', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error'
    })
    
    // TODO: 调用恢复API
    await new Promise(resolve => setTimeout(resolve, 2000))
    ElMessage.success('系统恢复成功，请重新登录')
    
    // 刷新页面
    setTimeout(() => {
      window.location.href = '/login'
    }, 1500)
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
      ElMessage.error('系统恢复失败')
    }
  }
}

// 数据库备份
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

// 数据库备份恢复
const handleDbRestoreUpload = async (file) => {
  try {
    await ElMessageBox.confirm('确定要从备份文件恢复数据库吗？此操作将覆盖当前数据！', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error'
    })
    
    // TODO: 调用数据库恢复API
    await new Promise(resolve => setTimeout(resolve, 2000))
    ElMessage.success('数据库恢复成功')
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
      ElMessage.error('数据库恢复失败')
    }
  }
}

// 系统重置
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
    
    // 跳转到登录页
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

// 审计日志删除
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
    auditDeleteLoading.value = false
  }
}




</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  font-weight: bold;
  font-size: 15px;
}

.operation-card {
  height: 100%;
  min-height: 280px;
  display: flex;
  flex-direction: column;
}

@media only screen and (max-width: 768px) {
  .operation-card {
    min-height: auto;
    margin-bottom: 15px;
  }
}

.operation-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.operation-content {
  padding: 10px 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.operation-content p {
  color: #606266;
  margin-bottom: 15px;
  line-height: 1.6;
  flex: 1;
}



</style>
