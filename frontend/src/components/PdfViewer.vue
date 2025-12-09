<template>
  <div class="pdf-viewer-container">
    <div class="toolbar">
      <el-button-group>
        <el-button icon="ZoomOut" @click="scale -= 0.1" :disabled="scale <= 0.5" />
        <el-button>{{ Math.round(scale * 100) }}%</el-button>
        <el-button icon="ZoomIn" @click="scale += 0.1" :disabled="scale >= 3" />
      </el-button-group>
      <el-button icon="Download" type="primary" link @click="download">下载</el-button>
    </div>
    
    <div class="pdf-content" :style="{ transform: `scale(${scale})`, transformOrigin: 'top center' }">
      <vue-pdf-embed :source="source" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import VuePdfEmbed from 'vue-pdf-embed'

const props = defineProps({
  source: {
    type: String,
    required: true
  }
})

const scale = ref(1.0)

const download = () => {
  window.open(props.source, '_blank')
}
</script>

<style scoped lang="scss">
.pdf-viewer-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  overflow: hidden;
  
  .toolbar {
    margin-bottom: 10px;
    z-index: 10;
    background: #fff;
    padding: 10px;
    position: sticky;
    top: 0;
    width: 100%;
    display: flex;
    justify-content: center;
    gap: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .pdf-content {
    flex: 1;
    overflow-y: auto;
    width: 100%;
    display: flex;
    justify-content: center;
    transition: transform 0.2s;
    padding-bottom: 50px;
  }
}
</style>
