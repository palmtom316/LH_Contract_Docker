<template>
  <section class="app-workspace-panel" :class="panelClass">
    <slot />
  </section>
</template>

<script setup>
defineProps({
  panelClass: {
    type: [String, Array, Object],
    default: ''
  }
})
</script>

<style scoped lang="scss">
.app-workspace-panel {
  display: grid;
  gap: 18px;
  min-width: 0;
  padding: var(--workspace-panel-padding);
  border: 1px solid var(--workspace-panel-border);
  border-radius: var(--workspace-panel-radius);
  background: var(--workspace-panel-background);
  box-shadow: var(--workspace-panel-shadow);
}
</style>
