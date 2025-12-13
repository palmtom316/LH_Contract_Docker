<template>
  <div class="pdf-link-container" v-if="filePath">
    <el-button 
      v-if="displayMode === 'button'"
      link 
      type="primary" 
      size="small"
      :icon="icon"
      @click="handleClick"
    >
      {{ buttonText }}
    </el-button>
    
    <el-link 
      v-else
      type="primary" 
      :underline="false"
      @click="handleClick"
    >
      <el-icon v-if="showIcon"><Document /></el-icon>
      {{ buttonText }}
    </el-link>

    <!-- PDF Viewer Dialog -->
    <el-dialog 
      v-model="viewerVisible" 
      :title="dialogTitle" 
      fullscreen 
      destroy-on-close
      append-to-body
    >
      <PdfViewer :source="filePath" />
    </el-dialog>
  </div>
  <span v-else class="no-file-text">{{ noFileText }}</span>
</template>

<script setup>
import { ref } from 'vue'
import { Document } from '@element-plus/icons-vue'
import PdfViewer from './PdfViewer.vue'

const props = defineProps({
  // File path to the PDF
  filePath: {
    type: String,
    default: ''
  },
  // Button/Link text
  buttonText: {
    type: String,
    default: '查看'
  },
  // Dialog title
  dialogTitle: {
    type: String,
    default: 'PDF 预览'
  },
  // Display mode: 'button' or 'link'
  displayMode: {
    type: String,
    default: 'button',
    validator: (v) => ['button', 'link'].includes(v)
  },
  // Show icon in link mode
  showIcon: {
    type: Boolean,
    default: true
  },
  // Icon for button mode
  icon: {
    type: String,
    default: 'Document'
  },
  // Open mode: 'dialog' or 'tab'
  openMode: {
    type: String,
    default: 'tab',
    validator: (v) => ['dialog', 'tab'].includes(v)
  },
  // Text to show when no file
  noFileText: {
    type: String,
    default: '-'
  }
})

const viewerVisible = ref(false)

// Handle click
const handleClick = () => {
  if (!props.filePath) return
  
  if (props.openMode === 'dialog') {
    viewerVisible.value = true
  } else {
    // Open in new tab
    window.open(props.filePath, '_blank')
  }
}

// Expose methods
defineExpose({
  openDialog: () => { viewerVisible.value = true },
  openInNewTab: () => { window.open(props.filePath, '_blank') }
})
</script>

<style scoped lang="scss">
.pdf-link-container {
  display: inline-flex;
  align-items: center;
  
  .el-link {
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
}

.no-file-text {
  color: #c0c4cc;
  font-size: 14px;
}
</style>
