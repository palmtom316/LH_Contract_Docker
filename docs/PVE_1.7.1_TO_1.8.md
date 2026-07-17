# PVE 1.7.1 升级到 1.8.0

本升级包含数据库结构变更和电子发票对象文件。回滚必须使用同一时间点的 PVE 快照，或成对恢复 PostgreSQL 与 MinIO；不要把 Alembic downgrade 作为生产数据回滚方案。

## 升级闸门

1. 将 `.env.production.example` 中新增的企业信息和发票导入限制同步到 `.env.production`。
2. 创建 PVE 虚拟机快照。
3. 安装并配置 MinIO Client (`mc`)，运行 `scripts/backup.sh`。脚本返回非零时停止升级。
4. 运行 `scripts/preflight_1.8.sh`，确认当前 revision、必填配置和 Compose 配置全部通过。
5. 确认 GHCR 中存在 `1.8.0` 后端和前端镜像。

## 停机升级

```bash
git fetch origin
git switch release/1.8
git pull --ff-only origin release/1.8

docker compose --env-file .env.production -f docker-compose.pve-prod.yml pull
docker compose --env-file .env.production -f docker-compose.pve-prod.yml up -d
```

后端容器启动时会先执行 `alembic upgrade head`。不要同时启动多个不同版本的后端容器执行迁移。

## 验收

```bash
docker compose --env-file .env.production -f docker-compose.pve-prod.yml ps
curl --fail http://127.0.0.1/health/ready
docker exec lh_contract_db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version_num FROM alembic_version;"
```

预期 revision 为 `20260716_invoice_posting_safety`。随后验证登录、合同查询、报表查询与导出、电子发票上传、候选合同选择和确认挂账。

## 回滚

如果迁移或验收失败，立即停止 1.8 服务并恢复升级前 PVE 快照。若只能使用应用级备份，则 PostgreSQL、MinIO 对象和旧 uploads 必须恢复到同一备份时间点。
