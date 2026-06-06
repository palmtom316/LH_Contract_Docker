<template>
  <div class="mobile-contract-list">
    <div class="mobile-contract-list__controls">
      <section class="mobile-contract-list__toolbar">
        <div class="mobile-contract-list__picker">
          <van-dropdown-menu>
            <van-dropdown-item v-model="contractType" :options="contractTypeOptions" @change="handleTypeChange" />
          </van-dropdown-menu>
        </div>
        <div class="mobile-contract-list__actions">
          <button
            v-if="canCreate"
            type="button"
            class="create-button"
            aria-label="新建合同"
            @click="showActionSheet = true"
          >
            <van-icon name="plus" size="18" />
            <span>新建</span>
          </button>
        </div>
      </section>

      <section class="mobile-contract-list__filters">
        <van-search
          v-model="queryParams.keyword"
          placeholder="搜索合同名称或编号"
          show-action
          @search="handleQuery"
          @cancel="resetQuery"
        />

        <van-tabs v-model:active="activeStatusTab" @change="handleTabChange">
          <van-tab title="全部" name="all" />
          <van-tab title="执行中" name="执行中" />
          <van-tab title="已完成" name="已完成" />
          <van-tab title="已终止" name="合同终止" />
        </van-tabs>
      </section>
    </div>

    <section class="mobile-contract-list__cards">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model:loading="listLoading"
          :finished="finished"
          finished-text="没有更多了"
          :immediate-check="false"
          @load="loadMore"
        >
          <van-cell-group inset v-for="contract in list" :key="contract.id" class="contract-card">
            <van-cell
              :title="contract.contract_name"
              :label="contract.contract_code"
              is-link
              @click="goToDetail(contract.id)"
            >
              <template #value>
                <van-tag
                  :type="getVantTagType(contract.status) as any"
                  class="status-tag"
                >
                  {{ contract.status }}
                </van-tag>
              </template>
            </van-cell>

            <van-cell>
              <template #title>
                <div class="contract-parties">
                  <div class="party-row">
                    <span class="label">甲方:</span>
                    <span class="value">{{ contract.party_a_name || '-' }}</span>
                  </div>
                  <div class="party-row">
                    <span class="label">乙方:</span>
                    <span class="value">{{ contract.party_b_name || '-' }}</span>
                  </div>
                </div>
              </template>
              <template #value>
                <div class="contract-amount">
                  <div class="amount">¥{{ formatMoney(contract.contract_amount) }}</div>
                  <div class="date">{{ formatDate(contract.sign_date) }}</div>
                </div>
              </template>
            </van-cell>
          </van-cell-group>

          <van-empty
            v-if="!listLoading && list.length === 0"
            description="暂无记录"
          />
        </van-list>
      </van-pull-refresh>
    </section>

    <van-action-sheet
      v-model:show="showActionSheet"
      :actions="createActions"
      cancel-text="取消"
      @select="onCreateSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import dayjs from 'dayjs';
import { showToast } from 'vant';
import * as upstreamApi from '@/api/contractUpstream';
import * as downstreamApi from '@/api/contractDownstream';
import * as managementApi from '@/api/contractManagement';
import { useUserStore } from '@/stores/user';
import { formatMoney } from '@/utils/common';
import type { ContractItem, PaginatedResponse } from '@/types/api';

import {
  DropdownMenu as VanDropdownMenu,
  DropdownItem as VanDropdownItem,
  Icon as VanIcon,
  Search as VanSearch,
  Tabs as VanTabs,
  Tab as VanTab,
  PullRefresh as VanPullRefresh,
  List as VanList,
  Cell as VanCell,
  CellGroup as VanCellGroup,
  Tag as VanTag,
  Empty as VanEmpty,
  ActionSheet as VanActionSheet,
} from 'vant';

const router = useRouter();
const userStore = useUserStore();

// State
const contractType = ref('upstream'); // upstream, downstream, management
const contractTypeOptions = [
  { text: '上游合同', value: 'upstream' },
  { text: '下游合同', value: 'downstream' },
  { text: '管理合同', value: 'management' },
];

const activeStatusTab = ref('all');
const refreshing = ref(false);
const listLoading = ref(false);
const finished = ref(false);
const showActionSheet = ref(false);
const list = ref<ContractItem[]>([]);
const total = ref(0);

const queryParams = reactive({
  page: 1,
  page_size: 10,
  keyword: '',
  status: ''
});

// Computed API based on type
const currentApi = computed(() => {
  switch (contractType.value) {
    case 'upstream': return upstreamApi;
    case 'downstream': return downstreamApi;
    case 'management': return managementApi;
    default: return upstreamApi;
  }
});

// Check permission
const canCreate = computed(() => {
  switch (contractType.value) {
    case 'upstream': return userStore.canManageUpstreamContracts;
    case 'downstream': return userStore.canManageDownstreamContracts;
    case 'management': return userStore.canManageManagementContracts;
    default: return false;
  }
});

// 新建合同操作
const createActions = computed(() => {
    // Show only the action for the current type to keep it simple, or keep all?
    // Let's keep it simple: "New [Current Type] Contract"
    const labelMap = {
        'upstream': '新建上游合同',
        'downstream': '新建下游合同',
        'management': '新建管理合同'
    };
    return [{ name: labelMap[contractType.value], value: contractType.value }];
});

// Map contract status to Vant tag types
const getVantTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    '执行中': 'primary',
    '已完成': 'success',
    '合同终止': 'danger',
    '合同中止': 'warning',
    '草稿': 'default',
  };
  return typeMap[status] || 'default';
};

