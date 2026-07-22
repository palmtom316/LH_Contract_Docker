# PVE 生产环境 1.8.0 升级至 1.9.0

## 前提

- 当前数据库 Alembic revision 必须为正式 1.8 基线之一：`20260527_add_zero_hour_tax_description` 或 `20260717_invoice_project_matching`。后者是包含发票匹配加固的最新 1.8 生产头。
- `.env.production` 必须配置 `CONFIG_ENCRYPTION_KEY`，并离线备份该密钥。
- 1.9.0 后端与前端镜像必须已推送至 GHCR。
- 如 `.env.production` 设置了 `BACKEND_IMAGE` 或 `FRONTEND_IMAGE`，必须更新为 `1.9.0`；预检会拒绝任何仍解析为 1.8 的镜像。
- `/opt/lh-contract/backups`、PostgreSQL、MinIO 数据卷必须有足够空间。

## 升级

在项目目录执行：

```bash
git fetch origin
git switch release/1.9
git pull --ff-only origin release/1.9
./scripts/upgrade_to_v1.9.sh
```

脚本会依次执行 1.8 基线检查、数据库与对象存储备份、拉取镜像、一次性迁移、1.9 schema 检查和服务滚动启动。任一步失败都会立即退出，不会继续启动新版本。

## 上线验证

```bash
docker compose --env-file .env.production -f docker-compose.pve-prod.yml ps
curl --fail http://127.0.0.1/health/ready
docker exec lh_contract_backend alembic current
```

Alembic revision 应为 `20260722_durable_import_jobs`。随后在系统设置中确认：

- 公司名称和税号正确。
- 公司银行账号已填写，否则回单方向只能人工复核。
- 启用 MinerU 时，API 地址必须为 HTTPS、密钥状态为已配置，并通过连接测试。
- 上传一份测试发票和回单，确认批次能够从 `uploaded` 自动进入完成或待复核状态。

## 回滚

1. 立即停止对外流量，不要继续录入 1.9 财务数据。
2. 停止应用容器。
3. 恢复升级脚本生成的 PostgreSQL 全库备份和同时间点 MinIO 对象备份。
4. 将 `BACKEND_IMAGE`、`FRONTEND_IMAGE` 固定回 `1.8.0` 后启动。

禁止只执行 Alembic downgrade 后继续使用，因为 1.9 的审计和来源字段采用保留数据的增量迁移，数据库与对象存储必须按同一备份时间点整体回滚。
