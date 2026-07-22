#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.pve-prod.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"
export COMPOSE_FILE ENV_FILE
export PRODUCTION_ENV_FILE="${ENV_FILE}"

./scripts/preflight_1.9.sh before
echo "Create and verify the upgrade backup before continuing."
./scripts/backup.sh
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" pull backend frontend sync-worker db redis minio
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" run --rm backend alembic upgrade head
./scripts/preflight_1.9.sh after
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --remove-orphans
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps
echo "1.9.0 upgrade completed; verify /health/ready and finance import queues before opening traffic."
