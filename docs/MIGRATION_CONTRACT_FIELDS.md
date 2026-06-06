# 合同字段迁移指南

## 新字段概述

本次更新为合同模块添加以下字段：

| 合同类型 | 新字段 | 数据库列名 | 说明 |
|---------|-------|-----------|------|
| 上游合同 | 合同经办人 | `contract_handler` | VARCHAR(100) |
| 上游合同 | 合同原件档案号 | `archive_number` | VARCHAR(100) |
| 下游合同 | 合同经办人 | `contract_handler` | VARCHAR(100) |
| 下游合同 | 合同负责人 | `contract_manager` | VARCHAR(100) |
| 管理合同 | 合同经办人 | `contract_handler` | VARCHAR(100) |
| 管理合同 | 合同负责人 | `contract_manager` | VARCHAR(100) |

## 数据库迁移 SQL

在连接到 PostgreSQL 数据库后执行以下 SQL：

```sql
-- 上游合同
ALTER TABLE contracts_upstream 
  ADD COLUMN IF NOT EXISTS contract_handler VARCHAR(100);
ALTER TABLE contracts_upstream 
  ADD COLUMN IF NOT EXISTS archive_number VARCHAR(100);

-- 下游合同
ALTER TABLE contracts_downstream 
  ADD COLUMN IF NOT EXISTS contract_handler VARCHAR(100);
ALTER TABLE contracts_downstream 
  ADD COLUMN IF NOT EXISTS contract_manager VARCHAR(100);

-- 管理合同
ALTER TABLE contracts_management 
  ADD COLUMN IF NOT EXISTS contract_handler VARCHAR(100);
ALTER TABLE contracts_management 
  ADD COLUMN IF NOT EXISTS contract_manager VARCHAR(100);
```

## 使用 Docker 执行迁移

```bash
# 进入容器
docker exec -it lh_contract_docker-backend-1 bash

# 使用 psql 执行
python -c "
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE contracts_upstream ADD COLUMN IF NOT EXISTS contract_handler VARCHAR(100)'))
    conn.execute(text('ALTER TABLE contracts_upstream ADD COLUMN IF NOT EXISTS archive_number VARCHAR(100)'))
    conn.execute(text('ALTER TABLE contracts_downstream ADD COLUMN IF NOT EXISTS contract_handler VARCHAR(100)'))
    conn.execute(text('ALTER TABLE contracts_downstream ADD COLUMN IF NOT EXISTS contract_manager VARCHAR(100)'))
    conn.execute(text('ALTER TABLE contracts_management ADD COLUMN IF NOT EXISTS contract_handler VARCHAR(100)'))
    conn.execute(text('ALTER TABLE contracts_management ADD COLUMN IF NOT EXISTS contract_manager VARCHAR(100)'))
    conn.commit()
print('Migration completed successfully!')
"
```

## 验证迁移

```sql
-- 验证字段已添加
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'contracts_upstream' 
  AND column_name IN ('contract_handler', 'archive_number');

SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'contracts_downstream' 
  AND column_name IN ('contract_handler', 'contract_manager');

SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'contracts_management' 
  AND column_name IN ('contract_handler', 'contract_manager');
```
