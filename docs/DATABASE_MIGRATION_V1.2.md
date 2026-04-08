# V1.2 完整数据库迁移指南

**适用版本**: V1.1.x → V1.2  
**创建日期**: 2025-12-24  
**重要性**: ⚠️ **必须执行**

---

## 概述

V1.2 版本包含以下数据库结构变更：
1. **零星用工表** (`zero_hour_labor`) 新增字段
2. **零星用工材料表** (`zero_hour_labor_materials`) 新表
3. **系统字典表** (`sys_dictionaries`) 新表
4. **系统配置表** (`sys_config`) 新表
5. **枚举类型迁移** - 从 PostgreSQL ENUM 转为 VARCHAR

---

## 执行方式

### 方法 1: 直接在数据库容器中执行

```bash
# SSH 连接到服务器
ssh root@192.168.72.101

# 进入项目目录
cd /path/to/LH_Contract_Docker

# 连接到数据库
docker exec -it lh_contract_db psql -U lh_admin -d lh_contract_db
```

然后粘贴下方"完整迁移 SQL"部分的内容。

### 方法 2: 通过文件执行

```bash
# 将下面的 SQL 保存为 migrate_v1_2.sql
docker exec -i lh_contract_db psql -U lh_admin -d lh_contract_db < migrate_v1_2.sql
```

---

## 完整迁移 SQL

