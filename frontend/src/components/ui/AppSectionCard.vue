<template>
  <el-card class="app-section-card" shadow="never">
    <template v-if="$slots.header || $slots.actions" #header>
      <div class="app-section-card__header">
        <div class="app-section-card__title">
          <slot name="header" />
        </div>
        <div v-if="$slots.actions" class="app-section-card__actions">
          <slot name="actions" />
        </div>
      </div>
    </template>
    <slot />
  </el-card>
</template>

<style scoped lang="scss">
.app-section-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.app-section-card__title {
  min-width: 0;
  color: var(--text-primary);
}

.app-section-card__actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .app-section-card__header {
    flex-direction: column;
  }

  .app-section-card__actions {
    justify-content: flex-start;
  }
}
</style>
