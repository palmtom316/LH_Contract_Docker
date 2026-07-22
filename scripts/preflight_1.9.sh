#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.pve-prod.yml}"
DB_CONTAINER="${DB_CONTAINER:-lh_contract_db}"
ENV_FILE="${ENV_FILE:-.env.production}"
TARGET_REVISION="20260722_durable_import_jobs"
BASE_REVISION="20260527_add_zero_hour_tax_description"
CURRENT_18_REVISION="20260717_invoice_project_matching"
MODE="${1:-after}"
export PRODUCTION_ENV_FILE="${ENV_FILE}"

test -f "${ENV_FILE}" || { echo "Preflight failed: ${ENV_FILE} not found" >&2; exit 1; }
query() { docker exec "${DB_CONTAINER}" sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "$1"' sh "$1"; }
require_env_key() {
    awk -F= -v key="$1" '$1 == key { value=substr($0,index($0,"=")+1); if (length(value)>0 && value !~ /^<.*>$/) found=1 } END { exit(found ? 0 : 1) }' "${ENV_FILE}" || {
        echo "Preflight failed: ${1} missing or placeholder" >&2; exit 1;
    }
}

revision="$(query 'SELECT version_num FROM alembic_version LIMIT 1;')"
width="$(query "SELECT character_maximum_length FROM information_schema.columns WHERE table_name='alembic_version' AND column_name='version_num';")"
if [ "${MODE}" = before ]; then
    if [ "${revision}" != "${BASE_REVISION}" ] && [ "${revision}" != "${CURRENT_18_REVISION}" ] && [ "${revision}" != "${TARGET_REVISION}" ]; then
        echo "Preflight failed: expected ${BASE_REVISION}, ${CURRENT_18_REVISION}, or ${TARGET_REVISION}, got ${revision:-missing}" >&2
        exit 1
    fi
else
    [ "${revision}" = "${TARGET_REVISION}" ] || { echo "Preflight failed: expected ${TARGET_REVISION}, got ${revision:-missing}" >&2; exit 1; }
fi
if [ "${MODE}" = after ]; then
    [ -z "${width}" ] || [ "${width}" -ge "40" ] || { echo "Preflight failed: alembic_version.version_num is too narrow" >&2; exit 1; }
fi

for key in COMPANY_NAME COMPANY_TAX_NO MINIO_ROOT_USER MINIO_ROOT_PASSWORD SECRET_KEY CONFIG_ENCRYPTION_KEY; do require_env_key "${key}"; done
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" config >/dev/null
images="$(docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" config --images)"
echo "${images}" | grep -Eq 'lh-contract-backend:1\.9\.0$' || { echo "Preflight failed: resolved backend image is not 1.9.0" >&2; exit 1; }
echo "${images}" | grep -Eq 'lh-contract-frontend:1\.9\.0$' || { echo "Preflight failed: resolved frontend image is not 1.9.0" >&2; exit 1; }

if [ "${MODE}" = after ]; then
    required=(
        "invoice_import_batches:job_attempts"
        "invoice_import_batches:job_lease_until"
        "bank_receipt_batches:job_worker_token"
        "finance_zero_hour_invoices:source_import_allocation_id"
        "finance_zero_hour_payments:source_bank_receipt_allocation_id"
    )
    for target in "${required[@]}"; do
        table="${target%%:*}"
        column="${target#*:}"
        query "SELECT 1 FROM information_schema.columns WHERE table_name='${table}' AND column_name='${column}' LIMIT 1;" | grep -qx 1 || { echo "Preflight failed: missing ${table}.${column}" >&2; exit 1; }
    done
fi
echo "1.9 preflight passed: mode=${MODE}, revision=${revision}, version_width=${width}"
