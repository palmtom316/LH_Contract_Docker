<template>
  <div class="zero-hour-detail">
    <AppWorkspacePanel v-if="detail" panel-class="detail-region detail-region--summary"
      ><AppPageHeader
        title="零星用工详情"
        description="基本信息、成本构成与独立财务明细"
      >
        <template #actions>
          <el-button plain @click="returnToList">返回列表</el-button>
        </template>
      </AppPageHeader>
      <el-row :gutter="20" class="summary-cards">
        <el-col :span="6" :xs="12"><StatCard title="应付款" :value="detail.payable_total" icon="Money" tone="warning" /></el-col>
        <el-col :span="6" :xs="12"><StatCard title="已挂账" :value="detail.invoiced_total" icon="Tickets" tone="accent" /></el-col>
        <el-col :span="6" :xs="12"><StatCard title="已付款" :value="detail.paid_total" icon="Wallet" tone="success" /></el-col>
        <el-col :span="6" :xs="12"><StatCard title="未付款" :value="detail.unpaid_total" icon="Money" tone="danger" /></el-col>
      </el-row>
    </AppWorkspacePanel><AppWorkspacePanel v-if="detail"
      ><el-descriptions border :column="isMobile ? 1 : 2"
        ><el-descriptions-item label="用工日期">{{
          detail.labor.labor_date
        }}</el-descriptions-item
        ><el-descriptions-item label="派工单位">{{
          detail.labor.dispatch_unit || "-"
        }}</el-descriptions-item
        ><el-descriptions-item label="归属">{{
          detail.labor.attribution === "PROJECT" ? "项目用工" : "公司用工"
        }}</el-descriptions-item
        ><el-descriptions-item label="关联合同">{{
          detail.labor.upstream_contract?.contract_name || "-"
        }}</el-descriptions-item
        ><el-descriptions-item label="说明">{{
          detail.labor.description || "-"
        }}</el-descriptions-item
        ><el-descriptions-item label="审批状态">{{
          detail.labor.approval_status || "-"
        }}</el-descriptions-item
        ><el-descriptions-item label="审批文件"
          ><el-button
            v-if="detail.labor.approval_pdf_key"
            link
            type="primary"
            @click="viewFile(detail.labor.approval_pdf_key)"
            >查看审批文件</el-button
          ><span v-else>-</span></el-descriptions-item
        ><el-descriptions-item label="零星用工总金额"
          >¥ {{ formatMoney(detail.labor.total_amount) }}</el-descriptions-item
        ></el-descriptions
      >
      <section class="amount-detail">
        <div class="section-heading"><h2>金额明细</h2><span>含税总额 ¥ {{ formatMoney(detail.labor.total_amount) }}</span></div>
        <el-table :data="amountRows" border>
          <el-table-column prop="item" label="项目" min-width="150" />
          <el-table-column prop="unit" label="单位" width="100" />
          <el-table-column prop="quantity" label="数量" width="110" align="right" />
          <el-table-column prop="unitPrice" label="单价" width="130" align="right"><template #default="{ row }">¥ {{ formatMoney(row.unitPrice) }}</template></el-table-column>
          <el-table-column prop="amount" label="金额" width="140" align="right"><template #default="{ row }">¥ {{ formatMoney(row.amount) }}</template></el-table-column>
        </el-table>
        <div class="tax-summary">税金：¥ {{ formatMoney(detail.labor.tax_amount) }}</div>
      </section>
      <el-tabs v-model="tab"
        ><el-tab-pane
          v-for="meta in sections"
          :key="meta.kind"
          :label="meta.label"
          :name="meta.kind"
          ><div class="table-toolbar">
            <el-button type="primary" plain @click="edit(meta.kind)"
              >新增{{ meta.singular }}</el-button
            >
          </div>
          <el-table :data="detail[meta.kind]" border
            ><el-table-column
              v-for="column in meta.columns"
              :key="column.prop"
              :prop="column.prop"
              :label="column.label"
              ><template v-if="column.prop === 'file_key'" #default="{ row }"
                ><el-button
                  v-if="row.file_key"
                  link
                  type="primary"
                  @click="viewFile(row.file_key)"
                  >查看文件</el-button
                ><span v-else>-</span></template
              ></el-table-column
            ><el-table-column label="操作" width="130"
              ><template #default="{ row }"
                ><el-button link type="primary" @click="edit(meta.kind, row)"
                  >编辑</el-button
                ><el-button link type="danger" @click="remove(meta.kind, row)"
                  >删除</el-button
                ></template
              ></el-table-column
            ></el-table
          ></el-tab-pane
        ></el-tabs
      ></AppWorkspacePanel
    ><el-dialog
      v-model="dialog"
      :title="form.id ? '编辑财务明细' : '新增财务明细'"
      width="520px"
      append-to-body
      ><el-form ref="financeFormRef" :model="form" :rules="financeRules" label-width="90px"
        ><el-form-item
          v-for="field in currentFields"
          :key="field.key"
          :label="field.label"
          :prop="field.key"
          ><el-autocomplete
            v-if="field.key === 'supplier'"
            v-model="form[field.key]"
            :fetch-suggestions="searchSuppliers"
            clearable
            placeholder="输入下游合同供应商"
            style="width: 100%"
          /><el-select
            v-else-if="field.key === 'payment_method'"
            v-model="form[field.key]"
            clearable
            placeholder="请选择付款方式"
            style="width: 100%"
          ><el-option label="银行转账" value="银行转账" /><el-option label="支票" value="支票" /><el-option label="现金" value="现金" /></el-select><el-date-picker
            v-else-if="field.type === 'date'"
            v-model="form[field.key]"
            value-format="YYYY-MM-DD"
            style="width: 100%" /><el-input-number
            v-else-if="field.type === 'number'"
            v-model="form[field.key]"
            :min="field.key === 'amount' ? 0.01 : 0"
            :precision="2"
            :controls="false"
            style="width: 100%" /><el-input
            v-else
            v-model="form[field.key]" /></el-form-item
        ><el-form-item label="附件/凭证"
          ><el-upload
            :auto-upload="false"
            :show-file-list="false"
            :on-change="uploadAttachment"
            ><el-button :loading="uploading">{{
              form.file_key ? "替换文件" : "选择文件"
            }}</el-button></el-upload
          ><span v-if="form.file_key" class="file-ready"
            >已上传</span
          ></el-form-item
        ></el-form
      ><template #footer
        ><el-button @click="dialog = false">取消</el-button
        ><el-button type="primary" @click="save">保存</el-button></template
      ></el-dialog
    >
  </div>
