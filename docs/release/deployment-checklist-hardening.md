# v1.6 Hardening Deployment Checklist

## 适用范围
- 本清单适用于已稳定运行半年、存在大量历史合同、历史费用记录、历史附件和既有数据字典值的生产环境升级。
- 本次升级目标是安全加固与兼容修复，不允许以“清理旧数据”为名删除历史记录、重写附件路径或覆盖已有 `expense_type` / 费用类别值。

## 发布顺序
1. 执行升级前基线备份。
2. 部署后端兼容改动。
3. 执行只增量、非破坏性数据库迁移。
4. 执行升级验证脚本与基线比对。
5. 部署前端。
6. 执行上线后冒烟验证。
7. 观察监控与错误日志，确认无回滚门槛触发。

## 上线前检查
- [ ] `./scripts/backup.sh` 已成功生成数据库、`uploads`、字典、对象存储快照。
- [ ] 已保留升级前版本镜像或可回退提交号。
- [ ] `python3 scripts/verify_migration.py --safety-only` 通过。
- [ ] 已确认本次迁移不包含 `DROP TABLE`、`DROP COLUMN`、附件路径批量改写、已引用字典值硬删除。
- [ ] 已准备至少 1 个历史附件样本用于上线后点检。
- [ ] 已准备至少 1 个使用历史 `expense_type` 的无合同费用记录用于上线后回归验证。
- [ ] 已确认生产环境 `INIT_ADMIN_TOKEN` 已配置，且未暴露默认管理员初始化入口。

## 发布执行
### 1. 备份与冻结
```bash
chmod +x scripts/backup.sh
./scripts/backup.sh
python3 scripts/verify_migration.py --safety-only
```

### 2. 部署后端
```bash
docker-compose -f docker-compose.production.yml --env-file .env.production build backend
docker-compose -f docker-compose.production.yml --env-file .env.production up -d backend
```

### 3. 执行迁移
```bash
# 示例，按实际迁移方式执行
docker-compose -f docker-compose.production.yml --env-file .env.production exec backend \
  python3 scripts/verify_migration.py --safety-only
```

### 4. 部署前端
```bash
npm --prefix frontend install
npm --prefix frontend run build
docker-compose -f docker-compose.production.yml --env-file .env.production build frontend
docker-compose -f docker-compose.production.yml --env-file .env.production up -d frontend nginx
```

## 上线后冒烟验证
### 必做检查
- [ ] 老用户可以正常登录。
- [ ] `/health` 与 `/health/detailed` 返回正常。
- [ ] 历史上游、下游、管理合同列表可打开。
- [ ] 历史无合同费用列表和详情可打开。
- [ ] 历史附件可下载或预览。
- [ ] `system/options?category=expense_type` 能正常返回现有费用类别。
- [ ] 已被历史记录引用的旧 `expense_type` 仍可在列表/详情中回显。
- [ ] 新增费用类别不会覆盖旧值，也不会导致旧记录显示空白。

### 推荐命令
```bash
curl -fsS http://localhost/health
curl -fsS http://localhost/api/v1/system/options?category=expense_type
```

### 需人工抽检的业务点
1. 打开一条历史上游合同，确认合同文件可访问。
2. 打开一条历史无合同费用记录，确认费用类别与费用归属均正常显示。
3. 在系统管理中查看数据字典，确认旧的费用类别若被停用，仍未被硬删除。

## 回滚门槛
满足任一条件立即进入回滚流程：
- 登录失败率明显上升，或刷新令牌流程持续报错。
- 历史附件出现大面积 `401` / `404`。
- 历史费用记录详情出现空白类别、报错或无法查询。
- 数据字典接口异常，影响录入页或筛选页使用。
- 数据库迁移耗时异常、阻塞写入或引发服务雪崩。

## 回滚方式
1. 停止写流量或进入维护模式。
2. 回退应用镜像或代码到升级前版本。
3. 保留已经执行的兼容性迁移，不做反向删列或反向破坏性 DDL。
4. 仅当数据确实损坏时，才从升级前备份恢复数据库与 `uploads`。
5. 对对象存储优先做只读校验，不做覆盖式回滚。

## 回滚后复核
- [ ] 登录恢复正常。
- [ ] 历史合同与历史费用记录恢复可查询。
- [ ] 历史附件恢复可访问。
- [ ] `expense_type` 字典及历史费用类别恢复可回显。
- [ ] 监控脚本恢复绿色状态。
