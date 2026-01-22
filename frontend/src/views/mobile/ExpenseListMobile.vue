<template>
  <div class="mobile-expense-list">
    <!-- 顶部导航栏 -->
    <van-nav-bar fixed placeholder title="费用管理" z-index="100" />
      
    <!-- 选项卡切换 -->
    <van-tabs v-model:active="activeType" sticky offset-top="46" @change="handleTypeChange">
      <van-tab title="普通费用" name="ordinary" />
      <van-tab title="零星用工" name="labor" />
    </van-tabs>

    <!-- 搜索栏 -->
    <van-search
      v-model="queryParams.keyword"
      placeholder="搜索内容..."
      show-action
      @search="handleQuery"
      @cancel="resetQuery"
    />

    <!-- 内容列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
        v-model:loading="listLoading"
        :finished="finished"
        finished-text="没有更多了"
        :immediate-check="false"
        @load="loadMore"
      >
        <!-- 普通费用卡片 -->
        <template v-if="activeType === 'ordinary'">
            <van-cell-group inset v-for="item in list" :key="item.id" class="expense-card">
            <van-cell :title="item.expense_type" :label="item.project_name" >
                <template #value>
                <div class="amount-info">
                    <div class="amount">¥{{ formatMoney(item.amount) }}</div>
                    <van-tag :type="item.is_paid ? 'success' : 'warning'">{{ item.is_paid ? '已支付' : '未支付' }}</van-tag>
                </div>
                </template>
            </van-cell>
            <van-cell>
                <template #title>
                 <div class="detail-row">
                    <span>经办人: {{ item.handler_name }}</span>
                    <span>日期: {{ formatDate(item.expense_date) }}</span>
                 </div>
                 <div class="detail-row" v-if="item.notes">
                    <span class="notes">备注: {{ item.notes }}</span>
                 </div>
                </template>
            </van-cell>
            <van-cell v-if="item.attachments && item.attachments.length" title="附件" is-link @click="viewAttachments(item.attachments)">
                 <template #value>
                    {{ item.attachments.length }}个附件
                 </template>
            </van-cell>
            </van-cell-group>
        </template>

        <!-- 零星用工卡片 -->
        <template v-else>
             <van-cell-group inset v-for="item in list" :key="item.id" class="expense-card">
            <van-cell :title="item.worker_name" :label="item.job_content" >
                <template #value>
                <div class="amount-info">
                    <div class="amount">¥{{ formatMoney(item.amount) }}</div>
                     <div class="date">{{ formatDate(item.work_date) }}</div>
                </div>
                </template>
            </van-cell>
            <van-cell>
                <template #title>
                 <div class="detail-row">
                    <span>工时: {{ item.work_hours }}小时</span>
                    <span>单价: ¥{{ item.unit_price }}</span>
                 </div>
                 <div class="detail-row" v-if="item.notes">
                    <span class="notes">备注: {{ item.notes }}</span>
                 </div>
                </template>
            </van-cell>
            </van-cell-group>
        </template>

        <van-empty
          v-if="!listLoading && list.length === 0"
          description="暂无数据"
        />
      </van-list>
    </van-pull-refresh>

    <!-- 附件预览弹窗 (简化版，仅提示) -->
    <!-- 实际项目中可能需要图片预览组件 -->
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue';
import dayjs from 'dayjs';
import { showToast, showImagePreview } from 'vant';
import * as expenseApi from '@/api/expense';
import * as laborApi from '@/api/zeroHourLabor';
import { formatMoney, getFileUrl } from '@/utils/common';

// Vant Components
import {
  NavBar as VanNavBar,
  Tabs as VanTabs,
  Tab as VanTab,
  Search as VanSearch,
  PullRefresh as VanPullRefresh,
  List as VanList,
  Cell as VanCell,
  CellGroup as VanCellGroup,
  Tag as VanTag,
  Empty as VanEmpty,
} from 'vant';

// State
const activeType = ref('ordinary'); // ordinary, labor
const refreshing = ref(false);
const listLoading = ref(false);
const finished = ref(false);
const list = ref<any[]>([]);
const total = ref(0);

const queryParams = reactive({
  page: 1,
  page_size: 10,
  keyword: '',
  // Add specific filters if needed
});

// Helper
const formatDate = (date: string) => {
    return date ? dayjs(date).format('YYYY-MM-DD') : '-';
};

const viewAttachments = (attachments: string) => {
    if (!attachments) return;
    try {
        // Assume attachments is custom comma separated string or JSON? 
        // Backend usually returns comma separated paths or array. 
        // Let's assume array or string.
        let urls: string[] = [];
        if (Array.isArray(attachments)) {
             urls = attachments.map(path => getFileUrl(path));
        } else if (typeof attachments === 'string') {
             urls = attachments.split(',').map(path => getFileUrl(path));
        }
        
        if (urls.length > 0) {
            showImagePreview(urls);
        }
    } catch (e) {
        console.error(e);
        showToast('无法预览附件');
    }
}

// Data Fetching
const fetchList = async (isLoadMore = false) => {
    if (!isLoadMore) {
        listLoading.value = true;
    }

    try {
        let res;
        if (activeType.value === 'ordinary') {
            res = await expenseApi.getExpenses(queryParams);
        } else {
            res = await laborApi.getZeroHourLaborList(queryParams);
        }

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
        console.error(e);
        showToast('加载失败');
        if (isLoadMore) {
            queryParams.page--;
            finished.value = true;
        }
    } finally {
        listLoading.value = false;
        refreshing.value = false;
    }
};

const handleQuery = () => {
    queryParams.page = 1;
    finished.value = false;
    fetchList();
};

const resetQuery = () => {
    queryParams.keyword = '';
    handleQuery();
};

const handleTypeChange = () => {
    queryParams.page = 1;
    finished.value = false;
    list.value = [];
    queryParams.keyword = '';
    fetchList();
};

const onRefresh = () => {
    queryParams.page = 1;
    finished.value = false;
    fetchList();
};

const loadMore = () => {
    if (listLoading.value || finished.value) return;
    queryParams.page++;
    fetchList(true);
};

onMounted(() => {
    fetchList();
});

</script>

<style scoped>
.mobile-expense-list {
  min-height: 100vh;
  background-color: #f7f8fa;
  padding-bottom: env(safe-area-inset-bottom);
}

.expense-card {
  margin: 12px;
  border-radius: 8px;
  overflow: hidden;
}

.amount-info {
    text-align: right;
}

.amount {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.detail-row {
    font-size: 13px;
    color: #666;
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
}

.notes {
    color: #999;
    font-size: 12px;
}

.date {
  font-size: 12px;
  color: #999;
}
</style>
