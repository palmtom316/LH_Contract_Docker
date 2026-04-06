<template>
  <div class="app-data-table">
    <div v-if="$slots.toolbar" class="app-data-table__toolbar">
      <slot name="toolbar" />
    </div>
    <div class="app-data-table__scroll">
      <slot />
    </div>
    <div v-if="$slots.footer" class="app-data-table__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<style scoped lang="scss">
.app-data-table {
  display: grid;
  gap: 14px;
}

.app-data-table__toolbar,
.app-data-table__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.app-data-table__scroll {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
  border-radius: 16px;
  border: 1px solid var(--border-subtle);
  background: #fff;
  box-shadow: none;
}

.app-data-table__scroll :deep(.el-table) {
  min-width: 100%;
}

.app-data-table__scroll :deep(.el-table th.el-table__cell) {
  background: #f8fafc;
}

@media (max-width: 767px) {
  .app-data-table__scroll :deep(.el-table) {
    min-width: 920px;
  }
}
</style>
