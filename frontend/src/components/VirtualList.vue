<template>
  <div 
    ref="containerRef"
    class="virtual-list-container"
    :style="containerStyle"
    @scroll="handleScroll"
  >
    <!-- Spacer to create correct scrollbar -->
    <div :style="{ height: totalHeight + 'px' }">
      <!-- Visible items -->
      <div 
        class="virtual-list-content"
        :style="contentStyle"
      >
        <div
          v-for="item in visibleItems"
          :key="getItemKey(item)"
          class="virtual-list-item"
          :style="{ height: itemHeight + 'px' }"
        >
          <slot :item="item.data" :index="item.index"></slot>
        </div>
      </div>
    </div>
    
    <!-- Loading indicator -->
    <div v-if="loading" class="virtual-list-loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
    
    <!-- Empty state -->
    <div v-if="!loading && items.length === 0" class="virtual-list-empty">
      <slot name="empty">
        <el-empty description="暂无记录" />
      </slot>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Loading } from '@element-plus/icons-vue'

const props = defineProps({
  // Array of items to render
  items: {
    type: Array,
    required: true,
    default: () => []
  },
  // Height of each item in pixels
  itemHeight: {
    type: Number,
    default: 50
  },
  // Height of the container
  containerHeight: {
    type: [Number, String],
    default: 400
  },
  // Number of items to render outside visible area (buffer)
  buffer: {
    type: Number,
    default: 5
  },
  // Key field for item identification
  keyField: {
    type: String,
    default: 'id'
  },
  // Loading state
  loading: {
    type: Boolean,
    default: false
  },
  // Enable infinite scroll
  infiniteScroll: {
    type: Boolean,
    default: false
  },
  // Threshold for infinite scroll (pixels from bottom)
  infiniteScrollThreshold: {
    type: Number,
    default: 100
  }
})

const emit = defineEmits(['scroll', 'load-more', 'scroll-end'])

// Refs
const containerRef = ref(null)
const scrollTop = ref(0)

// Computed styles
const containerStyle = computed(() => ({
  height: typeof props.containerHeight === 'number' 
    ? `${props.containerHeight}px` 
    : props.containerHeight,
  overflow: 'auto',
  position: 'relative'
}))

// Total height of all items
const totalHeight = computed(() => props.items.length * props.itemHeight)

// Calculate visible range
const visibleRange = computed(() => {
  const containerH = typeof props.containerHeight === 'number' 
    ? props.containerHeight 
    : parseInt(props.containerHeight) || 400
  
  const start = Math.max(0, Math.floor(scrollTop.value / props.itemHeight) - props.buffer)
  const visibleCount = Math.ceil(containerH / props.itemHeight) + props.buffer * 2
  const end = Math.min(props.items.length, start + visibleCount)
  
  return { start, end }
})

// Visible items with their indices
const visibleItems = computed(() => {
  const { start, end } = visibleRange.value
  return props.items.slice(start, end).map((data, i) => ({
    data,
    index: start + i
  }))
})

// Position the content div
const contentStyle = computed(() => ({
  transform: `translateY(${visibleRange.value.start * props.itemHeight}px)`,
  position: 'relative'
}))

// Get unique key for item
const getItemKey = (item) => {
  return item.data[props.keyField] ?? item.index
}

// Handle scroll event
const handleScroll = (e) => {
  scrollTop.value = e.target.scrollTop
  emit('scroll', { scrollTop: scrollTop.value, scrollHeight: e.target.scrollHeight })
  
  // Check for infinite scroll
  if (props.infiniteScroll) {
    const { scrollHeight, clientHeight } = e.target
    const distanceFromBottom = scrollHeight - scrollTop.value - clientHeight
    
    if (distanceFromBottom < props.infiniteScrollThreshold) {
      emit('load-more')
    }
  }
  
  // Check if scrolled to end
  if (scrollTop.value + e.target.clientHeight >= e.target.scrollHeight - 1) {
    emit('scroll-end')
  }
}

// Scroll to specific index
const scrollToIndex = (index) => {
  if (containerRef.value) {
    const offset = index * props.itemHeight
    containerRef.value.scrollTop = offset
  }
}

// Scroll to top
const scrollToTop = () => {
  if (containerRef.value) {
    containerRef.value.scrollTop = 0
  }
}

// Scroll to bottom
const scrollToBottom = () => {
  if (containerRef.value) {
    containerRef.value.scrollTop = containerRef.value.scrollHeight
  }
}

// Watch for items change to reset scroll if needed
watch(() => props.items.length, (newLength, oldLength) => {
  if (newLength === 0) {
    scrollTop.value = 0
  }
})

// Expose methods
defineExpose({
  scrollToIndex,
  scrollToTop,
  scrollToBottom,
  getScrollTop: () => scrollTop.value
})
</script>

<style scoped>
.virtual-list-container {
  will-change: transform;
  -webkit-overflow-scrolling: touch;
}

.virtual-list-content {
  will-change: transform;
}

.virtual-list-item {
  box-sizing: border-box;
  overflow: hidden;
}

.virtual-list-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  gap: 8px;
  color: var(--text-muted);
}

.virtual-list-loading .is-loading {
  animation: rotating 1.5s linear infinite;
}

.virtual-list-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
