<template>
  <section class="app-filter-bar">
    <div class="app-filter-bar__main">
      <slot />
    </div>
    <div v-if="$slots.actions" class="app-filter-bar__actions">
      <slot name="actions" />
    </div>
  </section>
</template>

<style scoped lang="scss">
.app-filter-bar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-panel);
  box-shadow: var(--shadow-soft);
}

.app-filter-bar__main {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  flex: 1;
}

.app-filter-bar__actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .app-filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
