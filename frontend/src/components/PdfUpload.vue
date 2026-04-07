<template>
  <div class="pdf-upload-container">
    <!-- Display uploaded file if exists -->
    <div v-if="filePath && showPreview" class="file-preview">
      <el-button 
        type="primary" 
        link 
        icon="Document" 
        @click="handleView"
      >
        {{ displayFileName }}
      </el-button>
      <el-button 
        type="danger" 
        link 
        icon="Delete" 
        @click="handleRemove"
        v-if="!disabled"
      >
        删除
      </el-button>
    </div>

    <!-- Upload component -->
    <el-upload
      v-if="!filePath || !showPreview"
      ref="uploadRef"
      class="upload-component"
      action="#"
      :http-request="handleUploadRequest"
      :limit="1"
      :on-remove="handleRemove"
      :file-list="fileList"
      :disabled="disabled || uploading"
      :accept="accept"
      :show-file-list="showFileList"
    >
      <template #trigger>
        <el-button 
          :type="buttonType" 
          :loading="uploading"
          :disabled="disabled"
        >
          <el-icon v-if="!uploading"><Upload /></el-icon>
          {{ uploading ? '上传中...' : buttonText }}
        </el-button>
      </template>
      <template #tip>
        <div class="el-upload__tip" v-if="showTip">
          {{ tipText }}
        </div>
      </template>
    </el-upload>

    <!-- PDF Viewer Dialog -->
    <el-dialog 
      v-model="viewerVisible" 
      title="PDF 预览" 
      fullscreen 
      destroy-on-close
      append-to-body
    >
      <PdfViewer :source="filePath" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { uploadFile } from '@/api/common'
import { ElMessage } from 'element-plus'
import PdfViewer from './PdfViewer.vue'

const props = defineProps({
  // v-model binding for file path
  modelValue: {
    type: String,
    default: ''
  },
  // Display file name (optional, defaults to extracted from path)
  fileName: {
    type: String,
    default: ''
  },
  // Button text
  buttonText: {
    type: String,
    default: '选择文件 (PDF)'
  },
  // Button type
  buttonType: {
    type: String,
    default: 'primary'
  },
  // Tip text
  tipText: {
    type: String,
    default: '支持 PDF 格式，单个文件不超过 50MB'
  },
  // Show tip
  showTip: {
    type: Boolean,
    default: true
  },
  // Accept file types
  accept: {
    type: String,
    default: '.pdf'
  },
  // Show file list in upload component
  showFileList: {
    type: Boolean,
    default: false
  },
  // Show preview when file exists
  showPreview: {
    type: Boolean,
    default: true
  },
  // Disabled state
  disabled: {
    type: Boolean,
    default: false
  },
  // Upload directory (contracts, invoices, receipts, settlements, expenses)
  uploadDir: {
    type: String,
    default: 'contracts'
  }
})

const emit = defineEmits(['update:modelValue', 'update:fileKey', 'upload-success', 'upload-error', 'remove'])

const uploadRef = ref(null)
const uploading = ref(false)
const viewerVisible = ref(false)
const fileList = ref([])

// Computed file path from v-model
const filePath = computed(() => props.modelValue || '')

// Computed display file name
const displayFileName = computed(() => {
  if (props.fileName) return props.fileName
  if (!filePath.value) return ''
  // Extract filename from path
  const parts = filePath.value.split('/')
  return parts[parts.length - 1] || '查看文件'
})

// Watch for external filePath changes
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    fileList.value = [{
      name: displayFileName.value,
      url: newVal
    }]
  } else {
    fileList.value = []
  }
}, { immediate: true })

// Handle upload request
const handleUploadRequest = async (option) => {
  uploading.value = true
  try {
    const res = await uploadFile(option.file, props.uploadDir)
    
    if (res && (res.path || res.key)) {
      // Prefer key, fallback to path if key missing (legacy)
      const val = res.key || res.path
      emit('update:modelValue', val)
      emit('update:fileKey', res.key) // Emit key specifically
      emit('upload-success', res)
      
      fileList.value = [{
        name: option.file.name,
        url: res.path
      }]
      
      ElMessage.success('上传成功')
    } else {
      throw new Error('上传返回路径为空')
    }
  } catch (e) {
    console.error('[PdfUpload] Upload error:', e)
    ElMessage.error('上传失败: ' + (e.message || e))
    emit('upload-error', e)
    option.onError && option.onError(e)
  } finally {
    uploading.value = false
  }
}

// Handle file removal
const handleRemove = () => {
  emit('update:modelValue', '')
  emit('remove')
  fileList.value = []
}

// Handle view PDF
const handleView = () => {
  if (!filePath.value) return
  viewerVisible.value = true
}

// Open PDF in new tab
const openInNewTab = () => {
  if (!filePath.value) return
  window.open(filePath.value, '_blank')
}

// Expose methods for parent components
defineExpose({
  handleView,
  openInNewTab,
  handleRemove
})
</script>

<style scoped lang="scss">
.pdf-upload-container {
  display: inline-block;
  
  .file-preview {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: color-mix(in srgb, var(--surface-panel-muted) 72%, var(--surface-panel) 28%);
    border: 1px solid var(--border-subtle);
    border-radius: 4px;
    
    .el-button {
      font-size: 14px;
    }
  }
  
  .upload-component {
    :deep(.el-upload__tip) {
      margin-top: 6px;
      color: var(--text-muted);
      font-size: 12px;
    }
  }
}
</style>
