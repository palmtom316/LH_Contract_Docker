<template>
  <el-autocomplete
    v-model="innerValue"
    :fetch-suggestions="querySearchAsync"
    :placeholder="placeholder"
    :trigger-on-focus="false"
    clearable
    class="smart-input"
    @select="handleSelect"
  >
    <template #default="{ item }">
      <div class="name">{{ item.value }}</div>
    </template>
  </el-autocomplete>
</template>

<script setup>
import { ref, watch } from 'vue'
import { getCompanies } from '@/api/common'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请输入公司名称'
  }
})

const emit = defineEmits(['update:modelValue', 'select'])

const innerValue = ref(props.modelValue)

watch(() => props.modelValue, (val) => {
  innerValue.value = val
})

watch(innerValue, (val) => {
  emit('update:modelValue', val)
})

const querySearchAsync = async (queryString, cb) => {
  if (!queryString) {
    cb([])
    return
  }
  try {
    const results = await getCompanies(queryString)
    // API returns list of strings: ["Company A", "Company B"]
    // Element Plus autocomplete expects objects with 'value' property
    const suggestions = results.map(name => ({ value: name }))
    cb(suggestions)
  } catch (error) {
    console.error(error)
    cb([])
  }
}

const handleSelect = (item) => {
  emit('select', item)
}
</script>

<style scoped>
.smart-input {
  width: 100%;
}
</style>
