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
-- 上游合同表
ALTER TABLE contract_upstream ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE contract_upstream ADD COLUMN IF NOT EXISTS feishu_instance_code VARCHAR(100);
ALTER TABLE contract_upstream ADD COLUMN IF NOT EXISTS approval_pdf_path VARCHAR(500);

-- 下游合同表
ALTER TABLE contract_downstream ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE contract_downstream ADD COLUMN IF NOT EXISTS feishu_instance_code VARCHAR(100);
ALTER TABLE contract_downstream ADD COLUMN IF NOT EXISTS approval_pdf_path VARCHAR(500);

-- 管理合同表
ALTER TABLE contract_management ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE contract_management ADD COLUMN IF NOT EXISTS feishu_instance_code VARCHAR(100);
ALTER TABLE contract_management ADD COLUMN IF NOT EXISTS approval_pdf_path VARCHAR(500);

-- 费用表
ALTER TABLE expense ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE expense ADD COLUMN IF NOT EXISTS feishu_instance_code VARCHAR(100);
ALTER TABLE expense ADD COLUMN IF NOT EXISTS approval_pdf_path VARCHAR(500);

-- 零星用工表
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS feishu_instance_code VARCHAR(100);
ALTER TABLE zero_hour_labor ADD COLUMN IF NOT EXISTS approval_pdf_path VARCHAR(500);
EOF

echo "✅ 数据库迁移完成！"
