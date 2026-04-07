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
  gap: 16px;
  min-width: 0;
}
</style>
