<template>
  <header class="app-page-header border-b border-border pb-3">
    <div class="app-page-header__copy">
      <h1 class="text-lg font-semibold tracking-tight text-foreground">{{ title }}</h1>
    </div>
    <div v-if="$slots.actions" class="app-page-header__side">
      <div class="app-page-header__actions">
        <slot name="actions" />
      </div>
    </div>
  </header>
</template>

<script setup>
defineProps({
  eyebrow: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  },
  meta: {
    type: String,
    default: ''
  }
})
</script>

<style scoped lang="scss">
.app-page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.app-page-header__copy {
  min-width: 0;
}

.app-page-header__side {
  display: grid;
  justify-items: end;
  align-content: start;
  gap: 10px;
  flex-shrink: 0;
}

.app-page-header__actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .app-page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .app-page-header__side {
    width: 100%;
    justify-items: start;
  }

  .app-page-header__meta,
  .app-page-header__actions {
    justify-content: flex-start;
    text-align: left;
  }
}

@media (max-width: 640px) {
  .app-page-header__actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
