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
  gap: 12px;
  min-width: 0;
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
  border-radius: var(--radius);
  border: 1px solid var(--workspace-panel-border);
  background: var(--surface-panel);
  box-shadow: none;
}

.app-data-table__scroll :deep(.el-table) {
  min-width: 100%;
  --el-table-border-color: hsl(var(--border));
  --el-table-border: 1px solid hsl(var(--border));
  --el-table-header-bg-color: hsl(var(--muted));
  --el-table-row-hover-bg-color: hsl(var(--muted) / 0.65);
}

.app-data-table__scroll :deep(.el-table th.el-table__cell) {
  background: hsl(var(--muted));
  color: hsl(var(--muted-foreground));
  font-weight: 600;
}

@media (max-width: 767px) {
  .app-data-table__scroll :deep(.el-table) {
    min-width: 920px;
  }
}
</style>
