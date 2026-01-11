<template>
  <el-card shadow="hover" class="stat-card-modern" :style="{ background: color }">
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
    default: 'linear-gradient(135deg, #409EFF 0%, #36CFC9 100%)' // Default Blue
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
</script>

<style scoped lang="scss">
.stat-card-modern {
  border: none;
  border-radius: 12px;
  color: #fff;
  position: relative;
  overflow: hidden;
  height: 140px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 20px;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 20px -8px rgba(0, 0, 0, 0.2);
    
    .card-icon-bg {
      transform: scale(1.1) rotate(10deg);
      opacity: 0.25;
    }
  }

  .card-icon-bg {
    position: absolute;
    right: -20px;
    bottom: -20px;
    font-size: 100px;
    opacity: 0.15;
    pointer-events: none;
    transition: all 0.4s ease;
    
    .el-icon {
      color: #fff;
    }
  }

  :deep(.el-card__body) {
    padding: 20px;
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
      font-size: 16px;
      font-weight: 500;
      opacity: 0.9;
    }
    
    .icon-wrapper {
      background: rgba(255, 255, 255, 0.2);
      border-radius: 50%;
      padding: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .el-icon {
        font-size: 18px;
        color: #fff;
      }
    }
  }

  .card-modern-content {
    .amount {
      font-size: 26px; /* Slightly adjusted for fitting */
      margin: 10px 0 5px;
      font-weight: bold;
      line-height: 1.2;
      
      small {
        font-size: 14px;
        font-weight: normal;
        opacity: 0.8;
      }
    }
    
    .sub-info {
      font-size: 12px;
      opacity: 0.7;
    }
  }
}
</style>
