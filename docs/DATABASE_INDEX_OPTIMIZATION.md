# 数据库性能优化索引指南

## 概述

本文档提供了 LH Contract Management System 数据库的性能优化索引脚本。这些索引将显著提升报表查询、列表分页和按日期筛选的性能。

## 执行方式

### 方法1：进入数据库容器执行

```bash
# 1. 进入 PostgreSQL 容器
docker exec -it lh_contract_db psql -U lh_admin -d lh_contract_db

# 2. 粘贴下方 SQL 脚本并执行
```

### 方法2：通过 Docker 直接执行

将下方 SQL 脚本保存为文件（如 `indexes.sql`），然后执行：

```bash
docker exec -i lh_contract_db psql -U lh_admin -d lh_contract_db < indexes.sql
```

---

## SQL 索引脚本

```sql
-- ============================================================================
-- Performance Indexes for LH Contract Management System
-- 性能优化索引脚本
-- 创建日期: 2025-12-23
-- ============================================================================

-- =====================
-- 上游合同表索引
-- =====================

-- 签订日期索引 (用于报表按日期筛选)
CREATE INDEX IF NOT EXISTS idx_contracts_upstream_sign_date 
    ON contracts_upstream(sign_date);

-- 复合索引: 状态 + 签订日期 (用于报表统计)
CREATE INDEX IF NOT EXISTS idx_contracts_upstream_status_sign_date 
    ON contracts_upstream(status, sign_date);

-- 复合索引: 甲方 + 状态 (用于按甲方筛选)
CREATE INDEX IF NOT EXISTS idx_contracts_upstream_party_a_status 
    ON contracts_upstream(party_a_name, status);

-- 合同金额索引 (用于金额排序和范围查询)
CREATE INDEX IF NOT EXISTS idx_contracts_upstream_amount 
    ON contracts_upstream(contract_amount);


-- =====================
-- 下游合同表索引
-- =====================

-- 签订日期索引
CREATE INDEX IF NOT EXISTS idx_contracts_downstream_sign_date 
    ON contracts_downstream(sign_date);

-- 复合索引: 状态 + 签订日期
CREATE INDEX IF NOT EXISTS idx_contracts_downstream_status_sign_date 
    ON contracts_downstream(status, sign_date);

-- 复合索引: 上游合同ID + 状态 (用于关联查询)
CREATE INDEX IF NOT EXISTS idx_contracts_downstream_upstream_status 
    ON contracts_downstream(upstream_contract_id, status);


-- =====================
-- 管理合同表索引
-- =====================

-- 签订日期索引
CREATE INDEX IF NOT EXISTS idx_contracts_management_sign_date 
    ON contracts_management(sign_date);

-- 复合索引: 状态 + 签订日期
CREATE INDEX IF NOT EXISTS idx_contracts_management_status_sign_date 
    ON contracts_management(status, sign_date);


-- =====================
-- 上游财务记录索引
-- =====================

-- 应收款日期索引
CREATE INDEX IF NOT EXISTS idx_finance_upstream_receivables_expected_date 
    ON finance_upstream_receivables(expected_date);

-- 开票日期索引
CREATE INDEX IF NOT EXISTS idx_finance_upstream_invoices_invoice_date 
    ON finance_upstream_invoices(invoice_date);

-- 复合索引: 合同ID + 开票日期 (用于合同内发票查询)
CREATE INDEX IF NOT EXISTS idx_finance_upstream_invoices_contract_date 
    ON finance_upstream_invoices(contract_id, invoice_date);

-- 收款日期索引
CREATE INDEX IF NOT EXISTS idx_finance_upstream_receipts_receipt_date 
    ON finance_upstream_receipts(receipt_date);

-- 复合索引: 合同ID + 收款日期
CREATE INDEX IF NOT EXISTS idx_finance_upstream_receipts_contract_date 
    ON finance_upstream_receipts(contract_id, receipt_date);

-- 结算日期索引
CREATE INDEX IF NOT EXISTS idx_project_settlements_settlement_date 
    ON project_settlements(settlement_date);


-- =====================
-- 下游财务记录索引
-- =====================

-- 应付款日期索引
CREATE INDEX IF NOT EXISTS idx_finance_downstream_payables_expected_date 
    ON finance_downstream_payables(expected_date);

-- 收票日期索引
CREATE INDEX IF NOT EXISTS idx_finance_downstream_invoices_invoice_date 
    ON finance_downstream_invoices(invoice_date);

-- 付款日期索引
CREATE INDEX IF NOT EXISTS idx_finance_downstream_payments_payment_date 
    ON finance_downstream_payments(payment_date);

-- 复合索引: 合同ID + 付款日期
CREATE INDEX IF NOT EXISTS idx_finance_downstream_payments_contract_date 
    ON finance_downstream_payments(contract_id, payment_date);

-- 下游结算日期索引
CREATE INDEX IF NOT EXISTS idx_downstream_settlements_settlement_date 
    ON downstream_settlements(settlement_date);


-- =====================
-- 费用表索引
-- =====================

-- 费用日期索引
CREATE INDEX IF NOT EXISTS idx_expenses_expense_date 
    ON expenses(expense_date);

-- 复合索引: 类别 + 费用日期 (用于费用分类报表)
CREATE INDEX IF NOT EXISTS idx_expenses_category_date 
    ON expenses(category, expense_date);


-- =====================
-- 零星用工表索引
-- =====================

CREATE INDEX IF NOT EXISTS idx_zero_hour_labor_work_date 
    ON zero_hour_labor(work_date);

CREATE INDEX IF NOT EXISTS idx_zero_hour_labor_project 
    ON zero_hour_labor(project_name);


-- =====================
-- 审计日志表索引
-- =====================

-- 操作时间索引 (用于按时间查询日志)
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at 
    ON audit_logs(created_at);

-- 复合索引: 资源类型 + 操作时间
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_time 
    ON audit_logs(resource_type, created_at);

-- 复合索引: 用户ID + 操作时间
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_time 
    ON audit_logs(user_id, created_at);


-- =====================
-- 统计信息更新
-- =====================

-- 更新统计信息以优化查询计划
ANALYZE contracts_upstream;
ANALYZE contracts_downstream;
ANALYZE contracts_management;
ANALYZE finance_upstream_receivables;
ANALYZE finance_upstream_invoices;
ANALYZE finance_upstream_receipts;
ANALYZE project_settlements;
ANALYZE finance_downstream_payables;
ANALYZE finance_downstream_invoices;
ANALYZE finance_downstream_payments;
ANALYZE downstream_settlements;
ANALYZE expenses;
ANALYZE audit_logs;
```

