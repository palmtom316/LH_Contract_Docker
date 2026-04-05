# Upgrade Runbook v1.6 Hardening

## Scope
This runbook defines the required pre-upgrade baseline capture and post-upgrade safety validation for production upgrades.

## Preconditions
- Deployment uses `docker-compose.production.yml`.
- Database and backend containers are running.
- Operator has write access to backup destination (`/backups` by default).
- Optional: MinIO `mc` client is configured when object snapshot is required.

## 1. Pre-Upgrade Baseline Capture (Mandatory)
Run from repository root:

```bash
chmod +x scripts/backup.sh
./scripts/backup.sh
```

Expected baseline outputs:
- PostgreSQL full dump under `/backups/database`
- `uploads` archive under `/backups/uploads`
- `sys_dictionaries` JSON/CSV under `/backups/dictionaries`
- MinIO bucket snapshot (if `mc` available) under `/backups/object_store`
- Business baseline summary under `/backups/baseline`

## 2. Record the Baseline Checklist (Mandatory)
Before upgrade, confirm evidence exists for:
1. PostgreSQL full backup
2. `uploads` complete backup
3. MinIO object count and total size snapshot (or explicit skipped reason)
4. `sys_dictionaries` export snapshot
5. Total users / contracts / expenses / audit logs
6. New records count in the last 30 days
7. Active dictionary values list

## 2.1 Dictionary Safety Rule for `expense_type` / 费用类别
- Any new 费用类别 must be added incrementally. Do not rename or delete existing values in place during upgrade.
- Before changing `expense_type`, run a reference scan against historical expense records and export the matching `sys_dictionaries` rows.
- If a value is no longer selectable, mark it inactive after compatibility validation. Do not hard-delete values already referenced by historical data.
- Post-upgrade validation must confirm that records using retired `expense_type` values still render and remain queryable.

## 3. Migration Safety Gate (Mandatory)
Run non-destructive checks before applying migrations:

```bash
python3 scripts/verify_migration.py --safety-only
```

The safety gate must fail on:
- `DROP TABLE`
- `DROP COLUMN`
- file-path rewrite `UPDATE ... SET ...` without `backup_marker`
- hard delete in `sys_dictionaries`

Default safety scan targets:
- `backend/alembic/versions`
- `backend/migrations`

## 4. Upgrade Execution
1. Pull/release target image and code.
2. Apply migrations in controlled window.
3. Restart services.

Do not proceed if Step 1/2/3 above is incomplete.

## 5. Post-Upgrade Validation
Run verification checks:

```bash
# Safety re-check
python3 scripts/verify_migration.py --safety-only

# Optional DB integrity check (requires DATABASE_URL)
DATABASE_URL="postgresql+asyncpg://<user>:<pass>@<host>:5432/<db>" \
python3 scripts/verify_migration.py --db-only
```

Verify:
- row counts and major sums are queryable
- dictionary snapshots can be diffed against baseline
- uploads and object storage spot checks succeed
- no unexpected data loss in contracts/expenses/audit logs

## 6. Rollback Readiness
If validation fails:
1. Stop write traffic.
2. Restore PostgreSQL from `/backups/database/*`.
3. Restore `uploads` from `/backups/uploads/*`.
4. Restore dictionary values from baseline export.
5. Re-run validation before reopening traffic.

## 7. Operator Notes
- `backup.sh` is tolerant of partially configured environments and logs warnings for optional components.
- Any warning in baseline capture must be recorded in the change ticket with risk acceptance.
