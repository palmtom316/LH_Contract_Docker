# LH 合同管理系统 V1.3 → V1.4.1 升级指南

> **适用环境**: Docker 部署 (Ubuntu/Linux VM)
> **升级内容**: 飞书审批集成 + 列表导航优化

---

## ✅ 升级前准备

1. **VM 快照** (已完成)
2. **确认当前版本**: `git log -1` 应显示 V1.3

---

## 📋 升级步骤

### 步骤 1: 切换到 root 并进入项目目录

```bash
sudo -i
cd /opt/lh-contract   # 或您的实际项目目录
```

### 步骤 2: 拉取最新代码

```bash
git fetch --all
git checkout release/V1.4.1
git pull origin release/V1.4.1
```

### 步骤 3: 执行数据库迁移 (关键!)

V1.4.1 新增了飞书审批相关字段，需要手动添加：

```bash
# 进入数据库容器
docker exec -it lh_contract_db psql -U lh_admin -d lh_contract_db
```

在 psql 中执行：

```sql
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

-- 退出
\q
```

### 步骤 4: 重建并重启容器

```bash
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d --force-recreate
```

### 步骤 5: 验证

```bash
# 检查服务状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f backend --tail=50
```

访问系统确认：
- 合同详情页显示"审批状态"字段
- 列表页分页/搜索返回功能正常

---

## ❌ 回滚方案

如升级失败，恢复 VM 快照即可。
