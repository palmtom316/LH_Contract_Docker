<template>
  <header class="app-page-header">
    <div class="app-page-header__copy">
      <p v-if="eyebrow" class="app-page-header__eyebrow">{{ eyebrow }}</p>
      <h1 class="app-page-header__title">{{ title }}</h1>
      <p v-if="description" class="app-page-header__description">{{ description }}</p>
    </div>
    <div v-if="meta || $slots.actions" class="app-page-header__side">
      <div v-if="meta" class="app-page-header__meta">{{ meta }}</div>
      <div v-if="$slots.actions" class="app-page-header__actions">
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
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: var(--workspace-panel-padding);
  border: 1px solid var(--workspace-panel-border);
  border-radius: var(--workspace-panel-radius);
  background: var(--workspace-panel-background);
  box-shadow: var(--workspace-panel-shadow);
}

.app-page-header__copy {
  min-width: 0;
  display: grid;
  gap: 8px;
}

.app-page-header__eyebrow {
  margin: 0;
  font-size: 12px;
  line-height: 1.4;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.app-page-header__title {
  margin: 0;
  font-size: clamp(28px, 3.4vw, 36px);
  line-height: 1.04;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--text-primary);
}

.app-page-header__description {
  margin: 0;
  max-width: var(--workspace-copy-width);
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.app-page-header__side {
  display: grid;
  justify-items: end;
  align-content: start;
  gap: 10px;
  flex-shrink: 0;
}

.app-page-header__meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-height: 24px;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.5;
  text-align: right;
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
    padding: 20px;
    flex-direction: column;
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
  .app-page-header {
    padding: 18px;
    border-radius: 20px;
  }

  .app-page-header__title {
    font-size: 26px;
  }
}
</style>
