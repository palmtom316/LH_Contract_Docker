<template>
  <div class="app-range-field" :class="{ 'app-range-field--error': rangeError }">
    <div class="app-range-field__icon">
      <el-icon><Calendar /></el-icon>
    </div>
    <template v-if="isMonthMode">
      <el-date-picker
        v-model="startPickerValue"
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
        v-model="endPickerValue"
        class="app-range-field__picker"
        :type="pickerType"
        :value-format="resolvedValueFormat"
        :format="resolvedDisplayFormat"
        :placeholder="endPlaceholder"
        :clearable="clearable"
        unlink-panels
      />
    </template>
    <template v-else>
      <SmartDateInput
        :key="startResetKey"
        :model-value="startValue"
        class="app-range-field__input"
        :placeholder="startPlaceholder"
        @update:model-value="handleStartUpdate"
        @validity-change="handleStartValidity"
      />
      <span class="app-range-field__separator">至</span>
      <SmartDateInput
        :key="endResetKey"
        :model-value="endValue"
        class="app-range-field__input"
        :placeholder="endPlaceholder"
        @update:model-value="handleEndUpdate"
        @validity-change="handleEndValidity"
      />
    </template>
  </div>
  <div v-if="rangeError" class="app-range-field__error">{{ rangeError }}</div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Calendar } from '@element-plus/icons-vue'
import SmartDateInput from '@/components/SmartDateInput.vue'

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
    default: ''
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

const isMonthMode = computed(() => props.type === 'month')
const pickerType = computed(() => (props.type === 'month' ? 'month' : 'date'))
const resolvedValueFormat = computed(() => props.valueFormat || (props.type === 'month' ? 'YYYY-MM' : 'YYYY-MM-DD'))
const resolvedDisplayFormat = computed(() => props.displayFormat || (props.type === 'month' ? 'YYYY-MM' : 'YYYY-MM-DD'))

const startValue = ref(props.modelValue?.[0] || '')
const endValue = ref(props.modelValue?.[1] || '')
const startValid = ref(true)
const endValid = ref(true)
const rangeError = ref('')
const lastEmitted = ref([props.modelValue?.[0] || '', props.modelValue?.[1] || ''])
const startResetKey = ref(0)
const endResetKey = ref(0)
const lastEmitWasInvalid = ref(false)
const lastEmitWasRangeError = ref(false)

function normalizeArray(value) {
  if (!Array.isArray(value)) return []
  return [value?.[0] || '', value?.[1] || '']
}

watch(
  () => props.modelValue,
  (value) => {
    const nextStart = value?.[0] || ''
    const nextEnd = value?.[1] || ''
    const [lastStart, lastEnd] = lastEmitted.value
    const nextPair = normalizeArray(value)
    const isSelfEcho =
      Array.isArray(value) &&
      value.length >= 2 &&
      nextPair[0] === lastStart &&
      nextPair[1] === lastEnd &&
      (lastEmitWasInvalid.value || lastEmitWasRangeError.value)
    const isExternalReset =
      !isSelfEcho &&
      (!value ||
        value.length === 0 ||
        (!nextStart && !nextEnd && (lastStart || lastEnd || startValue.value || endValue.value)))
    const echoedStart = nextStart === '' && lastStart === ''
    const echoedEnd = nextEnd === '' && lastEnd === ''

    if (isExternalReset || !(!startValid.value && echoedStart)) {
      startValue.value = nextStart
    }
    if (isExternalReset || !(!endValid.value && echoedEnd)) {
      endValue.value = nextEnd
    }

    if (isExternalReset || (!echoedStart && !echoedEnd)) {
      startValid.value = true
      endValid.value = true
      if (isExternalReset) {
        rangeError.value = ''
        lastEmitWasInvalid.value = false
        lastEmitWasRangeError.value = false
      }
      if (isExternalReset) {
        startResetKey.value += 1
        endResetKey.value += 1
      }
    }
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
    lastEmitted.value = [startValid.value ? startValue.value : '', endValid.value ? endValue.value : '']
    lastEmitWasInvalid.value = true
    lastEmitWasRangeError.value = false
    emit('update:modelValue', lastEmitted.value)
    return
  }

  if (startValue.value && endValue.value && startValue.value > endValue.value) {
    rangeError.value = '开始日期不能晚于结束日期'
    lastEmitted.value = ['', '']
    lastEmitWasInvalid.value = false
    lastEmitWasRangeError.value = true
    emit('update:modelValue', lastEmitted.value)
    return
  }

  rangeError.value = ''
  lastEmitted.value = [startValue.value || '', endValue.value || '']
  lastEmitWasInvalid.value = false
  lastEmitWasRangeError.value = false
  emit('update:modelValue', lastEmitted.value)
}

const startPickerValue = computed({
  get: () => normalizePickerValue(props.modelValue?.[0]),
  set: (value) => {
    emit('update:modelValue', normalizePickerRange(value, props.modelValue?.[1] || ''))
  }
})

const endPickerValue = computed({
  get: () => normalizePickerValue(props.modelValue?.[1]),
  set: (value) => {
    emit('update:modelValue', normalizePickerRange(props.modelValue?.[0] || '', value))
  }
})

function normalizePickerValue(value) {
  if (!value) return ''

  if (typeof value === 'string') {
    return props.type === 'month' ? value.slice(0, 7) : value.slice(0, 10)
  }

  return value
}

function normalizePickerRange(start, end) {
  const normalizedStart = normalizePickerValue(start)
  const normalizedEnd = normalizePickerValue(end)

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

.app-range-field__input,
.app-range-field__picker {
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
