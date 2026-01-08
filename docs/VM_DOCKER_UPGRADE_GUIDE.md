# VM Docker 系统安全升级指南

## 升级前准备

### 1. 创建 VM 快照 (关键!)

在进行任何升级操作之前，必须先创建 VM 快照：

```bash
# PVE 控制台执行 (假设 VM ID 为 100)
qm snapshot 100 pre-upgrade-$(date +%Y%m%d)

# 或者通过 PVE Web 界面: VM -> Snapshots -> Take Snapshot
```

### 2. 备份重要数据

```bash
# 登录到 VM
ssh user@vm-ip

# 进入项目目录
cd /path/to/LH_Contract_Docker

# 备份数据库
docker compose exec db pg_dump -U lh_admin lh_contract_db > backup_$(date +%Y%m%d).sql

# 备份上传文件
tar -czvf uploads_backup_$(date +%Y%m%d).tar.gz ./backend/uploads/
```

---

## 升级步骤

### 步骤 1: 拉取最新代码

```bash
cd /path/to/LH_Contract_Docker

# 查看当前分支
git branch

# 拉取最新代码
git pull origin release/V1.4.1
```

### 步骤 2: 重建并重启容器

```bash
# 方式一: 仅重建前端 (推荐，速度快)
docker compose build frontend
docker compose up -d frontend

# 方式二: 重建所有服务
docker compose build
docker compose up -d
```

### 步骤 3: 验证服务状态

```bash
# 检查所有容器运行状态
docker compose ps

# 检查前端日志
docker compose logs -f frontend --tail=50

# 检查后端日志
docker compose logs -f backend --tail=50
```

### 步骤 4: 功能验证

1. 访问系统首页，确认能正常加载
2. 测试上游/下游/管理合同列表的分页和搜索功能
3. 验证详情页返回功能是否保留查询状态

---

## 回滚方案

如果升级后出现问题：

### 方式一: 恢复 VM 快照 (最快)

```bash
# PVE 控制台
qm rollback 100 pre-upgrade-20260108
```

### 方式二: Git 回滚

```bash
# 查看提交历史
git log --oneline -5

# 回滚到上一个版本
git revert HEAD

# 重新构建
docker compose build
docker compose up -d
```

---

## 注意事项

> [!WARNING]
> - 生产环境升级请选择业务低峰期
> - 升级前务必创建 VM 快照
> - 升级后至少观察 30 分钟确保稳定
