# PVE 1.6.4 to 1.7 Restore Compatibility

## 结论

1.7 可以接收 1.6.4 的 PostgreSQL 全库备份，并在后端启动时自动执行 `alembic upgrade head`。

PDF 附件兼容分两类：

- 旧本地文件：恢复到宿主机 `/mnt/data/contract_uploads` 后，1.7 会通过 `/api/v1/common/files/...` 受保护接口读取。
- MinIO 对象：1.6.4 上传接口已经可能把 PDF 存到 MinIO。仅恢复数据库和 `uploads` 目录不够，必须同时恢复 `contracts-active` bucket 对象或完整 `minio_data` volume。

## 备份必须包含

- 数据库：`lh_contract_db_*.sql.gz`
- 本地上传目录：`uploads_*.tar.gz`
- MinIO 对象：`minio_contracts-active_*.tar.gz`，或 PVE/磁盘级 `minio_data` volume 备份

如果没有 MinIO 对象备份，数据库中指向 MinIO 的 PDF 记录会存在，但文件会打不开。

## 新 PVE 恢复顺序

在新机器准备目录：

```bash
mkdir -p /mnt/data/contract_uploads /opt/lh-contract/backups /opt/lh-contract/logs
docker network create lh-contract_lh_network 2>/dev/null || true
```

先只启动基础服务：

```bash
docker compose -f docker-compose.pve-prod.yml up -d db redis minio
```

恢复数据库到空库：

```bash
gunzip -c /opt/lh-contract/backups/database/lh_contract_db_YYYYMMDD_HHMMSS.sql.gz \
  | docker exec -i lh_contract_db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

恢复本地 uploads：

```bash
mkdir -p /tmp/lh_restore_uploads
tar -xzf /opt/lh-contract/backups/uploads/uploads_YYYYMMDD_HHMMSS.tar.gz -C /tmp/lh_restore_uploads
rsync -a /tmp/lh_restore_uploads/uploads/ /mnt/data/contract_uploads/
```

恢复 MinIO bucket：

```bash
mc alias set lhminio http://127.0.0.1:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
mc mb --ignore-existing lhminio/contracts-active
mkdir -p /tmp/lh_restore_minio
tar -xzf /opt/lh-contract/backups/object_store/minio_contracts-active_YYYYMMDD_HHMMSS.tar.gz -C /tmp/lh_restore_minio
mc mirror --overwrite /tmp/lh_restore_minio lhminio/contracts-active
```

启动 1.7：

```bash
docker compose -f docker-compose.pve-prod.yml up -d
```

后端容器会自动执行数据库迁移。

## 恢复后检查

```bash
docker compose -f docker-compose.pve-prod.yml exec backend \
  python -m app.scripts.check_pve_restore_compat
```

检查通过条件：

- 关键表和 1.7 必需列存在
- `alembic_version` 已到 `20260527_add_zero_hour_tax_description`，或至少可被 1.7 迁移修正
- 数据库中的 PDF/附件引用能在 MinIO bucket 或 `/app/uploads` 找到

如果检查报告 missing file，需要先确认缺的是 MinIO bucket 对象还是本地 uploads 文件，再补恢复对应备份。
