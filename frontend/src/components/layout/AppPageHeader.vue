<template>
  <header class="app-page-header">
    <div class="app-page-header__copy">
      <h1 class="app-page-header__title">{{ title }}</h1>
      <p v-if="description" class="app-page-header__description">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="app-page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  }
})
</script>

<style scoped lang="scss">
.app-page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.app-page-header__copy {
  min-width: 0;
}

.app-page-header__title {
  margin: 0;
  font-size: clamp(24px, 3vw, 32px);
  line-height: 1.1;
  font-weight: 700;
  color: var(--text-primary);
}

.app-page-header__description {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.app-page-header__actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .app-page-header {
    flex-direction: column;
  }

  .app-page-header__actions {
    justify-content: flex-start;
  }
}
</style>
