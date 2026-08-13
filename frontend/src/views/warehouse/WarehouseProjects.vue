<template>
  <div class="warehouse-page">
    <WarehouseNav />
    <AppWorkspacePanel>
      <AppSectionCard>
        <template #header>项目档案</template>
        <template #actions>
          <el-button v-if="userStore.canManageWarehouseMaster" type="primary" @click="openCreate">新建项目</el-button>
        </template>
        <AppFilterBar>
          <el-input v-model="query" placeholder="合同序号 / 合同名称 / 甲方" clearable @keyup.enter="load" />
          <template #actions>
            <el-button type="primary" @click="load">搜索</el-button>
          </template>
        </AppFilterBar>
        <AppDataTable>
          <el-table v-loading="loading" :data="items" border>
            <el-table-column prop="code" label="合同序号" width="120" />
            <el-table-column prop="name" label="合同名称" min-width="240" show-overflow-tooltip />
            <el-table-column prop="company_category" label="公司合同分类" min-width="140" />
            <el-table-column prop="party_a_name" label="甲方" min-width="180" show-overflow-tooltip />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">{{ row.is_active ? '启用' : '停用' }}</template>
            </el-table-column>
          </el-table>
        </AppDataTable>
      </AppSectionCard>
    </AppWorkspacePanel>
    <el-dialog v-model="visible" title="新建项目" width="560px" append-to-body>
      <el-form :model="form" label-width="112px">
        <el-form-item label="合同序号">
          <el-input
            v-model="form.code"
            placeholder="输入上游合同序号后回车或失焦自动带出"
            clearable
            @blur="lookupBySerial"
            @keyup.enter="lookupBySerial"
          />
        </el-form-item>
        <el-form-item label="合同名称">
          <el-autocomplete
            v-model="form.name"
            :fetch-suggestions="searchNames"
            placeholder="输入合同名称模糊匹配"
            value-key="contract_name"
            clearable
            style="width: 100%"
            @select="applyContract"
          >
            <template #default="{ item }">
              <div class="contract-option">
                <strong>{{ item.serial_number || '-' }} {{ item.contract_name }}</strong>
                <small>{{ item.party_a_name || '' }}</small>
              </div>
            </template>
          </el-autocomplete>
        </el-form-item>
        <el-form-item label="公司合同分类">
          <el-input v-model="form.company_category" readonly placeholder="选择合同后自动填报" />
        </el-form-item>
        <el-form-item label="甲方">
          <el-input v-model="form.party_a_name" readonly placeholder="选择合同后自动填报" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" :disabled="!form.upstream_contract_id" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createProject, listProjects, searchUpstreamContracts } from '@/api/warehouse'
import { useUserStore } from '@/stores/user'
import WarehouseNav from './WarehouseNav.vue'

const userStore = useUserStore()
const items = ref([])
const visible = ref(false)
const saving = ref(false)
const loading = ref(false)
const query = ref('')
const form = reactive({
  code: '',
  name: '',
  upstream_contract_id: null,
  company_category: '',
  party_a_name: ''
})

function resetForm() {
  form.code = ''
  form.name = ''
  form.upstream_contract_id = null
  form.company_category = ''
  form.party_a_name = ''
}

function applyContract(contract) {
  if (!contract) return
  form.upstream_contract_id = contract.id
  form.code = contract.serial_number == null ? '' : String(contract.serial_number)
  form.name = contract.contract_name || ''
  form.company_category = contract.company_category || ''
  form.party_a_name = contract.party_a_name || ''
}

async function lookupBySerial() {
  const serial = String(form.code || '').trim()
  if (!serial) return
  const rows = await searchUpstreamContracts(
    /^\d+$/.test(serial) ? { serial_number: Number(serial) } : { q: serial }
  )
  if (!rows.length) {
    form.upstream_contract_id = null
    form.company_category = ''
    form.party_a_name = ''
    ElMessage.warning('未找到该合同序号对应的上游合同')
    return
  }
  applyContract(rows[0])
}

async function searchNames(queryString, cb) {
  const keyword = (queryString || '').trim()
  if (!keyword) {
    cb([])
    return
  }
  try {
    const rows = await searchUpstreamContracts({ q: keyword })
    cb(rows)
  } catch {
    cb([])
  }
}

function openCreate() {
  resetForm()
  visible.value = true
}

async function load() {
  loading.value = true
  try {
    items.value = await listProjects({ include_inactive: true, q: query.value || undefined })
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!form.upstream_contract_id) {
    ElMessage.warning('请先用合同序号或合同名称匹配一份上游合同')
    return
  }
  saving.value = true
  try {
    await createProject({
      upstream_contract_id: form.upstream_contract_id,
      code: form.code,
      name: form.name
    })
    visible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
.warehouse-page { display: grid; gap: 16px; }

.contract-option {
  display: grid;
  gap: 2px;
}

.contract-option small {
  color: var(--text-muted);
}
</style>
