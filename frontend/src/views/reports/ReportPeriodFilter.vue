<template>
  <div class="report-period-filter filter-control--period">
    <el-date-picker
      v-if="periodType === 'monthly'"
      v-model="selection.month"
      class="period-month-picker"
      type="month"
      value-format="YYYY-MM"
      format="YYYY年MM月"
      placeholder="选择月份"
      :clearable="false"
    />
    <el-date-picker
      v-else-if="periodType === 'quarterly'"
      v-model="selection.quarterYear"
      class="period-year-picker"
      type="year"
      value-format="YYYY"
      format="YYYY年"
      placeholder="选择年份"
      :clearable="false"
    />
    <el-select
      v-if="periodType === 'quarterly'"
      v-model="selection.quarter"
      class="period-segment-select"
      aria-label="选择季度"
    >
      <el-option v-for="quarter in 4" :key="quarter" :label="`第${quarter}季度`" :value="quarter" />
    </el-select>
    <el-date-picker
      v-if="periodType === 'half_yearly'"
      v-model="selection.halfYear"
      class="period-year-picker"
      type="year"
      value-format="YYYY"
      format="YYYY年"
      placeholder="选择年份"
      :clearable="false"
    />
    <el-select
      v-if="periodType === 'half_yearly'"
      v-model="selection.half"
      class="period-segment-select"
      aria-label="选择半年度"
    >
      <el-option label="上半年" :value="1" />
      <el-option label="下半年" :value="2" />
    </el-select>
    <el-date-picker
      v-if="periodType === 'yearly'"
      v-model="selection.year"
      class="period-year-picker"
      type="year"
      value-format="YYYY"
      format="YYYY年"
      placeholder="选择年份"
      :clearable="false"
    />
  </div>
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
.report-period-filter {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  width: fit-content;
  max-width: 100%;
  min-width: 0;
  min-height: var(--workspace-control-height);
}

.period-month-picker {
  width: 180px;
}

.period-year-picker {
  width: 150px;
}

.period-segment-select {
  width: 132px;
}

.report-period-filter > .period-month-picker,
.report-period-filter > .period-year-picker,
.report-period-filter > .period-segment-select {
  height: var(--workspace-control-height);
  min-height: var(--workspace-control-height);
  align-self: flex-start;
}

.report-period-filter :deep(.el-input__wrapper),
.report-period-filter :deep(.el-select__wrapper) {
  height: var(--workspace-control-height);
  min-height: var(--workspace-control-height);
}

@media (max-width: 640px) {
  .report-period-filter {
    width: 100%;
  }

  .period-month-picker,
  .period-year-picker,
  .period-segment-select {
    flex: 1 1 0;
    width: auto;
    min-width: 0;
  }
}
</style>
