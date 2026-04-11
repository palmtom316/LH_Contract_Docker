<template>
  <section class="app-chart-panel">
    <header v-if="$slots.header || $slots.actions" class="app-chart-panel__header">
      <div class="app-chart-panel__title">
        <slot name="header" />
      </div>
      <div v-if="$slots.actions" class="app-chart-panel__actions">
        <slot name="actions" />
      </div>
    </header>
    <div class="app-chart-panel__body">
      <slot />
    </div>
  </section>
</template>

<style scoped lang="scss">
.app-chart-panel {
  display: grid;
  gap: 16px;
  min-width: 0;
  padding: 16px;
  border: 1px solid var(--workspace-panel-border);
  border-radius: var(--radius);
  background: var(--surface-panel);
  box-shadow: var(--workspace-panel-shadow);
}

.app-chart-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.app-chart-panel__title {
  min-width: 0;
  color: hsl(var(--foreground));
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.app-chart-panel__actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.app-chart-panel__body {
  min-width: 0;
}

@media (max-width: 768px) {
  .app-chart-panel__header {
    flex-direction: column;
    align-items: stretch;
  }

  .app-chart-panel__actions {
    justify-content: flex-start;
  }
}
</style>
