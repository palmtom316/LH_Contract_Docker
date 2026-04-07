# 系统升级指南：V1.1.2 → V1.2

## 升级概述

本次升级主要变更：
1. **数据字典支持**：分类字段（合同类别、计价模式、管理模式、应收/应付款类别等）从固定ENUM改为支持数据字典的VARCHAR类型
2. **状态调整**：删除"进行中"状态，统一使用"执行中"
3. **Bug修复**：修复应收款保存时的数据库错误

---

## 升级步骤

### 第一步：备份现有数据（重要！）

在生产服务器上执行：

```bash
# 1. 进入项目目录
cd /path/to/LH_Contract_Docker

# 2. 备份数据库
docker exec lh_contract_db pg_dump -U lh_admin -d lh_contract_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 3. 备份上传文件
cp -r uploads uploads_backup_$(date +%Y%m%d)

# 4. 确认备份文件已生成
ls -la backup_*.sql
ls -la uploads_backup_*
```

### 第二步：停止服务

```bash
docker compose down
```

### 第三步：拉取最新代码

```bash
# 拉取最新代码
git fetch origin
git checkout release/V1.2   # 或者您创建的新分支名
git pull origin release/V1.2

# 或者如果使用main分支
git pull origin main
```

### 第四步：执行数据库迁移

启动数据库服务并执行迁移SQL：

```bash
# 仅启动数据库
docker compose up -d db

# 等待数据库启动（约5秒）
sleep 5

# 执行数据库迁移
docker exec -i lh_contract_db psql -U lh_admin -d lh_contract_db << 'EOF'
-- ===== V1.2 数据库迁移脚本 =====

-- 1. 将ENUM列改为VARCHAR类型
ALTER TABLE contracts_upstream ALTER COLUMN category TYPE VARCHAR(100) USING category::TEXT;
ALTER TABLE contracts_upstream ALTER COLUMN pricing_mode TYPE VARCHAR(100) USING pricing_mode::TEXT;
ALTER TABLE contracts_upstream ALTER COLUMN management_mode TYPE VARCHAR(100) USING management_mode::TEXT;

ALTER TABLE contracts_downstream ALTER COLUMN pricing_mode TYPE VARCHAR(100) USING pricing_mode::TEXT;
ALTER TABLE contracts_downstream ALTER COLUMN management_mode TYPE VARCHAR(100) USING management_mode::TEXT;

ALTER TABLE contracts_management ALTER COLUMN pricing_mode TYPE VARCHAR(100) USING pricing_mode::TEXT;
ALTER TABLE contracts_management ALTER COLUMN management_mode TYPE VARCHAR(100) USING management_mode::TEXT;

ALTER TABLE finance_downstream_payables ALTER COLUMN category TYPE VARCHAR(100) USING category::TEXT;
ALTER TABLE finance_management_payables ALTER COLUMN category TYPE VARCHAR(100) USING category::TEXT;
ALTER TABLE finance_upstream_receivables ALTER COLUMN category TYPE VARCHAR(100) USING category::TEXT;

-- 2. 更新上游合同分类数据（从英文ENUM值转为中文）
UPDATE contracts_upstream SET category = '总包合同' WHERE category = 'GENERAL';
UPDATE contracts_upstream SET category = '专业分包' WHERE category = 'SUB_PRO';
UPDATE contracts_upstream SET category = '劳务分包' WHERE category = 'SUB_LABOR';
UPDATE contracts_upstream SET category = '技术服务' WHERE category = 'SERVICE';
UPDATE contracts_upstream SET category = '运营维护' WHERE category = 'MAINTENANCE';
UPDATE contracts_upstream SET category = '物资采购' WHERE category = 'MATERIAL';
UPDATE contracts_upstream SET category = '其他合同' WHERE category = 'OTHER';

-- 3. 更新计价模式数据
UPDATE contracts_upstream SET pricing_mode = '总价包干' WHERE pricing_mode = 'FIXED_TOTAL';
UPDATE contracts_upstream SET pricing_mode = '单价包干' WHERE pricing_mode = 'FIXED_UNIT';
UPDATE contracts_upstream SET pricing_mode = '工日单价' WHERE pricing_mode = 'LABOR_UNIT';
UPDATE contracts_upstream SET pricing_mode = '费率下浮' WHERE pricing_mode = 'RATE_FLOAT';

UPDATE contracts_downstream SET pricing_mode = '总价包干' WHERE pricing_mode = 'FIXED_TOTAL';
UPDATE contracts_downstream SET pricing_mode = '单价包干' WHERE pricing_mode = 'FIXED_UNIT';
UPDATE contracts_downstream SET pricing_mode = '工日单价' WHERE pricing_mode = 'LABOR_UNIT';
UPDATE contracts_downstream SET pricing_mode = '费率下浮' WHERE pricing_mode = 'RATE_FLOAT';

UPDATE contracts_management SET pricing_mode = '总价包干' WHERE pricing_mode = 'FIXED_TOTAL';
UPDATE contracts_management SET pricing_mode = '单价包干' WHERE pricing_mode = 'FIXED_UNIT';
UPDATE contracts_management SET pricing_mode = '工日单价' WHERE pricing_mode = 'LABOR_UNIT';
UPDATE contracts_management SET pricing_mode = '费率下浮' WHERE pricing_mode = 'RATE_FLOAT';

-- 4. 更新管理模式数据
UPDATE contracts_upstream SET management_mode = '自营工程' WHERE management_mode = 'SELF';
UPDATE contracts_upstream SET management_mode = '合作工程' WHERE management_mode = 'COOP';
UPDATE contracts_upstream SET management_mode = '挂靠工程' WHERE management_mode = 'AFFILIATE';

UPDATE contracts_downstream SET management_mode = '自营工程' WHERE management_mode = 'SELF';
UPDATE contracts_downstream SET management_mode = '合作工程' WHERE management_mode = 'COOP';
UPDATE contracts_downstream SET management_mode = '挂靠工程' WHERE management_mode = 'AFFILIATE';

UPDATE contracts_management SET management_mode = '自营工程' WHERE management_mode = 'SELF';
UPDATE contracts_management SET management_mode = '合作工程' WHERE management_mode = 'COOP';
UPDATE contracts_management SET management_mode = '挂靠工程' WHERE management_mode = 'AFFILIATE';

-- 5. 更新应收款/应付款类别数据
UPDATE finance_upstream_receivables SET category = '预付款' WHERE category = 'ADVANCE_PAYMENT';
UPDATE finance_upstream_receivables SET category = '进度款' WHERE category = 'PROGRESS_PAYMENT';
UPDATE finance_upstream_receivables SET category = '结算款' WHERE category = 'SETTLEMENT_PAYMENT';
UPDATE finance_upstream_receivables SET category = '质保金' WHERE category = 'RETENTION_MONEY';
UPDATE finance_upstream_receivables SET category = '其他' WHERE category = 'OTHER';

UPDATE finance_downstream_payables SET category = '预付款' WHERE category = 'PREPAYMENT';
UPDATE finance_downstream_payables SET category = '进度款' WHERE category = 'PROGRESS';
UPDATE finance_downstream_payables SET category = '完工款' WHERE category = 'COMPLETION';
UPDATE finance_downstream_payables SET category = '结算款' WHERE category = 'SETTLEMENT';
UPDATE finance_downstream_payables SET category = '质保金' WHERE category = 'WARRANTY';

UPDATE finance_management_payables SET category = '预付款' WHERE category = 'PREPAYMENT';
UPDATE finance_management_payables SET category = '进度款' WHERE category = 'PROGRESS';
UPDATE finance_management_payables SET category = '完工款' WHERE category = 'COMPLETION';
UPDATE finance_management_payables SET category = '结算款' WHERE category = 'SETTLEMENT';
UPDATE finance_management_payables SET category = '质保金' WHERE category = 'WARRANTY';

-- 6. 更新合同状态（进行中 → 执行中）
UPDATE contracts_upstream SET status = '执行中' WHERE status = '进行中';
UPDATE contracts_downstream SET status = '执行中' WHERE status = '进行中';
UPDATE contracts_management SET status = '执行中' WHERE status = '进行中';

-- 7. 验证迁移结果
SELECT 'contracts_upstream' as table_name, COUNT(*) as count FROM contracts_upstream
UNION ALL
SELECT 'contracts_downstream', COUNT(*) FROM contracts_downstream
UNION ALL
SELECT 'contracts_management', COUNT(*) FROM contracts_management;

EOF
```

