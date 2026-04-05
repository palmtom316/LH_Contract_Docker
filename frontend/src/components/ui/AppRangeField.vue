<template>
  <div class="app-range-field" :class="{ 'app-range-field--month': type === 'month' }">
    <div class="app-range-field__icon">
      <el-icon><Calendar /></el-icon>
    </div>
    <el-date-picker
      v-model="startValue"
      class="app-range-field__picker"
      :type="pickerType"
      :value-format="resolvedValueFormat"
      :format="resolvedDisplayFormat"
      :placeholder="startPlaceholder"
      :clearable="clearable"
      unlink-panels
    />
    <span class="app-range-field__separator">至</span>
    <el-date-picker
      v-model="endValue"
      class="app-range-field__picker"
      :type="pickerType"
      :value-format="resolvedValueFormat"
      :format="resolvedDisplayFormat"
      :placeholder="endPlaceholder"
      :clearable="clearable"
      unlink-panels
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Calendar } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  type: {
    type: String,
    default: 'date'
  },
  valueFormat: {
    type: String,
    default: 'YYYY-MM-DD'
  },
  displayFormat: {
    type: String,
    default: ''
  },
  startPlaceholder: {
    type: String,
    default: '开始日期'
  },
  endPlaceholder: {
    type: String,
    default: '结束日期'
  },
  clearable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue'])

const pickerType = computed(() => (props.type === 'month' ? 'month' : 'date'))
const resolvedValueFormat = computed(() => props.valueFormat || (props.type === 'month' ? 'YYYY-MM' : 'YYYY-MM-DD'))
const resolvedDisplayFormat = computed(() => props.displayFormat || (props.type === 'month' ? 'YYYY-MM' : 'YYYY-MM-DD'))

const startValue = computed({
  get: () => normalizeValue(props.modelValue?.[0]),
  set: (value) => {
    emit('update:modelValue', normalizeRange(value, props.modelValue?.[1] || ''))
  }
})

const endValue = computed({
  get: () => normalizeValue(props.modelValue?.[1]),
  set: (value) => {
    emit('update:modelValue', normalizeRange(props.modelValue?.[0] || '', value))
  }
})

function normalizeValue(value) {
  if (!value) return ''

  if (typeof value === 'string') {
    return props.type === 'month' ? value.slice(0, 7) : value.slice(0, 10)
  }

  return value
}

function normalizeRange(start, end) {
  const normalizedStart = normalizeValue(start)
  const normalizedEnd = normalizeValue(end)

  if (!normalizedStart && !normalizedEnd) return []
  return [normalizedStart || '', normalizedEnd || '']
}
</script>

<style scoped lang="scss">
.app-range-field {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 6px;
  width: 100%;
  min-width: 0;
  min-height: 42px;
  padding: 3px 8px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface-panel) 96%, var(--surface-panel-muted) 4%);
  border: 1px solid color-mix(in srgb, var(--border-subtle) 82%, var(--brand-primary) 18%);
  container-type: inline-size;
}

.app-range-field__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 15px;
}

.app-range-field__separator {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  padding-inline: 6px;
  white-space: nowrap;
}

.app-range-field__picker {
  width: 100%;
  min-width: 0;
  position: relative;
}

.app-range-field :deep(.el-date-editor.el-input),
.app-range-field :deep(.el-date-editor.el-input__wrapper) {
  width: 100%;
  min-width: 0;
  max-width: 100%;
}

.app-range-field :deep(.el-input__wrapper) {
  min-height: 34px;
  padding-inline: 2px;
  border-radius: 8px;
  box-shadow: none;
  background: transparent;
}

.app-range-field :deep(.el-input__prefix),
.app-range-field :deep(.el-input__suffix) {
  display: none;
}

.app-range-field :deep(.el-input__inner) {
  text-align: left;
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.2;
  text-overflow: ellipsis;
}

.app-range-field__picker:first-of-type {
  padding-right: 2px;
  border-right: 1px solid color-mix(in srgb, var(--border-subtle) 72%, transparent);
}

.app-range-field__picker:last-of-type {
  padding-left: 2px;
}
</style>