```sql
-- ============================================================
-- V1.2 完整数据库迁移脚本
-- ============================================================

-- 开始事务
BEGIN;

-- ============================================================
-- 1. 零星用工表 (zero_hour_labor) 新增列
-- ============================================================
DO $$
BEGIN
    -- 添加派工单文件路径字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'zero_hour_labor' AND column_name = 'dispatch_file_path') THEN
        ALTER TABLE zero_hour_labor ADD COLUMN dispatch_file_path VARCHAR(500);
        RAISE NOTICE 'Added column: zero_hour_labor.dispatch_file_path';
    END IF;
    
    -- 添加技工相关字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'zero_hour_labor' AND column_name = 'skilled_unit_price') THEN
        ALTER TABLE zero_hour_labor ADD COLUMN skilled_unit_price NUMERIC(15, 2) DEFAULT 0;
        RAISE NOTICE 'Added column: zero_hour_labor.skilled_unit_price';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'zero_hour_labor' AND column_name = 'skilled_quantity') THEN
        ALTER TABLE zero_hour_labor ADD COLUMN skilled_quantity NUMERIC(15, 2) DEFAULT 0;
        RAISE NOTICE 'Added column: zero_hour_labor.skilled_quantity';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'zero_hour_labor' AND column_name = 'skilled_price_total') THEN
        ALTER TABLE zero_hour_labor ADD COLUMN skilled_price_total NUMERIC(15, 2) DEFAULT 0;
        RAISE NOTICE 'Added column: zero_hour_labor.skilled_price_total';
    END IF;
    
    -- 添加普工相关字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'zero_hour_labor' AND column_name = 'general_unit_price') THEN
        ALTER TABLE zero_hour_labor ADD COLUMN general_unit_price NUMERIC(15, 2) DEFAULT 0;
        RAISE NOTICE 'Added column: zero_hour_labor.general_unit_price';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'zero_hour_labor' AND column_name = 'general_quantity') THEN
        ALTER TABLE zero_hour_labor ADD COLUMN general_quantity NUMERIC(15, 2) DEFAULT 0;
        RAISE NOTICE 'Added column: zero_hour_labor.general_quantity';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'zero_hour_labor' AND column_name = 'general_price_total') THEN
        ALTER TABLE zero_hour_labor ADD COLUMN general_price_total NUMERIC(15, 2) DEFAULT 0;
        RAISE NOTICE 'Added column: zero_hour_labor.general_price_total';
    END IF;
END $$;

-- ============================================================
-- 2. 零星用工材料表 (zero_hour_labor_materials) - 新表
-- ============================================================
CREATE TABLE IF NOT EXISTS zero_hour_labor_materials (
    id SERIAL PRIMARY KEY,
    zero_hour_labor_id INTEGER NOT NULL REFERENCES zero_hour_labor(id) ON DELETE CASCADE,
    material_name VARCHAR(200) NOT NULL,
    material_unit VARCHAR(50),
    material_quantity NUMERIC(15, 2) DEFAULT 0,
    material_unit_price NUMERIC(15, 2) DEFAULT 0,
    material_price_total NUMERIC(15, 2) DEFAULT 0
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_zero_hour_labor_materials_labor_id 
    ON zero_hour_labor_materials(zero_hour_labor_id);

-- ============================================================
-- 3. 系统字典表 (sys_dictionaries) - 新表
-- ============================================================
CREATE TABLE IF NOT EXISTS sys_dictionaries (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL,
    value VARCHAR(200) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_sys_dictionaries_category ON sys_dictionaries(category);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sys_dictionaries_cat_val ON sys_dictionaries(category, value);

-- ============================================================
-- 4. 系统配置表 (sys_config) - 新表
-- ============================================================
CREATE TABLE IF NOT EXISTS sys_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 插入默认配置
INSERT INTO sys_config (key, value) VALUES ('system_name', '合同管理系统')
ON CONFLICT (key) DO NOTHING;

INSERT INTO sys_config (key, value) VALUES ('system_logo', '')
ON CONFLICT (key) DO NOTHING;

-- ============================================================
-- 5. 枚举类型迁移 (从 ENUM 转换为 VARCHAR)
-- ============================================================
DO $$
DECLARE
    r RECORD;
BEGIN
    -- 迁移列表: (表名, 列名, 枚举类型名)
    FOR r IN SELECT * FROM (VALUES 
        ('contracts_upstream', 'category', 'contractcategory'),
        ('contracts_upstream', 'pricing_mode', 'pricingmode'),
        ('contracts_upstream', 'management_mode', 'managementmode'),
        ('finance_upstream_receivables', 'category', 'receivablecategory'),
        ('contracts_downstream', 'pricing_mode', 'pricingmode'),
        ('contracts_downstream', 'management_mode', 'managementmode'),
        ('finance_downstream_payables', 'category', 'paymentcategory'),
        ('contracts_management', 'pricing_mode', 'pricingmode'),
        ('contracts_management', 'management_mode', 'managementmode'),
        ('finance_management_payables', 'category', 'paymentcategory')
    ) AS t(table_name, column_name, type_name)
    LOOP
        -- 检查列是否存在且类型是否为枚举
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = r.table_name 
            AND column_name = r.column_name
            AND udt_name = r.type_name
        ) THEN
            EXECUTE format('ALTER TABLE %I ALTER COLUMN %I TYPE VARCHAR(255) USING %I::text', 
                           r.table_name, r.column_name, r.column_name);
            RAISE NOTICE 'Converted %.% from ENUM to VARCHAR', r.table_name, r.column_name;
        END IF;
    END LOOP;
END $$;

-- 删除不再使用的枚举类型
DROP TYPE IF EXISTS contractcategory CASCADE;
DROP TYPE IF EXISTS pricingmode CASCADE;
DROP TYPE IF EXISTS managementmode CASCADE;
DROP TYPE IF EXISTS paymentcategory CASCADE;
DROP TYPE IF EXISTS receivablecategory CASCADE;
DROP TYPE IF EXISTS downstreamcontractcategory CASCADE;
DROP TYPE IF EXISTS expensecategory CASCADE;
DROP TYPE IF EXISTS expensetype CASCADE;

-- ============================================================
-- 6. 数据库索引优化
-- ============================================================
-- 上游合同索引
CREATE INDEX IF NOT EXISTS idx_contract_upstream_sign_date ON contracts_upstream(sign_date);
CREATE INDEX IF NOT EXISTS idx_contract_upstream_status ON contracts_upstream(status);
CREATE INDEX IF NOT EXISTS idx_contract_upstream_category ON contracts_upstream(category);

-- 下游合同索引
CREATE INDEX IF NOT EXISTS idx_contract_downstream_upstream_id ON contracts_downstream(upstream_contract_id);
CREATE INDEX IF NOT EXISTS idx_contract_downstream_sign_date ON contracts_downstream(sign_date);

-- 管理合同索引
CREATE INDEX IF NOT EXISTS idx_contract_management_upstream_id ON contracts_management(upstream_contract_id);

-- 财务记录索引
CREATE INDEX IF NOT EXISTS idx_finance_upstream_receipt_date ON finance_upstream_receipts(receipt_date);
CREATE INDEX IF NOT EXISTS idx_finance_upstream_receipt_contract ON finance_upstream_receipts(contract_id);
CREATE INDEX IF NOT EXISTS idx_finance_downstream_payment_date ON finance_downstream_payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_finance_downstream_payment_contract ON finance_downstream_payments(contract_id);

-- 费用索引
CREATE INDEX IF NOT EXISTS idx_expense_non_contract_date ON expenses_non_contract(expense_date);
CREATE INDEX IF NOT EXISTS idx_expense_non_contract_type ON expenses_non_contract(expense_type);

-- 审计日志索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);

-- 零星用工索引
CREATE INDEX IF NOT EXISTS idx_zero_hour_labor_date ON zero_hour_labor(labor_date);
CREATE INDEX IF NOT EXISTS idx_zero_hour_labor_upstream_id ON zero_hour_labor(upstream_contract_id);

-- ============================================================
-- 7. 初始化字典数据 (从枚举值填充)
-- ============================================================
-- 合同分类
INSERT INTO sys_dictionaries (category, label, value, sort_order, is_active) VALUES
('contract_category', '总包合同', '总包合同', 1, TRUE),
('contract_category', '专业分包', '专业分包', 2, TRUE),
('contract_category', '劳务分包', '劳务分包', 3, TRUE),
('contract_category', '设备租赁', '设备租赁', 4, TRUE),
('contract_category', '材料采购', '材料采购', 5, TRUE),
('contract_category', '其他', '其他', 6, TRUE)
ON CONFLICT (category, value) DO NOTHING;

-- 计价模式
INSERT INTO sys_dictionaries (category, label, value, sort_order, is_active) VALUES
('pricing_mode', '固定总价', '固定总价', 1, TRUE),
('pricing_mode', '固定单价', '固定单价', 2, TRUE),
('pricing_mode', '成本加酬金', '成本加酬金', 3, TRUE)
ON CONFLICT (category, value) DO NOTHING;

-- 管理模式
INSERT INTO sys_dictionaries (category, label, value, sort_order, is_active) VALUES
('management_mode', '自主施工', '自主施工', 1, TRUE),
('management_mode', '委托管理', '委托管理', 2, TRUE)
ON CONFLICT (category, value) DO NOTHING;

-- 收款分类
INSERT INTO sys_dictionaries (category, label, value, sort_order, is_active) VALUES
('receivable_category', '预付款', '预付款', 1, TRUE),
('receivable_category', '进度款', '进度款', 2, TRUE),
('receivable_category', '结算款', '结算款', 3, TRUE),
('receivable_category', '质保金', '质保金', 4, TRUE),
('receivable_category', '其他', '其他', 5, TRUE)
ON CONFLICT (category, value) DO NOTHING;

-- 付款分类
INSERT INTO sys_dictionaries (category, label, value, sort_order, is_active) VALUES
('payment_category', '预付款', '预付款', 1, TRUE),
('payment_category', '进度款', '进度款', 2, TRUE),
('payment_category', '结算款', '结算款', 3, TRUE),
('payment_category', '质保金', '质保金', 4, TRUE),
('payment_category', '其他', '其他', 5, TRUE)
ON CONFLICT (category, value) DO NOTHING;

-- 费用分类
INSERT INTO sys_dictionaries (category, label, value, sort_order, is_active) VALUES
('expense_category', '项目相关', '项目相关', 1, TRUE),
('expense_category', '公司运营', '公司运营', 2, TRUE)
ON CONFLICT (category, value) DO NOTHING;

-- 费用类型
INSERT INTO sys_dictionaries (category, label, value, sort_order, is_active) VALUES
('expense_type', '办公费', '办公费', 1, TRUE),
('expense_type', '差旅费', '差旅费', 2, TRUE),
('expense_type', '招待费', '招待费', 3, TRUE),
('expense_type', '水电费', '水电费', 4, TRUE),
('expense_type', '维修费', '维修费', 5, TRUE),
('expense_type', '其他', '其他', 6, TRUE)
ON CONFLICT (category, value) DO NOTHING;

-- 提交事务
COMMIT;

-- ============================================================
-- 完成提示
-- ============================================================
DO $$
BEGIN
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'V1.2 数据库迁移完成!';
    RAISE NOTICE '请重启后端服务: docker-compose restart backend';
    RAISE NOTICE '==============================================';
END $$;
```

---

## 迁移后验证

执行以下 SQL 验证迁移结果：

```sql
-- 检查 zero_hour_labor 新字段
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'zero_hour_labor' 
ORDER BY ordinal_position;

-- 检查新表是否存在
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('zero_hour_labor_materials', 'sys_dictionaries', 'sys_config');

-- 检查字典数据
SELECT category, COUNT(*) FROM sys_dictionaries GROUP BY category;
```

---

## 重启服务

```bash
# 重启后端服务
docker-compose restart backend

# 查看日志确认启动正常
docker-compose logs backend --tail=50
```

---

## 常见问题

### Q1: 迁移脚本报错 "表不存在"

如果 `zero_hour_labor` 表不存在，说明这是全新安装而非升级，无需执行迁移。

### Q2: 枚举类型转换失败

如果某些列已经是 VARCHAR 类型，迁移脚本会自动跳过，不会报错。

### Q3: 如何回滚迁移？

建议在迁移前备份数据库。回滚需要手动删除新增的列和表。
