<template>
  <section class="app-section-card rounded-xl border border-border bg-card shadow-sm">
    <div v-if="$slots.header || $slots.actions" class="app-section-card__header">
      <div class="app-section-card__title">
        <slot name="header" />
      </div>
      <div v-if="$slots.actions" class="app-section-card__actions">
        <slot name="actions" />
      </div>
    </div>
    <slot />
  </section>
</template>

<style scoped lang="scss">
.app-section-card {
  display: grid;
  gap: 16px;
  padding: 16px;
  min-width: 0;
  position: relative;
  overflow: hidden;
  border-color: var(--workspace-panel-border);
  background: var(--surface-panel-elevated);
  box-shadow: var(--workspace-panel-shadow);
  transition: box-shadow 180ms ease, border-color 180ms ease;
}

.app-section-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.app-section-card__title {
  min-width: 0;
  color: hsl(var(--foreground));
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.app-section-card__actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .app-section-card__header {
    flex-direction: column;
    align-items: stretch;
  }

  .app-section-card__actions {
    justify-content: flex-start;
  }
}
</style>
