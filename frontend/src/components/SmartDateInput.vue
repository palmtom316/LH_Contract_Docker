
<template>
  <el-input 
    v-model="displayValue" 
    placeholder="YYYY-MM-DD" 
    @blur="handleBlur"
    @keyup.enter="handleBlur"
    clearable
  >
    <template #prefix>
        <el-icon><Calendar /></el-icon>
    </template>
  </el-input>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Calendar } from '@element-plus/icons-vue' // Assuming Element Plus icons globally available or imported

const props = defineProps({
  modelValue: String // Expect YYYY-MM-DD
})

const emit = defineEmits(['update:modelValue'])

const displayValue = ref(props.modelValue)

watch(() => props.modelValue, (val) => {
    displayValue.value = val
})

function handleBlur() {
    const raw = displayValue.value
    if (!raw) {
        emit('update:modelValue', null)
        return
    }

    // Attempt to parse
    // Replace custom separators with '-'
    // Separators: . / - — 。
    const normalized = raw.replace(/[./—。]/g, '-')
    // Try native Date parse? Strings like 2025-12-25 work.
    // 2025-1-1 works.
    
    // Check pattern YYYY-MM-DD
    const parts = normalized.split('-')
    if (parts.length === 3) {
        let y = parseInt(parts[0])
        let m = parseInt(parts[1])
        let d = parseInt(parts[2])
        
        if (!isNaN(y) && !isNaN(m) && !isNaN(d)) {
            // Pad
            const mStr = m.toString().padStart(2, '0')
            const dStr = d.toString().padStart(2, '0')
            const result = `${y}-${mStr}-${dStr}`
            
            // Validate validity
            const dateObj = new Date(result)
            if (!isNaN(dateObj.getTime())) {
                displayValue.value = result
                emit('update:modelValue', result)
                return
            }
        }
    } else if (raw.length === 8 && !isNaN(Number(raw))) {
         // 20251225 support
         const y = raw.substring(0, 4)
         const m = raw.substring(4, 6)
         const d = raw.substring(6, 8)
         const result = `${y}-${m}-${d}`
         displayValue.value = result
         emit('update:modelValue', result)
         return
    }
    
    // If failed, maybe revert or keep as is (but emit null?)
    // Requirement says "converted to standard". If fail, user might want to correct.
    // We'll leave it but maybe show warning?
    // For now, if invalid, we don't update modelValue or we update with invalid string?
    // Better to only update if valid.
}
</script>
