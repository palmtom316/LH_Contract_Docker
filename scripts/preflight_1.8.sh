#!/usr/bin/env bash

set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.pve-prod.yml}"
DB_CONTAINER="${DB_CONTAINER:-lh_contract_db}"
ENV_FILE="${ENV_FILE:-.env.production}"
EXPECTED_REVISION="20260527_add_zero_hour_tax_description"

query() {
    docker exec "${DB_CONTAINER}" sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "$1"' sh "$1"
}

require_env_key() {
    if ! awk -F= -v key="$1" '
        $1 == key {
            value = substr($0, index($0, "=") + 1)
            if (length(value) > 0 && value !~ /^<.*>$/) found = 1
        }
        END { exit(found ? 0 : 1) }
    ' "${ENV_FILE}"; then
        echo "Preflight failed: ${1} is missing or still a placeholder in ${ENV_FILE}" >&2
        exit 1
    fi
}

test -f "${ENV_FILE}" || { echo "Preflight failed: ${ENV_FILE} not found" >&2; exit 1; }

current_revision="$(query "SELECT version_num FROM alembic_version LIMIT 1;")"
version_width="$(query "SELECT character_maximum_length FROM information_schema.columns WHERE table_name='alembic_version' AND column_name='version_num';")"

if [ "${current_revision}" != "${EXPECTED_REVISION}" ]; then
    echo "Preflight failed: expected Alembic revision ${EXPECTED_REVISION}, got ${current_revision:-missing}" >&2
    exit 1
fi

if [ -n "${version_width}" ] && [ "${version_width}" -lt "${#current_revision}" ]; then
    echo "Preflight failed: alembic_version.version_num cannot hold the current revision" >&2
    exit 1
fi

required=(COMPANY_NAME COMPANY_TAX_NO MINIO_ROOT_USER MINIO_ROOT_PASSWORD SECRET_KEY)
for name in "${required[@]}"; do
    require_env_key "${name}"
done

docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" config >/dev/null
echo "1.8 preflight passed: revision=${current_revision}, version_width=${version_width}"