---

## 验证索引

执行以下 SQL 查看已创建的索引：

```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
    AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
```

---

## 索引说明

### 单列索引

| 表名 | 字段 | 用途 |
|------|------|------|
| contracts_upstream | sign_date | 按签订日期筛选 |
| contracts_upstream | contract_amount | 按金额排序 |
| finance_upstream_receipts | receipt_date | 按收款日期筛选 |
| finance_downstream_payments | payment_date | 按付款日期筛选 |
| audit_logs | created_at | 按时间查询日志 |

### 复合索引

| 表名 | 字段组合 | 用途 |
|------|----------|------|
| contracts_upstream | (status, sign_date) | 按状态和日期筛选报表 |
| contracts_upstream | (party_a_name, status) | 按甲方筛选合同 |
| contracts_downstream | (upstream_contract_id, status) | 关联查询下游合同 |
| finance_upstream_invoices | (contract_id, invoice_date) | 查询合同内的发票 |
| audit_logs | (user_id, created_at) | 查询用户操作记录 |

---

## 性能影响

- **查询性能**: 预计提升 50%-80%（特别是报表和按日期筛选）
- **写入开销**: 索引会略微增加 INSERT/UPDATE 操作的时间（约 5%-10%）
- **存储空间**: 预计增加 10%-20% 的存储空间

---

## 注意事项

1. 在生产环境执行前，建议先在测试环境验证
2. `CREATE INDEX IF NOT EXISTS` 确保不会重复创建索引
3. 执行 `ANALYZE` 命令更新统计信息，帮助查询优化器选择最佳执行计划
4. 如果某些表不存在（如 `zero_hour_labor`），对应的 CREATE INDEX 会报错但不影响其他索引创建
