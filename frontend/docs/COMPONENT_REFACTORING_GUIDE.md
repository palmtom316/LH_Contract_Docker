# 前端组件重构指南

## 📋 重构目标

提升代码可维护性、复用性和可测试性

---

## 🎯 识别需要重构的组件

### 大型组件识别标准

组件需要重构如果存在以下问题：
- ✅ 文件超过500行
- ✅ template部分超过200行
- ✅ 包含多个职责
- ✅ 难以理解和维护
- ✅ 重复代码多

### 当前项目中的大型组件

根据审核，以下组件可能需要拆分：

1. **UpstreamDetail.vue** (估计 800-1000行)
   - 合同基本信息
   - 财务记录表格
   - 结算信息
   - 文件上传
   - 操作按钮

2. **DownstreamDetail.vue** (估计 700-900行)
   - 类似结构过于庞大

3. **ManagementDetail.vue** (估计 700-900行)
   - 重复逻辑过多

---

## 🔨 重构策略

### 策略1: 按功能拆分组件

**原则**: 一个组件只负责一个功能模块

#### UpstreamDetail.vue 重构方案

**重构前** (单文件):
```
UpstreamDetail.vue (1000 lines)
├── 基本信息表单 (200 lines)
├── 财务记录Tab (300 lines)
├── 结算信息 (150 lines)
├── 文件管理 (150 lines)
└── 操作按钮 (100 lines)
```

**重构后** (5个组件):
```
frontend/src/views/contracts/
├── UpstreamDetail.vue (200 lines) - 主组件，负责布局
│
frontend/src/components/contracts/
├── ContractBasicInfo.vue (150 lines) - 基本信息
├── ContractFinanceTabs.vue (200 lines) - 财务Tab容器
│   ├── ReceivableTable.vue (共用)
│   ├── InvoiceTable.vue (共用)
│   └── ReceiptTable.vue (共用)
├── ContractSettlement.vue (120 lines) - 结算信息
├── ContractFileManager.vue (100 lines) - 文件管理
└── ContractActions.vue (80 lines) - 操作按钮
```

---

### 策略2: 提取可复用组件

#### 示例1: ContractBasicInfo.vue

