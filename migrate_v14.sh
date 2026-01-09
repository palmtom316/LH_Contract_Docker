#!/bin/bash
# V1.3 -> V1.4.1 数据库迁移脚本
# 添加飞书审批集成所需的字段

set -e

echo "🔄 正在执行 V1.4.1 数据库迁移..."

# 检测容器名称
if docker ps | grep -q "lh_contract_db_prod"; then
    DB_CONTAINER="lh_contract_db_prod"
elif docker ps | grep -q "lh_contract_db"; then
    DB_CONTAINER="lh_contract_db"
else
    echo "❌ 未找到数据库容器！"
    exit 1
fi

echo "📦 使用数据库容器: $DB_CONTAINER"

docker exec -i "$DB_CONTAINER" psql -U lh_admin -d lh_contract_db << 'EOF'
-- 上游合同表 (contracts_upstream)
ALTER TABLE contracts_upstream ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE contracts_upstream ADD COLUMN IF NOT EXISTS feishu_instance_code VARCHAR(100);
ALTER TABLE contracts_upstream ADD COLUMN IF NOT EXISTS approval_pdf_path VARCHAR(500);
ALTER TABLE contracts_upstream ADD COLUMN IF NOT EXISTS contract_handler VARCHAR(100);
ALTER TABLE contracts_upstream ADD COLUMN IF NOT EXISTS archive_number VARCHAR(100);

-- 下游合同表 (contracts_downstream)
ALTER TABLE contracts_downstream ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE contracts_downstream ADD COLUMN IF NOT EXISTS feishu_instance_code VARCHAR(100);
ALTER TABLE contracts_downstream ADD COLUMN IF NOT EXISTS approval_pdf_path VARCHAR(500);
ALTER TABLE contracts_downstream ADD COLUMN IF NOT EXISTS contract_handler VARCHAR(100);
ALTER TABLE contracts_downstream ADD COLUMN IF NOT EXISTS contract_manager VARCHAR(100);

-- 管理合同表 (contracts_management)
ALTER TABLE contracts_management ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE contracts_management ADD COLUMN IF NOT EXISTS feishu_instance_code VARCHAR(100);
ALTER TABLE contracts_management ADD COLUMN IF NOT EXISTS approval_pdf_path VARCHAR(500);
ALTER TABLE contracts_management ADD COLUMN IF NOT EXISTS contract_handler VARCHAR(100);
ALTER TABLE contracts_management ADD COLUMN IF NOT EXISTS contract_manager VARCHAR(100);

-- 费用表 (expenses_non_contract)
ALTER TABLE expenses_non_contract ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE expenses_non_contract ADD COLUMN IF NOT EXISTS feishu_instance_code VARCHAR(100);
ALTER TABLE expenses_non_contract ADD COLUMN IF NOT EXISTS approval_pdf_path VARCHAR(500);

-- 零星用工表 (zero_hour_labor)
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS feishu_instance_code VARCHAR(100);
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS approval_pdf_path VARCHAR(500);
EOF

echo "✅ 数据库迁移完成！"