### 第五步：重建并启动所有服务

```bash
# 重建镜像并启动
docker compose up -d --build

# 查看启动状态
docker compose ps

# 查看日志确认无错误
docker logs lh_contract_backend --tail 20
docker logs lh_contract_frontend --tail 10
```

### 第六步：验证升级

1. **访问系统**：打开浏览器访问 http://您的服务器IP
2. **清除浏览器缓存**：按 Ctrl+Shift+R 硬刷新
3. **检查合同列表**：确认合同类别、计价模式等字段显示正确的中文值
4. **测试新增功能**：尝试新增一条应收款，选择"安全文明措施费"等自定义类别
5. **检查状态筛选**：确认状态下拉框只有"执行中"没有"进行中"

---

## 回滚方案

如果升级失败，可以回滚到之前版本：

```bash
# 1. 停止服务
docker compose down

# 2. 恢复代码
git checkout v1.1.2  # 或之前的分支/标签

# 3. 恢复数据库
docker compose up -d db
sleep 5
docker exec -i lh_contract_db psql -U lh_admin -d lh_contract_db < backup_YYYYMMDD_HHMMSS.sql

# 4. 恢复上传文件
rm -rf uploads
mv uploads_backup_YYYYMMDD uploads

# 5. 重启服务
docker compose up -d --build
```

---

## 注意事项

1. **备份优先**：升级前务必完成数据库和文件备份
2. **低峰期操作**：建议在业务低峰期进行升级
3. **网络环境**：确保服务器可以访问Docker Hub（用于拉取镜像）
4. **磁盘空间**：确保有足够的磁盘空间用于备份和重建镜像
5. **浏览器缓存**：升级后通知用户清除浏览器缓存

---

## 联系支持

如遇问题，请保存以下信息用于排查：
- 错误日志：`docker logs lh_contract_backend > error.log 2>&1`
- 数据库状态：`docker exec lh_contract_db psql -U lh_admin -d lh_contract_db -c "\dt"`