// 格式化日期
const formatDate = (date: string | null) => {
  if (!date) return '-';
  return dayjs(date).format('YYYY-MM-DD');
};

// Fetch Data
const getList = async (isLoadMore = false) => {
  if (!isLoadMore) {
    listLoading.value = true; // Show loading for initial fetch/refresh
  }

  try {
    const api = currentApi.value;
    const res = await api.getContracts(queryParams) as unknown as PaginatedResponse<ContractItem>;
    const newItems = res.items || [];

    if (isLoadMore) {
        list.value = [...list.value, ...newItems];
    } else {
        list.value = newItems;
    }
    
    total.value = res.total || 0;

    if (list.value.length >= total.value) {
        finished.value = true;
    } else {
        finished.value = false;
    }
  } catch (e) {
    showToast('加载失败');
    if (isLoadMore) {
        queryParams.page -= 1; // Revert if load more failed
        finished.value = true; // Stop infinite load loop on error
    }
  } finally {
    listLoading.value = false;
    refreshing.value = false;
  }
};

// Type Change
const handleTypeChange = () => {
    resetQuery(false); // Reset params, don't auto fetch yet
    getList(); // Fetch new type
};

// Search
const handleQuery = () => {
    queryParams.page = 1;
    finished.value = false;
    getList();
};

const resetQuery = (fetch = true) => {
    queryParams.keyword = '';
    queryParams.status = '';
    activeStatusTab.value = 'all';
    queryParams.page = 1;
    finished.value = false;
    if (fetch) getList();
};

// Tab Change
const handleTabChange = (name: string) => {
  queryParams.status = name === 'all' ? '' : name;
  queryParams.page = 1;
  finished.value = false;
  getList();
};

// Pull Refresh
const onRefresh = () => {
  queryParams.page = 1;
  finished.value = false;
  getList();
};

// Infinite Scroll
const loadMore = () => {
  if (listLoading.value || finished.value) return;
  queryParams.page += 1;
  getList(true);
};

// Go to Detail
const goToDetail = (id: number) => {
  router.push(`/contracts/${contractType.value}/${id}`);
};

// Create
const onCreateSelect = (action: { value: string }) => {
  router.push(`/contracts/${action.value}/new`);
  showActionSheet.value = false;
};

onMounted(() => {
  getList();
});
</script>

<style scoped>
.mobile-contract-list {
  display: grid;
  gap: 14px;
}

.mobile-contract-list__controls {
  position: sticky;
  top: 0;
  z-index: 4;
  display: grid;
  gap: 14px;
}

.mobile-contract-list__toolbar,
.mobile-contract-list__filters,
.mobile-contract-list__cards {
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  background: var(--surface-panel);
  box-shadow: var(--shadow-soft);
}

.mobile-contract-list__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px;
}

.mobile-contract-list__picker {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 6px;
}

.mobile-contract-list__actions {
  flex-shrink: 0;
}

.mobile-contract-list__filters {
  overflow: hidden;
}

.mobile-contract-list__cards {
  padding: 12px;
}

.contract-card {
  margin: 0 0 12px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: none;
}

.mobile-contract-list__cards :deep(.van-list) {
  display: grid;
  gap: 12px;
}

.mobile-contract-list__cards :deep(.van-cell-group--inset) {
  margin: 0;
  background: var(--surface-panel);
}

.mobile-contract-list__cards :deep(.van-cell) {
  padding: 14px 16px;
}

.contract-parties {
  font-size: 13px;
  color: var(--text-secondary);
}

.party-row {
  display: flex;
  margin-bottom: 4px;
}

.party-row .label {
  color: var(--text-muted);
  margin-right: 4px;
  flex-shrink: 0;
}

.party-row .value {
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contract-amount {
  text-align: right;
}

.contract-amount .amount {
  font-size: 16px;
  font-weight: 600;
  color: var(--brand-primary);
}

.contract-amount .date {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.status-tag {
  margin-left: 8px;
}

.create-button {
  min-height: 42px;
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  background: color-mix(in srgb, var(--text-primary) 92%, transparent);
  color: var(--text-inverse);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 14px;
  cursor: pointer;
  font-weight: 600;
}

:deep(.van-dropdown-menu__bar) {
    background-color: transparent;
    box-shadow: none;
    height: 40px;
}

:deep(.van-dropdown-menu__title) {
    font-weight: 600;
    font-size: 15px;
    color: var(--text-primary);
}

:deep(.van-search) {
    background: transparent;
}

:deep(.van-search__content) {
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    background: var(--surface-panel);
}

:deep(.van-tabs__wrap) {
    padding: 0 12px 10px;
}

:deep(.van-tabs__line) {
    background: var(--brand-primary);
}

@media (min-width: 768px) {
  .mobile-contract-list__controls {
    grid-template-columns: minmax(0, 1fr) minmax(280px, 0.92fr);
    align-items: start;
  }

  .mobile-contract-list__cards :deep(.van-list) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 420px) {
  .mobile-contract-list__toolbar {
    flex-wrap: wrap;
  }

  .mobile-contract-list__actions,
  .create-button {
    width: 100%;
  }

  .mobile-contract-list__cards :deep(.van-cell__value) {
    min-width: 96px;
  }

  .contract-amount {
    display: grid;
    gap: 4px;
    text-align: left;
  }

  .party-row {
    display: grid;
    gap: 2px;
  }
}
</style>
