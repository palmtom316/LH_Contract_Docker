<template>
  <div class="app-data-table">
    <div v-if="$slots.toolbar" class="app-data-table__toolbar">
      <slot name="toolbar" />
    </div>
    <el-table v-bind="$attrs" class="app-data-table__table">
      <slot />
    </el-table>
    <div v-if="$slots.footer" class="app-data-table__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
defineOptions({
  inheritAttrs: false
})
</script>

<style scoped lang="scss">
.app-data-table {
  display: grid;
  gap: 12px;
}

.app-data-table__toolbar,
.app-data-table__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.app-data-table__table {
  width: 100%;
}
</style>
