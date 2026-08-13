<template>
  <div class="warehouse-page">
    <WarehouseNav />
    <AppWorkspacePanel>
      <AppSectionCard>
        <template #header>库房与货位</template>
        <template #actions>
          <el-button v-if="userStore.canManageWarehouseMaster" type="primary" @click="createVisible = true">新建库房</el-button>
        </template>
        <div v-for="item in items" :key="item.id" class="warehouse-card">
          <div class="warehouse-card__title">
            <strong>{{ item.name }}</strong>
            <span>{{ item.code }}</span>
            <el-tag size="small">{{ item.is_active ? '启用' : '停用' }}</el-tag>
          </div>
          <p>{{ item.address || '未填写地址' }} / 负责人 {{ item.manager_name || '-' }}</p>
          <div class="locations">
            <el-tag v-for="loc in item.locations" :key="loc.id" class="location-tag">
              {{ loc.name }} ({{ loc.code }})
            </el-tag>
          </div>
        </div>
      </AppSectionCard>
    </AppWorkspacePanel>
    <el-dialog v-model="createVisible" title="新建库房" width="480px" append-to-body>
      <el-form :model="form" label-width="88px">
        <el-form-item label="编码"><el-input v-model="form.code" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="负责人"><el-input v-model="form.manager_name" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createWarehouse, listWarehouses } from '@/api/warehouse'
import { useUserStore } from '@/stores/user'
import WarehouseNav from './WarehouseNav.vue'

const userStore = useUserStore()
const items = ref([])
const createVisible = ref(false)
const saving = ref(false)
const form = reactive({ code: '', name: '', address: '', manager_name: '' })

async function load() {
  items.value = await listWarehouses({ include_inactive: true })
}

async function save() {
  saving.value = true
  try {
    await createWarehouse(form)
    ElMessage.success('库房已创建，并自动建立暂存区')
    createVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
.warehouse-page { display: grid; gap: 16px; }
.warehouse-card {
  display: grid;
  gap: 8px;
  padding: 12px 0;
  border-bottom: 1px solid hsl(var(--border));
}
.warehouse-card__title {
  display: flex;
  gap: 10px;
  align-items: center;
}
.locations { display: flex; flex-wrap: wrap; gap: 8px; }
</style>
