<template>
  <article class="app-metric-card">
    <div class="app-metric-card__head">
      <span class="app-metric-card__eyebrow">{{ eyebrow }}</span>
      <slot name="badge" />
    </div>
    <div class="app-metric-card__title">{{ title }}</div>
    <div class="app-metric-card__value">{{ value }}</div>
    <p v-if="description" class="app-metric-card__description">{{ description }}</p>
    <div v-if="$slots.footer" class="app-metric-card__footer">
      <slot name="footer" />
    </div>
  </article>
</template>

<script setup>
defineProps({
  eyebrow: {
    type: String,
    default: '核心指标'
  },
  title: {
    type: String,
    default: ''
  },
  value: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  }
})
</script>

<style scoped lang="scss">
.app-metric-card {
  display: grid;
  gap: 12px;
  min-height: 100%;
  min-width: 0;
  padding: 22px;
  border: 1px solid var(--border-subtle);
  border-radius: 22px;
  background:
    linear-gradient(180deg, var(--surface-panel), color-mix(in srgb, var(--surface-panel) 88%, var(--surface-panel-muted) 12%));
  box-shadow: var(--shadow-soft);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.app-metric-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-card);
}

.app-metric-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.app-metric-card__eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--text-muted);
}

.app-metric-card__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-secondary);
  line-height: 1.5;
}

.app-metric-card__value {
  font-size: clamp(24px, 4vw, 34px);
  line-height: 1.05;
  font-weight: 700;
  color: var(--text-primary);
  word-break: break-word;
}

.app-metric-card__description {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-secondary);
}

.app-metric-card__footer {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  color: var(--text-secondary);
}
</style>
