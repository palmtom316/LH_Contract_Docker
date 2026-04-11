<template>
  <header class="app-page-header border-b border-border/80 pb-4">
    <div class="app-page-header__copy">
      <p v-if="eyebrow" class="app-page-header__eyebrow">{{ eyebrow }}</p>
      <h1 class="text-lg font-semibold tracking-tight text-foreground">{{ title }}</h1>
      <p v-if="description" class="app-page-header__description">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="app-page-header__side">
      <p v-if="meta" class="app-page-header__meta">{{ meta }}</p>
      <div class="app-page-header__actions">
        <slot name="actions" />
      </div>
    </div>
    <p v-else-if="meta" class="app-page-header__meta app-page-header__meta--inline">{{ meta }}</p>
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
  display: grid;
  gap: 6px;
}

.app-page-header__eyebrow,
.app-page-header__description,
.app-page-header__meta {
  margin: 0;
}

.app-page-header__eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.app-page-header__description {
  max-width: min(72ch, 100%);
  font-size: 13px;
  line-height: 1.55;
  color: var(--text-secondary);
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

.app-page-header__meta {
  font-size: 12px;
  color: var(--text-muted);
}

.app-page-header__meta--inline {
  margin-left: auto;
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
