<template>
  <section class="app-workspace-panel">
    <slot />
  </section>
</template>

<style scoped lang="scss">
.app-workspace-panel {
  display: grid;
  gap: var(--workspace-shell-gap);
  padding: var(--workspace-panel-padding);
  border: 1px solid var(--workspace-panel-border);
  border-radius: var(--workspace-panel-radius);
  background: var(--workspace-panel-background);
  box-shadow: var(--workspace-panel-shadow);
}

@media (max-width: 768px) {
  .app-workspace-panel {
    padding: 20px;
  }
}

@media (max-width: 640px) {
  .app-workspace-panel {
    padding: 18px;
    border-radius: 20px;
  }
}
</style>
