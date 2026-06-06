<template>
  <section class="app-empty-state rounded-xl border border-dashed border-border bg-muted/40">
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
  padding: 28px 20px;
  text-align: center;
}

.app-empty-state__icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 18px;
  color: hsl(var(--primary));
  background: hsl(var(--primary) / 0.08);
}

.app-empty-state__title {
  margin: 0;
  font-size: 16px;
  color: hsl(var(--foreground));
}

.app-empty-state__description {
  margin: 0;
  max-width: 420px;
  font-size: 13px;
  line-height: 1.5;
  color: hsl(var(--muted-foreground));
}

.app-empty-state__actions {
  display: inline-flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}
</style>
