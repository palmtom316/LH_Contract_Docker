<template>
  <section class="app-empty-state">
    <div class="app-empty-state__icon">
      <slot name="icon">+</slot>
    </div>
    <h3 class="app-empty-state__title">{{ title }}</h3>
    <p v-if="description" class="app-empty-state__description">{{ description }}</p>
    <div v-if="$slots.actions" class="app-empty-state__actions">
      <slot name="actions" />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '暂无数据'
  },
  description: {
    type: String,
    default: ''
  }
})
</script>

<style scoped lang="scss">
.app-empty-state {
  display: grid;
  justify-items: center;
  gap: 12px;
  padding: 32px 20px;
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-md);
  background: var(--surface-panel-muted);
  text-align: center;
}

.app-empty-state__icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  font-size: 22px;
  color: var(--brand-primary);
  background: var(--brand-primary-soft);
}

.app-empty-state__title {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.app-empty-state__description {
  margin: 0;
  max-width: 420px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.app-empty-state__actions {
  display: inline-flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}
</style>