</template>
<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  createZeroHourFinance,
  deleteZeroHourFinance,
  fetchZeroHourFinanceFile,
  getZeroHourLaborDetail,
  searchZeroHourSuppliers,
  updateZeroHourFinance,
} from "@/api/zeroHourLabor";
import { uploadFile } from "@/api/common";
import AppPageHeader from "@/components/ui/AppPageHeader.vue";
import AppWorkspacePanel from "@/components/ui/AppWorkspacePanel.vue";
import StatCard from "@/components/StatCard.vue";
import { formatMoney } from "@/utils/common";
const route = useRoute(),
  router = useRouter(),
  detail = ref(null),
  tab = ref("payables"),
  dialog = ref(false),
  kind = ref("payables"),
  uploading = ref(false),
  financeFormRef = ref(null),
  isMobile = window.innerWidth < 768,
  form = reactive({});
const sections = [
  {
    kind: "payables",
    label: "应付款",
    singular: "应付款",
    columns: [
      { prop: "expected_date", label: "日期" },
      { prop: "amount", label: "金额" },
      { prop: "file_key", label: "审批附件" },
    ],
  },
  {
    kind: "invoices",
    label: "挂账",
    singular: "挂账",
    columns: [
      { prop: "invoice_number", label: "发票号码" },
      { prop: "invoice_date", label: "日期" },
      { prop: "supplier", label: "供应商" },
      { prop: "amount", label: "金额" },
      { prop: "status", label: "状态" },
      { prop: "file_key", label: "来源文件" },
    ],
  },
  {
    kind: "payments",
    label: "付款",
    singular: "付款",
    columns: [
      { prop: "payment_date", label: "付款日期" },
      { prop: "payee_name", label: "收款方" },
      { prop: "payment_method", label: "方式" },
      { prop: "amount", label: "金额" },
      { prop: "status", label: "状态" },
      { prop: "file_key", label: "凭证" },
    ],
  },
];
const fields = {
  payables: [
    ["expected_date", "日期", "date"],
    ["amount", "金额", "number"],
    ["description", "说明"],
  ],
  invoices: [
    ["invoice_number", "发票号码"],
    ["invoice_date", "挂账日期", "date"],
    ["supplier", "供应商"],
    ["amount", "金额", "number"],
    ["tax_amount", "税额", "number"],
  ],
  payments: [
    ["payment_date", "付款日期", "date"],
    ["payee_name", "收款方"],
    ["payee_account", "账号"],
    ["payee_bank", "银行"],
    ["payment_method", "付款方式"],
    ["amount", "金额", "number"],
  ],
};
const currentFields = computed(() =>
  (fields[kind.value] || []).map(([key, label, type = "text"]) => ({
    key,
    label,
    type,
  })),
);
const financeRules = {
  expected_date: [{ required: true, message: "请选择日期", trigger: "change" }],
  invoice_date: [{ required: true, message: "请选择日期", trigger: "change" }],
  payment_date: [{ required: true, message: "请选择日期", trigger: "change" }],
  amount: [{ required: true, message: "请输入金额", trigger: "blur" }],
  supplier: [{ required: true, message: "请输入供应商", trigger: "blur" }],
  payee_name: [{ required: true, message: "请输入收款方", trigger: "blur" }],
};
const amountRows = computed(() => {
  const labor = detail.value?.labor;
  if (!labor) return [];
  return [
    { item: "技工", unit: "工日", quantity: labor.skilled_quantity, unitPrice: labor.skilled_unit_price, amount: labor.skilled_price_total },
    { item: "普工", unit: "工日", quantity: labor.general_quantity, unitPrice: labor.general_unit_price, amount: labor.general_price_total },
    { item: "车辆", unit: "台班", quantity: labor.vehicle_quantity, unitPrice: labor.vehicle_unit_price, amount: labor.vehicle_price_total },
    ...(labor.materials || []).map((material) => ({
      item: material.material_name || "材料",
      unit: material.material_unit || "-",
      quantity: material.material_quantity,
      unitPrice: material.material_unit_price,
      amount: material.material_price_total,
    })),
  ];
});
const load = async () =>
  (detail.value = await getZeroHourLaborDetail(route.params.id));
