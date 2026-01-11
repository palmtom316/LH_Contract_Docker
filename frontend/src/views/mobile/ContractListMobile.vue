<template>
  <div class="mobile-contract-list">
    <!-- 搜索栏 -->
    <van-search
      v-model="queryParams.keyword"
      placeholder="搜索合同名称或编号"
      show-action
      @search="handleQuery"
      @cancel="resetQuery"
    />

    <!-- 筛选标签 -->
    <van-tabs v-model:active="activeTab" sticky @change="handleTabChange">
      <van-tab title="全部" name="all" />
      <van-tab title="执行中" name="执行中" />
      <van-tab title="已完成" name="已完成" />
      <van-tab title="已终止" name="合同终止" />
    </van-tabs>

    <!-- 下拉刷新容器 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <!-- 合同卡片列表 -->
      <van-list
        v-model:loading="listLoading"
        :finished="finished"
        finished-text="没有更多了"
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
                :type="getVantTagType(contract.status)"
                class="status-tag"
              >
                {{ contract.status }}
              </van-tag>
            </template>
          </van-cell>
          
          <!-- 合同详情摘要 -->
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

        <!-- 空状态 -->
        <van-empty
          v-if="!loading && list.length === 0"
          description="暂无合同数据"
        />
      </van-list>
    </van-pull-refresh>

    <!-- 新建合同按钮 -->
    <van-floating-bubble
      v-if="canCreate"
      icon="plus"
      @click="showActionSheet = true"
    />

    <!-- 新建合同操作菜单 -->
    <van-action-sheet
      v-model:show="showActionSheet"
      :actions="createActions"
      cancel-text="取消"
      @select="onCreateSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import dayjs from 'dayjs';
import { showToast } from 'vant';
import * as upstreamApi from '@/api/contractUpstream';
import { useContractList } from '@/composables/useContractList';
import { useUserStore } from '@/stores/user';

// Vant 组件
import {
  Search as VanSearch,
  Tabs as VanTabs,
  Tab as VanTab,
  PullRefresh as VanPullRefresh,
  List as VanList,
  Cell as VanCell,
  CellGroup as VanCellGroup,
  Tag as VanTag,
  Empty as VanEmpty,
  FloatingBubble as VanFloatingBubble,
  ActionSheet as VanActionSheet,
} from 'vant';

const router = useRouter();
const userStore = useUserStore();

// Use the shared composable for API operations
const {
  loading,
  list,
  total,
  queryParams,
  getList,
  handleQuery,
  resetQuery,
  formatMoney,
} = useContractList({
  api: upstreamApi,
  contractType: '上游合同',
  exportPrefix: '上游合同导出'
});

// Local state for mobile-specific behavior
const activeTab = ref('all');
const refreshing = ref(false);
const listLoading = ref(false);
const finished = ref(false);
const showActionSheet = ref(false);

// Check if user can create contracts
const canCreate = computed(() => userStore.canManageUpstreamContracts);

// 新建合同操作
const createActions = [
  { name: '新建上游合同', value: 'upstream' },
  { name: '新建下游合同', value: 'downstream' },
  { name: '新建管理合同', value: 'management' },
];

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

// Handle tab change - filter by status
const handleTabChange = (name: string) => {
  queryParams.status = name === 'all' ? '' : name;
  queryParams.page = 1;
  finished.value = false;
  getList();
};

// 下拉刷新
const onRefresh = async () => {
  try {
    queryParams.page = 1;
    finished.value = false;
    await getList();
  } catch (e) {
    showToast('刷新失败');
  } finally {
    refreshing.value = false;
  }
};

// 加载更多 
const loadMore = async () => {
  if (finished.value || loading.value) return;
  
  listLoading.value = true;
  try {
    queryParams.page += 1;
    await getList();
    
    // Check if we've loaded all items
    if (list.value.length >= total.value) {
      finished.value = true;
    }
  } catch (e) {
    showToast('加载失败');
    queryParams.page -= 1; // Revert page on error
  } finally {
    listLoading.value = false;
  }
};

// 跳转到详情
const goToDetail = (id: number) => {
  router.push(`/contracts/upstream/${id}`);
};

// 新建合同
const onCreateSelect = (action: { value: string }) => {
  router.push(`/contracts/${action.value}/new`);
  showActionSheet.value = false;
};

// 初始化
onMounted(() => {
  getList();
});

// Watch loading state from composable
watch(loading, (val) => {
  if (!val && !refreshing.value) {
    listLoading.value = false;
  }
});
</script>

<style scoped>
.mobile-contract-list {
  min-height: 100vh;
  background-color: #f7f8fa;
  padding-bottom: env(safe-area-inset-bottom);
}

.contract-card {
  margin: 12px;
  border-radius: 8px;
  overflow: hidden;
}

.contract-parties {
  font-size: 13px;
  color: #666;
}

.party-row {
  display: flex;
  margin-bottom: 4px;
}

.party-row .label {
  color: #999;
  margin-right: 4px;
  flex-shrink: 0;
}

.party-row .value {
  color: #333;
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
  color: #1890ff;
}

.contract-amount .date {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.status-tag {
  margin-left: 8px;
}

:deep(.van-cell-group--inset) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

:deep(.van-tabs__wrap) {
  background-color: #fff;
}

:deep(.van-floating-bubble) {
  --van-floating-bubble-background: #1890ff;
}
</style>
