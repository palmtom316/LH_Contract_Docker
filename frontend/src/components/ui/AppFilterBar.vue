<template>
  <section class="app-filter-bar">
    <div class="app-filter-bar__content">
      <div class="app-filter-bar__main">
        <slot />
        <div v-if="inlineActions && $slots.actions" class="app-filter-bar__actions app-filter-bar__actions--inline">
          <slot name="actions" />
        </div>
      </div>
      <div v-if="!inlineActions && $slots.actions" class="app-filter-bar__actions">
        <slot name="actions" />
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  inlineActions: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped lang="scss">
.app-filter-bar {
  position: relative;
  padding: 12px 14px;
  border: 1px solid color-mix(in srgb, var(--border-subtle) 78%, var(--brand-primary) 22%);
  border-radius: 18px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--surface-panel) 96%, white 4%), color-mix(in srgb, var(--surface-panel) 88%, var(--surface-panel-muted) 12%));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.6),
    0 8px 22px rgba(15, 23, 42, 0.04);
}

.app-filter-bar__content {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.app-filter-bar__main {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 12px;
  min-width: 0;
}

.app-filter-bar__main > * {
  grid-column: span 3;
  min-width: 0;
  max-width: none;
}

.app-filter-bar__main :deep(.el-input),
.app-filter-bar__main :deep(.el-select),
.app-filter-bar__main :deep(.el-date-editor),
.app-filter-bar__main :deep(.el-date-editor.el-input__wrapper),
.app-filter-bar__main :deep(.app-range-field) {
  width: 100%;
  max-width: none;
  min-width: 0;
}

.app-filter-bar__main :deep(.el-input) {
  min-width: 0;
}

.app-filter-bar__main :deep(.el-select),
.app-filter-bar__main :deep(.dict-select) {
  min-width: 0;
}

.app-filter-bar__main :deep(.filter-control--wide) {
  grid-column: span 4;
}

.app-filter-bar__main :deep(.filter-control--time) {
  grid-column: span 4;
  width: 100%;
  justify-self: stretch;
}

.app-filter-bar__main :deep(.filter-control--range-wide) {
  grid-column: span 5;
}

.app-filter-bar__main :deep(.app-range-field) {
  min-height: 44px;
}

.app-filter-bar__main :deep(.filter-control--search) {
  grid-column: span 5;
}

.app-filter-bar__main :deep(.filter-control--search .el-input__wrapper),
.app-filter-bar__main :deep(.filter-control--search.el-input__wrapper) {
  background: color-mix(in srgb, var(--surface-panel) 92%, white 8%);
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--border-subtle) 72%, var(--brand-primary) 28%) inset,
    0 8px 18px rgba(37, 99, 235, 0.06);
}

.app-filter-bar__main :deep(.filter-control--search .el-input__inner) {
  font-weight: 500;
}

.app-filter-bar__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
  padding-top: 2px;
}

.app-filter-bar__actions--inline {
  grid-column: span 4;
  padding-top: 0;
  justify-content: flex-start;
}

.app-filter-bar__actions :deep(.el-dropdown) {
  display: inline-flex;
}

.app-filter-bar__actions :deep(.el-button) {
  min-width: 0;
  height: 40px;
  padding-inline: 14px;
  white-space: nowrap;
}

@media (max-width: 1280px) {
  .app-filter-bar__main {
    grid-template-columns: repeat(8, minmax(0, 1fr));
  }

  .app-filter-bar__main :deep(.filter-control--search),
  .app-filter-bar__main :deep(.filter-control--time) {
    grid-column: span 3;
  }

  .app-filter-bar__actions--inline {
    grid-column: span 3;
  }

  .app-filter-bar__main :deep(.filter-control--range-wide) {
    grid-column: span 4;
  }
}

@media (max-width: 900px) {
  .app-filter-bar__main > * {
    grid-column: span 4;
  }

  .app-filter-bar__main :deep(.filter-control--wide) {
    grid-column: 1 / -1;
  }

  .app-filter-bar__main :deep(.filter-control--time),
  .app-filter-bar__main :deep(.filter-control--range-wide) {
    grid-column: 1 / -1;
  }

  .app-filter-bar__main :deep(.filter-control--search) {
    grid-column: 1 / -1;
  }

  .app-filter-bar__actions--inline {
    grid-column: 1 / -1;
  }
}

@media (max-width: 640px) {
  .app-filter-bar {
    padding: 12px;
    border-radius: 16px;
  }

  .app-filter-bar__content,
  .app-filter-bar__main {
    gap: 10px;
  }

  .app-filter-bar__main {
    grid-template-columns: 1fr;
  }

  .app-filter-bar__main > * {
    grid-column: 1 / -1;
  }

  .app-filter-bar__actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .app-filter-bar__actions :deep(.el-button),
  .app-filter-bar__actions :deep(.el-dropdown) {
    flex: 1 1 calc(50% - 5px);
  }

  .app-filter-bar__actions :deep(.el-button > span) {
    justify-content: center;
  }
}
</style>