onMounted(load);
const returnToList = () =>
  router.push({
    name: "Expenses",
    query: { ...route.query, tab: "zeroHourLabor" },
  });
const edit = (next, row = {}) => {
  kind.value = next;
  for (const key of Object.keys(form)) delete form[key];
  const labor = detail.value?.labor || {};
  Object.assign(form, row, {
    amount: row.id ? Number(row.amount || 0) : next === "payables" ? Number(labor.total_amount || 0) : 0,
    expected_date: row.expected_date || labor.labor_date,
    invoice_date: row.invoice_date || labor.labor_date,
    payment_date: row.payment_date || labor.labor_date,
    supplier: row.supplier || "",
    payee_name: row.payee_name || labor.dispatch_unit || "",
  });
  dialog.value = true;
};
const searchSuppliers = async (queryString, callback) => {
  if (!queryString?.trim()) return callback([]);
  try {
    const names = await searchZeroHourSuppliers(queryString.trim());
    callback(names.map((value) => ({ value })));
  } catch {
    callback([]);
  }
};
const uploadAttachment = async (file) => {
  uploading.value = true;
  try {
    const result = await uploadFile(file.raw, {
      uploadDir: "expenses",
      subdir: `zero-hour-labor/${route.params.id}`,
    });
    form.file_path = result.path;
    form.file_key = result.key;
    ElMessage.success("文件已上传");
  } finally {
    uploading.value = false;
  }
};
const viewFile = async (key) => {
  const win = window.open("about:blank", "_blank");
  if (!win) {
    ElMessage.error("请允许本站弹出窗口");
    return;
  }
  try {
    const blob = await fetchZeroHourFinanceFile(key);
    const url = URL.createObjectURL(blob);
    win.opener = null;
    win.location.replace(url);
    window.setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (error) {
    win.close();
    throw error;
  }
};
const save = async () => {
  if (!(await financeFormRef.value?.validate().catch(() => false))) return;
  const payload = {
    file_path: form.file_path || null,
    file_key: form.file_key || null,
  };
  for (const field of currentFields.value) {
    const value = form[field.key];
    payload[field.key] = value === "" || value === undefined ? null : value;
  }
  if (form.id)
    await updateZeroHourFinance(route.params.id, kind.value, form.id, payload);
  else await createZeroHourFinance(route.params.id, kind.value, payload);
  ElMessage.success("财务明细已保存");
  dialog.value = false;
  await load();
};
const remove = async (next, row) => {
  try {
    await ElMessageBox.confirm("确定删除该财务明细？", "删除确认", {
      type: "warning",
    });
    await deleteZeroHourFinance(route.params.id, next, row.id);
    ElMessage.success("财务明细已删除");
    await load();
  } catch {}
};
</script>
<style scoped>
.summary-cards {
  margin-top: 20px;
}
.amount-detail {
  margin: 24px 0;
}
.section-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}
.section-heading h2 {
  margin: 0;
  font-size: 16px;
}
.section-heading span,
.tax-summary {
  color: var(--text-secondary);
  font-size: 13px;
}
.tax-summary {
  padding-top: 12px;
  text-align: right;
}
.table-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}
.file-ready {
  margin-left: 10px;
  color: var(--el-color-success);
  font-size: 13px;
}
</style>
