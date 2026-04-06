<template>
  <div class="app-range-field" :class="{ 'app-range-field--error': rangeError }">
    <div class="app-range-field__icon">
      <el-icon><Calendar /></el-icon>
    </div>
    <SmartDateInput
      :model-value="startValue"
      class="app-range-field__input"
      :placeholder="startPlaceholder"
      @update:model-value="handleStartUpdate"
      @validity-change="handleStartValidity"
    />
    <span class="app-range-field__separator">至</span>
    <SmartDateInput
      :model-value="endValue"
      class="app-range-field__input"
      :placeholder="endPlaceholder"
      @update:model-value="handleEndUpdate"
      @validity-change="handleEndValidity"
    />
  </div>
  <div v-if="rangeError" class="app-range-field__error">{{ rangeError }}</div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Calendar } from '@element-plus/icons-vue'
import SmartDateInput from '@/components/SmartDateInput.vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  startPlaceholder: {
    type: String,
    default: '开始日期'
  },
  endPlaceholder: {
    type: String,
    default: '结束日期'
  }
})

const emit = defineEmits(['update:modelValue'])

const startValue = ref(props.modelValue?.[0] || '')
const endValue = ref(props.modelValue?.[1] || '')
const startValid = ref(true)
const endValid = ref(true)
const rangeError = ref('')

watch(
  () => props.modelValue,
  (value) => {
    startValue.value = value?.[0] || ''
    endValue.value = value?.[1] || ''
    startValid.value = true
    endValid.value = true
    rangeError.value = ''
  },
  { deep: true }
)

function handleStartUpdate(value) {
  startValue.value = value || ''
  startValid.value = true
  emitRange()
}

function handleEndUpdate(value) {
  endValue.value = value || ''
  endValid.value = true
  emitRange()
}

function handleStartValidity(payload) {
  startValid.value = payload?.valid !== false
  if (!startValid.value) {
    emitRange()
  }
}

function handleEndValidity(payload) {
  endValid.value = payload?.valid !== false
  if (!endValid.value) {
    emitRange()
  }
}

function emitRange() {
  if (!startValid.value || !endValid.value) {
    rangeError.value = ''
    emit('update:modelValue', [startValid.value ? startValue.value : '', endValid.value ? endValue.value : ''])
    return
  }

  if (startValue.value && endValue.value && startValue.value > endValue.value) {
    rangeError.value = '开始日期不能晚于结束日期'
    emit('update:modelValue', ['', ''])
    return
  }

  rangeError.value = ''
  emit('update:modelValue', [startValue.value || '', endValue.value || ''])
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

.app-range-field__input {
  width: 100%;
  min-width: 0;
  position: relative;
}

.app-range-field :deep(.smart-date-input) {
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

.app-range-field__input:first-of-type {
  padding-right: 2px;
  border-right: 1px solid color-mix(in srgb, var(--border-subtle) 72%, transparent);
}

.app-range-field__input:last-of-type {
  padding-left: 2px;
}

.app-range-field__error {
  margin-top: 4px;
  color: var(--color-danger, #e24d4d);
  font-size: 12px;
}
</style>
