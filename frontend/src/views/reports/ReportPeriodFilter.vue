<template>
  <template v-if="periodType === 'monthly'">
    <el-date-picker
      v-model="selection.month"
      class="filter-control--time"
      type="month"
      value-format="YYYY-MM"
      format="YYYY年MM月"
      placeholder="选择月份"
      :clearable="false"
    />
  </template>
  <template v-else-if="periodType === 'quarterly'">
    <el-date-picker
      v-model="selection.quarterYear"
      class="filter-control--time period-year-picker"
      type="year"
      value-format="YYYY"
      format="YYYY年"
      placeholder="选择年份"
      :clearable="false"
    />
    <el-select v-model="selection.quarter" class="period-segment-select" aria-label="选择季度">
      <el-option v-for="quarter in 4" :key="quarter" :label="`第${quarter}季度`" :value="quarter" />
    </el-select>
  </template>
  <template v-else-if="periodType === 'half_yearly'">
    <el-date-picker
      v-model="selection.halfYear"
      class="filter-control--time period-year-picker"
      type="year"
      value-format="YYYY"
      format="YYYY年"
      placeholder="选择年份"
      :clearable="false"
    />
    <el-select v-model="selection.half" class="period-segment-select" aria-label="选择半年度">
      <el-option label="上半年" :value="1" />
      <el-option label="下半年" :value="2" />
    </el-select>
  </template>
  <template v-else>
    <el-date-picker
      v-model="selection.year"
      class="filter-control--time"
      type="year"
      value-format="YYYY"
      format="YYYY年"
      placeholder="选择年份"
      :clearable="false"
    />
  </template>
</template>

<script setup>
defineProps({
  periodType: {
    type: String,
    required: true
  },
  selection: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.period-year-picker {
  max-width: 150px;
}

.period-segment-select {
  width: 132px;
}
</style>
