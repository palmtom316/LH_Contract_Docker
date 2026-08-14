<template>
  <div class="warehouse-attachment">
    <input
      ref="inputRef"
      class="warehouse-attachment__input"
      type="file"
      :accept="WAREHOUSE_FILE_ACCEPT"
      capture="environment"
      :disabled="disabled || uploading"
      @change="onFileChange"
    >
    <div v-if="modelValue" class="warehouse-attachment__preview">
      <el-button type="primary" link @click="openFile">{{ fileName || '查看附件' }}</el-button>
      <el-button v-if="!disabled" type="danger" link @click="clear">删除</el-button>
    </div>
    <el-button
      v-else
      :loading="uploading"
      :disabled="disabled"
      @click="inputRef?.click()"
    >
      {{ uploading ? '上传中...' : buttonText }}
    </el-button>
    <p class="warehouse-attachment__tip">支持 PDF / 图片，手机可直接拍照上传</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadFile } from '@/api/common'
import { openProtectedFile } from '@/utils/protectedFiles'
import { WAREHOUSE_FILE_ACCEPT } from '@/constants/warehouse'

const props = defineProps({
  modelValue: { type: String, default: '' },
  fileName: { type: String, default: '' },
  buttonText: { type: String, default: '上传文件或拍照' },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'update:fileName'])

const inputRef = ref(null)
const uploading = ref(false)

async function onFileChange(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  uploading.value = true
  try {
    const result = await uploadFile(file, 'warehouse')
    const path = result?.key || result?.path
    if (!path) throw new Error('上传返回路径为空')
    emit('update:modelValue', path)
    emit('update:fileName', file.name)
    ElMessage.success('上传成功')
  } catch (error) {
    ElMessage.error(error?.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

function clear() {
  emit('update:modelValue', '')
  emit('update:fileName', '')
}

async function openFile() {
  if (props.modelValue) await openProtectedFile(props.modelValue)
}
</script>

<style scoped>
.warehouse-attachment { display: grid; gap: 6px; }
.warehouse-attachment__input { display: none; }
.warehouse-attachment__preview { display: flex; align-items: center; gap: 8px; }
.warehouse-attachment__tip { margin: 0; color: var(--text-muted, #909399); font-size: 12px; }
</style>