```vue
<!-- frontend/src/components/contracts/ContractBasicInfo.vue -->
<template>
  <el-card class="contract-basic-info">
    <template #header>
      <div class="card-header">
        <span>基本信息</span>
        <el-button 
          v-if="editable" 
          type="primary" 
          size="small"
          @click="emit('edit')"
        >
          编辑
        </el-button>
      </div>
    </template>

    <el-descriptions :column="2" border>
      <el-descriptions-item label="合同编号">
        {{ contract.contract_code }}
      </el-descriptions-item>
      
      <el-descriptions-item label="合同名称">
        {{ contract.contract_name }}
      </el-descriptions-item>
      
      <el-descriptions-item label="甲方单位">
        {{ contract.party_a_name }}
      </el-descriptions-item>
      
      <el-descriptions-item label="乙方单位">
        {{ contract.party_b_name }}
      </el-descriptions-item>
      
      <el-descriptions-item label="合同金额">
        <span class="amount">
          {{ formatCurrency(contract.contract_amount) }}
        </span>
      </el-descriptions-item>
      
      <el-descriptions-item label="签约日期">
        {{ formatDate(contract.sign_date) }}
      </el-descriptions-item>
    </el-descriptions>
  </el-card>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  contract: {
    type: Object,
    required: true
  },
  editable: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['edit'])

const formatCurrency = (amount) => {
  return `¥${Number(amount).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.contract-basic-info {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.amount {
  color: #409eff;
  font-weight: bold;
  font-size: 16px;
}
</style>
```

#### 示例2: ContractActions.vue

```vue
<!-- frontend/src/components/contracts/ContractActions.vue -->
<template>
  <div class="contract-actions">
    <el-button-group>
      <el-button 
        v-if="canEdit"
        type="primary"
        :icon="Edit"
        @click="emit('edit')"
      >
        编辑
      </el-button>
      
      <el-button 
        v-if="canDelete"
        type="danger"
        :icon="Delete"
        @click="handleDelete"
      >
        删除
      </el-button>
      
      <el-button 
        :icon="Download"
        @click="emit('export')"
      >
        导出
      </el-button>
      
      <el-button 
        :icon="Printer"
        @click="emit('print')"
      >
        打印
      </el-button>
    </el-button-group>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'
import { ElMessageBox } from 'element-plus'
import { Edit, Delete, Download, Printer } from '@element-plus/icons-vue'

const props = defineProps({
  canEdit: {
    type: Boolean,
    default: false
  },
  canDelete: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['edit', 'delete', 'export', 'print'])

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除此合同吗？删除后无法恢复。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    emit('delete')
  } catch {
    // User cancelled
  }
}
</script>

<style scoped>
.contract-actions {
  margin-top: 20px;
  text-align: right;
}
</style>
```

---

### 策略3: 使用组合式API提取逻辑

#### 示例: useContractForm.js

```javascript
// frontend/src/composables/useContractForm.js
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { createContract, updateContract } from '@/api/contracts'

export function useContractForm(initialData = null) {
  const formData = ref(initialData || {
    contract_code: '',
    contract_name: '',
    party_a_name: '',
    party_b_name: '',
    contract_amount: 0,
    sign_date: null,
    // ... other fields
  })

  const loading = ref(false)
  const errors = ref({})

  const isValid = computed(() => {
    return formData.value.contract_code && 
           formData.value.contract_name &&
           formData.value.contract_amount > 0
  })

  const validateForm = () => {
    errors.value = {}
    
    if (!formData.value.contract_code) {
      errors.value.contract_code = '合同编号不能为空'
    }
    
    if (!formData.value.contract_name) {
      errors.value.contract_name = '合同名称不能为空'
    }
    
    if (formData.value.contract_amount <= 0) {
      errors.value.contract_amount = '合同金额必须大于0'
    }
    
    return Object.keys(errors.value).length === 0
  }

  const submitForm = async () => {
    if (!validateForm()) {
      ElMessage.error('请检查表单数据')
      return false
    }

    loading.value = true
    try {
      const apiCall = formData.value.id ? updateContract : createContract
      const result = await apiCall(formData.value)
      
      ElMessage.success(
        formData.value.id ? '更新成功' : '创建成功'
      )
      
      return result
    } catch (error) {
      ElMessage.error(error.message || '操作失败')
      return false
    } finally {
      loading.value = false
    }
  }

  const resetForm = () => {
    formData.value = initialData || {}
    errors.value = {}
  }

  return {
    formData,
    loading,
    errors,
    isValid,
    validateForm,
    submitForm,
    resetForm
  }
}
```

**使用示例**:
```vue
<script setup>
import { useContractForm } from '@/composables/useContractForm'

const contract = ref(null) // 从API获取

const {
  formData,
  loading,
  errors,
  isValid,
  submitForm,
  resetForm
} = useContractForm(contract.value)

const handleSubmit = async () => {
  const result = await submitForm()
  if (result) {
    // 成功处理
  }
}
</script>
```

---

## 📁 推荐目录结构

```
frontend/src/
├── components/
│   ├── contracts/              # 合同相关组件
│   │   ├── ContractBasicInfo.vue
│   │   ├── ContractFinanceTabs.vue
│   │   ├── ContractSettlement.vue
│   │   ├── ContractFileManager.vue
│   │   ├── ContractActions.vue
│   │   └── tables/             # 表格组件
│   │       ├── ReceivableTable.vue
│   │       ├── InvoiceTable.vue
│   │       └── ReceiptTable.vue
│   │
│   └── common/                 # 通用组件
│       ├── PageHeader.vue
│       ├── SearchBar.vue
│       └── DataTable.vue
│
├── composables/                # 组合式函数
│   ├── useContractForm.js
│   ├── useTablePagination.js
│   ├── useFileUpload.js
│   └── usePermissions.js
│
└── views/
    └── contracts/
        ├── UpstreamDetail.vue  # 简化后的主组件
        ├── DownstreamDetail.vue
        └── ManagementDetail.vue
```

---

## ✅ 重构检查清单

在重构每个组件时，确保：

- [ ] 组件单一职责
- [ ] Props类型定义完整
- [ ] Emits事件清晰
- [ ] 样式使用scoped
- [ ] 逻辑提取到composables
- [ ] 添加注释说明
- [ ] 性能优化(v-memo, computed)
- [ ] 错误处理完善

---

## 🎯 重构优先级

### 高优先级 (立即)
1. ✅ 提取ContractBasicInfo组件
2. ✅ 提取ContractActions组件
3. ✅ 创建useContractForm composable

### 中优先级 (本周)
4. 拆分UpstreamDetail.vue
5. 复用组件到Downstream和Management
6. 统一表单验证逻辑

### 低优先级 (下周)
7. 提取通用Table组件
8. 优化移动端适配
9. 添加组件单元测试

---

## 📊 重构效果预期

**代码质量提升**:
- 组件平均行数: 1000行 → **200行** (-80%)
- 代码复用率: 30% → **70%** (+133%)
- 可维护性: +60%
- 测试覆盖率: 0% → **50%** (新组件)

**开发效率**:
- 新功能开发时间: -40%
- Bug修复时间: -50%
- 代码Review时间: -60%

---

## 💡 最佳实践

1. **渐进式重构**: 不要一次性重构所有组件
2. **保持向后兼容**: 重构时确保现有功能正常
3. **编写测试**: 重构前后都要测试
4. **代码审查**: 重构代码需要团队审查
5. **文档更新**: 更新组件使用文档

---

## 🔗 相关资源

- Vue 3 组合式API文档
- Element Plus 组件库
- Vite 性能优化指南
- 前端代码规范

---

**重构是持续的过程，从最关键的部分开始，逐步改进！**
