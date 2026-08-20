<template>
  <div class="wh-scan">
    <p>先扫物资码，再扫货位码。扫货位后自动带出所属库房，提交前仍需确认项目和数量。</p>
    <van-notice-bar v-if="pendingMaterialId" :title="`已识别物资 #${pendingMaterialId}，请继续扫描货位码`" />
    <video v-if="supported" ref="videoRef" class="wh-scan__video" playsinline muted autoplay />
    <van-button v-if="supported" block type="primary" @click="start">打开摄像头扫码</van-button>
    <van-notice-bar v-else title="当前浏览器不支持扫码，请改用物资搜索。" />
    <van-search v-model="keyword" placeholder="手工搜索物资" @search="search" />
    <van-cell-group inset>
      <van-cell
        v-for="item in materials"
        :key="item.id"
        :title="`${item.code} ${item.name}`"
        :label="`${item.specification} / ${item.supply_type}`"
        is-link
        @click="goInbound(item.id)"
      />
    </van-cell-group>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showFailToast } from 'vant'
import { Button as VanButton, Cell as VanCell, CellGroup as VanCellGroup, NoticeBar as VanNoticeBar, Search as VanSearch } from 'vant'
import { listMaterials } from '@/api/warehouse'

const router = useRouter()
const supported = ref(typeof window !== 'undefined' && 'BarcodeDetector' in window && navigator.mediaDevices)
const videoRef = ref(null)
const keyword = ref('')
const materials = ref([])
const pendingMaterialId = ref(Number(new URLSearchParams(window.location.search).get('material_id') || 0) || null)
let stream = null
let timer = null

async function start() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    if (videoRef.value) videoRef.value.srcObject = stream
    const detector = new window.BarcodeDetector({ formats: ['qr_code'] })
    timer = window.setInterval(async () => {
      if (!videoRef.value) return
      const codes = await detector.detect(videoRef.value)
      const raw = codes[0]?.rawValue
      if (!raw) return
      const match = String(raw).match(/(materials|locations)\/(\d+)/)
      if (match) {
        stop()
        if (match[1] === 'materials') {
          pendingMaterialId.value = Number(match[2])
          return
        }
        if (!pendingMaterialId.value) {
          showFailToast('请先扫描物资码')
          return
        }
        stop()
        router.push({ path: '/m/warehouse/inbound', query: { location_id: Number(match[2]), material_id: pendingMaterialId.value } })
      }
    }, 600)
  } catch {
    showFailToast('无法使用摄像头，请改为手工搜索')
  }
}

function stop() {
  if (timer) window.clearInterval(timer)
  stream?.getTracks().forEach(track => track.stop())
}

async function search() {
  materials.value = await listMaterials({ q: keyword.value })
}

function goInbound(id) {
  pendingMaterialId.value = id
}

onBeforeUnmount(stop)
</script>

<style scoped>
.wh-scan { display: grid; gap: 12px; }
.wh-scan__video {
  width: 100%;
  min-height: 180px;
  background: #111;
  border-radius: var(--radius);
}
.wh-scan :deep(.van-button) { min-height: 44px; }
</style>
