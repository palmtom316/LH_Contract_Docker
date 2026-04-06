
<template>
  <div class="smart-date-input">
    <el-input
      v-model="displayValue"
      :placeholder="placeholder"
      @blur="commitInput"
      @clear="handleClear"
      @keyup.enter="commitInput"
      clearable
    >
      <template #prefix>
        <el-icon><Calendar /></el-icon>
      </template>
    </el-input>
    <div v-if="hasError" class="smart-date-input__error">{{ errorMessage }}</div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Calendar } from '@element-plus/icons-vue'
import { formatDateInputDisplay, parseFlexibleDateInput } from '@/utils/dateInput'

const props = defineProps({
  modelValue: {
    type: String,
    default: null
  },
  placeholder: {
    type: String,
    default: '请输入日期'
  }
})

const emit = defineEmits(['update:modelValue', 'validity-change'])

const displayValue = ref(formatDateInputDisplay(props.modelValue))
const errorMessage = ref('')

watch(
  () => props.modelValue,
  (value) => {
    errorMessage.value = ''
    displayValue.value = formatDateInputDisplay(value)
  }
)

const hasError = computed(() => Boolean(errorMessage.value))

function commitInput() {
  const raw = displayValue.value?.trim() ?? ''

  if (!raw) {
    errorMessage.value = ''
    emit('update:modelValue', null)
    emit('validity-change', { valid: true, value: null })
    return
  }

  const parsed = parseFlexibleDateInput(raw)
  if (!parsed) {
    errorMessage.value = '日期格式无法识别，请输入如 2026/04/06'
    emit('validity-change', { valid: false, value: null, raw })
    return
  }

  errorMessage.value = ''
  displayValue.value = parsed.displayValue
  emit('update:modelValue', parsed.isoValue)
  emit('validity-change', { valid: true, value: parsed.isoValue, raw: parsed.displayValue })
}

function handleClear() {
  displayValue.value = ''
  errorMessage.value = ''
  emit('update:modelValue', null)
  emit('validity-change', { valid: true, value: null })
}
</script>
