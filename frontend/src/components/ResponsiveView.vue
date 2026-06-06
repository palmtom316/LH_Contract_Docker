<template>
  <!-- PC 端: Element Plus 视图 -->
  <component 
    v-if="isDesktop" 
    :is="desktopComponent" 
    v-bind="$attrs"
  />
  
  <!-- 移动端: Vant UI 视图 -->
  <component 
    v-else 
    :is="mobileComponent" 
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
import { defineAsyncComponent, type Component } from 'vue';
import { useDevice } from '@/composables/useDevice';

interface Props {
  /**
   * PC 端组件路径 (相对于 views 目录)
   * 例如: 'contracts/ContractList.vue'
   */
  desktopView: string;
  
  /**
   * 移动端组件路径 (相对于 views/mobile 目录)
   * 例如: 'ContractListMobile.vue'
   */
  mobileView: string;
}

const props = defineProps<Props>();
const { isDesktop } = useDevice();

// 动态导入组件
const desktopComponent = defineAsyncComponent(
  () => import(`@/views/${props.desktopView}`)
) as Component;

const mobileComponent = defineAsyncComponent(
  () => import(`@/views/mobile/${props.mobileView}`)
) as Component;
</script>

<script lang="ts">
export default {
  name: 'ResponsiveView',
  inheritAttrs: false,
};
</script>
