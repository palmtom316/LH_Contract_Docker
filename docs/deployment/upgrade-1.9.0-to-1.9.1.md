# PVE 生产环境 1.9.0 升级至 1.9.1

本升级默认使用 `docker-compose.pve-prod.yml` 中的 GHCR 镜像标签 `1.9.1`。如 `.env.production` 覆盖了 `BACKEND_IMAGE` 或 `FRONTEND_IMAGE`，必须同步改为 `1.9.1`，否则预检会拒绝继续。

## 升级前

1. 确认 GitHub Actions 已发布 `1.9.1` 后端、前端镜像。
2. 创建 PVE 虚拟机快照。
3. 确认 `.env.production` 中必填密钥和企业税号不是占位值。

## 执行升级

```bash
git switch release/1.9
git pull --ff-only origin release/1.9
./scripts/upgrade_to_v1.9.sh
```

脚本会执行升级前预检、应用备份、拉取 `1.9.1` 镜像、Alembic 迁移、升级后预检并重启服务。任一步失败都会立即退出。

## 验收

```bash
docker compose --env-file .env.production -f docker-compose.pve-prod.yml ps
curl -fsS http://127.0.0.1/health/ready
docker compose --env-file .env.production -f docker-compose.pve-prod.yml config --images
```

确认后端和前端镜像均解析为 `1.9.1`，健康检查返回 ready 后再恢复对外流量。

## 回滚

如升级失败，优先恢复升级前 PVE 快照。若只能使用应用级备份，PostgreSQL、MinIO 对象和本地上传目录必须恢复到同一备份时间点。
