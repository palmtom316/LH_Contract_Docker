<template>
  <el-card shadow="never" class="stat-card-modern" :class="toneClass">
    <div class="card-icon-bg">
      <el-icon><component :is="icon" /></el-icon>
    </div>
    <div class="card-inner">
      <div class="card-modern-header">
        <span class="title">{{ title }}</span>
        <div class="icon-wrapper">
          <el-icon><component :is="icon" /></el-icon>
        </div>
      </div>
      <div class="card-modern-content">
        <h2 class="amount">
          <slot name="value">
            {{ formatValue(value) }} <small>{{ unit }}</small>
          </slot>
        </h2>
        <div class="sub-info" v-if="subInfo">{{ subInfo }}</div>
        <slot name="footer"></slot>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: [Number, String],
    default: 0
  },
  unit: {
    type: String,
    default: '' // Can be empty if value includes unit or is a count
  },
  icon: {
    type: String,
    default: 'Document'
  },
  color: {
    type: String,
    default: ''
  },
  tone: {
    type: String,
    default: 'default'
  },
  subInfo: {
    type: String,
    default: ''
  }
})

const formatValue = (val) => {
  if (val === undefined || val === null) return '0.00'
  return typeof val === 'number' ? val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : val
}

const toneClass = computed(() => `stat-card-modern--${props.tone}`)
</script>

<style scoped lang="scss">
.stat-card-modern {
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  color: var(--text-primary);
  position: relative;
  overflow: hidden;
  height: 136px;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease, transform 0.2s ease;
  margin-bottom: 12px;
  background: var(--surface-panel);
  
  &:hover {
    transform: translateY(-1px);
    border-color: color-mix(in srgb, var(--border-subtle) 55%, var(--brand-primary) 45%);
    
    .card-icon-bg {
      transform: scale(1.03);
      opacity: 1;
    }
  }

  .card-icon-bg {
    position: absolute;
    right: 16px;
    top: 16px;
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    opacity: 0.9;
    pointer-events: none;
    transition: transform 0.2s ease, opacity 0.2s ease;
    
    .el-icon {
      font-size: 18px;
      color: inherit;
    }
  }

  :deep(.el-card__body) {
    padding: 18px;
    height: 100%;
    box-sizing: border-box;
  }

  .card-inner {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
  }

  .card-modern-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .title {
      max-width: calc(100% - 52px);
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.01em;
      color: var(--text-secondary);
    }
    
    .icon-wrapper {
      display: none;
    }
  }

  .card-modern-content {
    .amount {
      font-size: 24px;
      margin: 10px 0 4px;
      font-weight: 700;
      line-height: 1.15;
      letter-spacing: -0.02em;
      
      small {
        font-size: 13px;
        font-weight: normal;
        color: var(--text-muted);
      }
    }
    
    .sub-info {
      font-size: 12px;
      color: var(--text-muted);
    }
  }
}

.stat-card-modern--default {
  background: var(--surface-panel);
}

.stat-card-modern--info {
  background: color-mix(in srgb, var(--surface-panel) 92%, var(--brand-primary) 8%);
}

.stat-card-modern--warning {
  background: color-mix(in srgb, var(--surface-panel) 92%, var(--status-warning) 8%);
}

.stat-card-modern--success {
  background: color-mix(in srgb, var(--surface-panel) 92%, var(--status-success) 8%);
}

.stat-card-modern--accent {
  background: color-mix(in srgb, var(--surface-panel) 92%, var(--status-info) 8%);
}

.stat-card-modern--danger {
  background: color-mix(in srgb, var(--surface-panel) 92%, var(--status-danger) 8%);
}

.stat-card-modern--info .card-icon-bg {
  background: color-mix(in srgb, var(--brand-primary) 12%, transparent);
  color: var(--brand-primary);
}

.stat-card-modern--warning .card-icon-bg {
  background: color-mix(in srgb, var(--status-warning) 14%, transparent);
  color: var(--status-warning);
}

.stat-card-modern--success .card-icon-bg {
  background: color-mix(in srgb, var(--status-success) 14%, transparent);
  color: var(--status-success);
}

.stat-card-modern--accent .card-icon-bg {
  background: color-mix(in srgb, var(--status-info) 14%, transparent);
  color: var(--status-info);
}

.stat-card-modern--danger .card-icon-bg {
  background: color-mix(in srgb, var(--status-danger) 14%, transparent);
  color: var(--status-danger);
}
</style>
