
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

const props = defineProps({
  modelValue: [Number, String],
  placeholder: String,
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
    if (/^[\d+\-*/.()\s]+$/.test(raw)) {
        try {
            // Safe eval using Function constructor with restricted scope
            // But 'eval' or 'Function' with arithmetic is mostly what we need
            // "100+200"
            const result = new Function('return ' + raw)()
            if (!isNaN(result) && isFinite(result)) {
                // Round to 2 decimals usually involved in money
                const rounded = Math.round(result * 100) / 100
                displayValue.value = rounded
                emit('update:modelValue', rounded)
                return
            }
        } catch (e) {
            // console.error(e)
        }
    }
    
    // If not a formula, try parsing as number
    const num = parseFloat(raw)
    if (!isNaN(num)) {
         emit('update:modelValue', num)
    }
}
</script>
