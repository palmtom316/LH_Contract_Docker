<template>
  <div class="error-boundary">
    <slot v-if="!hasError"></slot>
    
    <div v-else class="error-fallback">
      <el-result 
        icon="error" 
        :title="title"
        :sub-title="subTitle"
      >
        <template #extra>
          <div class="error-actions">
            <el-button type="primary" @click="handleRetry">
              <el-icon><Refresh /></el-icon>
              重试
            </el-button>
            <el-button @click="handleBack">
              <el-icon><Back /></el-icon>
              返回
            </el-button>
          </div>
          
          <el-collapse v-if="showDetails && errorDetails" class="error-details">
            <el-collapse-item title="错误详情" name="details">
              <pre class="error-message">{{ errorDetails }}</pre>
            </el-collapse-item>
          </el-collapse>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ref, onErrorCaptured, defineProps, defineEmits } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Back } from '@element-plus/icons-vue'

const props = defineProps({
  title: {
    type: String,
    default: '页面加载出错'
  },
  subTitle: {
    type: String,
    default: '抱歉，页面遇到了问题。请稍后重试或联系管理员。'
  },
  showDetails: {
    type: Boolean,
    default: false  // Only show in development
  },
  onError: {
    type: Function,
    default: null
  }
})

const emit = defineEmits(['error', 'retry'])

const router = useRouter()
const hasError = ref(false)
const errorDetails = ref('')

/**
 * Capture errors from child components
 */
onErrorCaptured((error, instance, info) => {
  hasError.value = true
  
  // Format error details
  const details = [
    `Error: ${error.message}`,
    `Component: ${instance?.$options?.name || 'Unknown'}`,
    `Info: ${info}`,
    '',
    'Stack Trace:',
    error.stack || 'Not available'
  ].join('\n')
  
  errorDetails.value = details
  
  // Log to console in development
  console.error('[ErrorBoundary] Caught error:', error)
  console.error('[ErrorBoundary] Component:', instance)
  console.error('[ErrorBoundary] Info:', info)
  
  // Call custom error handler if provided
  if (props.onError) {
    props.onError(error, instance, info)
  }
  
  // Emit error event
  emit('error', { error, instance, info })
  
  // Return false to prevent the error from propagating
  return false
})

/**
 * Handle retry button click
 */
const handleRetry = () => {
  hasError.value = false
  errorDetails.value = ''
  emit('retry')
}

/**
 * Handle back button click
 */
const handleBack = () => {
  router.back()
}
</script>

<style scoped>
.error-boundary {
  width: 100%;
  height: 100%;
}

.error-fallback {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  padding: 40px 20px;
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 20px;
}

.error-details {
  width: 100%;
  max-width: 600px;
  margin-top: 20px;
  text-align: left;
}

.error-message {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}

:deep(.el-result) {
  padding: 40px 30px;
}

:deep(.el-result__title) {
  margin-top: 20px;
}
</style>
