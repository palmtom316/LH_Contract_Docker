
<template>
  <el-input 
    v-model="displayValue" 
    :placeholder="placeholder"
    @blur="handleBlur"
    @keyup.enter="handleBlur"
  >
    <template #append v-if="showIcon">
        <span>=</span>
    </template>
  </el-input>
</template>

<script setup>
import { ref, watch } from 'vue'
import { evaluateQuantityExpression } from '@/utils/quantityExpression'

const props = defineProps({
  modelValue: [Number, String],
  placeholder: String,
  precision: {
    type: Number,
    default: 2
  },
  showIcon: {
      type: Boolean, 
      default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const displayValue = ref(props.modelValue)

watch(() => props.modelValue, (val) => {
    // avoid resetting if trying to type
    if (parseFloat(val) !== parseFloat(displayValue.value)) {
         displayValue.value = val
    }
})

function handleBlur() {
    let raw = String(displayValue.value).trim()
    if (!raw) {
        emit('update:modelValue', 0)
        return
    }
    
    // Check if formula characters are present
    if (/^[\d+\-*/.()x×÷\s]+$/i.test(raw)) {
        try {
            // Normalize multiplication/division symbols
            const normalized = raw
                .replace(/×/g, '*')
                .replace(/÷/g, '/')
                .replace(/x/gi, '*')
            
            const result = evaluateQuantityExpression(normalized, props.precision)
            if (result !== null) {
                displayValue.value = result
                emit('update:modelValue', result)
                return
            }
        } catch (e) {
            // If mathjs fails to parse, fall through to simple parsing
            console.debug('Formula evaluation failed:', e.message)
        }
    }
    
    // If not a formula, try parsing as number
    const num = parseFloat(raw)
    if (!isNaN(num)) {
         emit('update:modelValue', num)
    }
}
</script>
