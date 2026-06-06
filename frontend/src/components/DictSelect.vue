
<template>
  <el-select 
    v-bind="$attrs" 
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :loading="loading"
    filterable
    clearable
  >
    <el-option
      v-for="item in options"
      :key="item.value"
      :label="item.label"
      :value="item.value"
    />
  </el-select>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useSystemStore } from '@/stores/system'

const props = defineProps({
  modelValue: [String, Number, Array],
  category: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const systemStore = useSystemStore()
const loading = ref(false)

const options = computed(() => systemStore.getOptions(props.category))

onMounted(async () => {
    // If empty, fetch
    if (options.value.length === 0) {
        loading.value = true
        await systemStore.fetchOptions(props.category)
        loading.value = false
    }
})

// Watch category change
watch(() => props.category, async (newVal) => {
    if (newVal) {
        loading.value = true
        await systemStore.fetchOptions(newVal)
        loading.value = false
    }
})
</script>
