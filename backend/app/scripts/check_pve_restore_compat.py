"""
Check 1.6.4 backup compatibility after restoring into a 1.7 PVE deployment.

Run inside the backend container:
    python -m app.scripts.check_pve_restore_compat
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
from pathlib import Path, PurePosixPath
from typing import Iterable
from urllib.parse import urlparse

from sqlalchemy import text

from app.config import settings
from app.core.minio import get_minio_client
from app.database import engine
from app.services.file_authorization import normalize_file_reference


EXPECTED_HEAD = "20260527_add_zero_hour_tax_description"

REQUIRED_TABLES = (
    "users",
    "contracts_upstream",
    "contracts_downstream",
    "contracts_management",
    "expenses_non_contract",
    "zero_hour_labor",
    "sys_dictionaries",
    "sys_config",
    "refresh_tokens",
)

REQUIRED_COLUMNS = {
    "contracts_upstream": (
        "contract_file_path",
        "contract_file_key",
        "approval_pdf_path",
        "approval_pdf_key",
    ),
    "contracts_downstream": (
        "contract_file_path",
        "contract_file_key",
        "approval_pdf_path",
        "approval_pdf_key",
    ),
    "contracts_management": (
        "contract_file_path",
        "contract_file_key",
        "approval_pdf_path",
        "approval_pdf_key",
    ),
    "expenses_non_contract": (
        "file_path",
        "file_key",
        "approval_pdf_path",
        "approval_pdf_key",
    ),
    "zero_hour_labor": (
        "dispatch_file_path",
        "dispatch_file_key",
        "approval_pdf_path",
        "approval_pdf_key",
        "description",
        "tax_rate",
        "tax_amount",
    ),
    "refresh_tokens": ("jti", "user_id", "expires_at", "revoked"),
}

FILE_REFERENCE_COLUMNS = {
    "contracts_upstream": (
        "contract_file_path",
        "contract_file_key",
        "approval_pdf_path",
        "approval_pdf_key",
    ),
    "contracts_downstream": (
        "contract_file_path",
        "contract_file_key",
        "approval_pdf_path",
        "approval_pdf_key",
    ),
    "contracts_management": (
        "contract_file_path",
        "contract_file_key",
        "approval_pdf_path",
        "approval_pdf_key",
    ),
    "project_settlements": (
        "file_path",
        "file_key",
        "audit_report_path",
        "audit_report_key",
        "start_report_path",
        "start_report_key",
        "completion_report_path",
        "completion_report_key",
    ),
    "expenses_non_contract": (
        "file_path",
        "file_key",
        "approval_pdf_path",
        "approval_pdf_key",
    ),
    "finance_upstream_receivables": ("file_path", "file_key"),
    "finance_upstream_invoices": ("file_path", "file_key"),
    "finance_upstream_receipts": ("file_path", "file_key"),
    "finance_downstream_payables": ("file_path", "file_key"),
    "finance_downstream_invoices": ("file_path", "file_key"),
    "finance_downstream_payments": ("file_path", "file_key"),
    "finance_management_payables": ("file_path", "file_key"),
    "finance_management_invoices": ("file_path", "file_key"),
    "finance_management_payments": ("file_path", "file_key"),
    "downstream_settlements": ("file_path", "file_key"),
    "management_settlements": ("file_path", "file_key"),
    "zero_hour_labor": (
        "dispatch_file_path",
        "dispatch_file_key",
        "approval_pdf_path",
        "approval_pdf_key",
    ),
}

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def quote_identifier(value: str) -> str:
    if not IDENTIFIER_RE.match(value):
        raise ValueError(f"Unsafe SQL identifier: {value}")
    return f'"{value}"'


def normalize_restored_file_reference(raw_value: str, upload_root: Path) -> tuple[str | None, str | None]:
    value = str(raw_value or "").strip()
    if not value:
        return None, "empty"

    parsed = urlparse(value)
    if parsed.scheme in {"http", "https", "blob", "data"}:
        return None, "external"
    if parsed.scheme and parsed.scheme not in {"file"}:
        return None, f"unsupported scheme: {parsed.scheme}"

    path_value = parsed.path if parsed.scheme else value
    path_value = path_value.split("?", 1)[0].replace("\\", "/")

    upload_root_text = str(upload_root).replace("\\", "/").rstrip("/")
    for prefix in (
        f"{upload_root_text}/",
        "/app/uploads/",
        "app/uploads/",
        "/backend/uploads/",
        "backend/uploads/",
        "/uploads/",
        "uploads/",
    ):
        if path_value.startswith(prefix):
            path_value = path_value[len(prefix):]
            break

    normalized = normalize_file_reference(path_value)
    if not normalized:
        return None, "empty"

    parts = PurePosixPath(normalized).parts
    if any(part in {"", ".", ".."} for part in parts):
        return None, f"unsafe path: {raw_value}"
    return "/".join(parts), None


def path_under_upload_root(upload_root: Path, normalized: str) -> Path:
    candidate = upload_root.joinpath(*PurePosixPath(normalized).parts)
    root_real = upload_root.resolve(strict=False)
    candidate_real = candidate.resolve(strict=False)
    try:
        candidate_real.relative_to(root_real)
    except ValueError as exc:
        raise ValueError(f"path escapes upload root: {normalized}") from exc
    return candidate_real


async def fetch_existing_tables(conn) -> set[str]:
    result = await conn.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """
        )
    )
    return {row[0] for row in result}


async def fetch_existing_columns(conn, table_name: str) -> set[str]:
    result = await conn.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table_name
            """
        ),
        {"table_name": table_name},
    )
    return {row[0] for row in result}


async def fetch_alembic_versions(conn, existing_tables: set[str]) -> list[str]:
    if "alembic_version" not in existing_tables:
        return []
    result = await conn.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num"))
    return [row[0] for row in result]


def minio_object_exists(client, bucket_name: str, object_name: str) -> bool:
    if not client:
        return False
    try:
        client.stat_object(bucket_name, object_name)
        return True
    except Exception:
        return False


async def iter_file_references(conn, existing_tables: set[str]) -> Iterable[tuple[str, int, str, str]]:
    for table_name, reference_columns in FILE_REFERENCE_COLUMNS.items():
        if table_name not in existing_tables:
            continue
        existing_columns = await fetch_existing_columns(conn, table_name)
        available_columns = [col for col in reference_columns if col in existing_columns]
        for column_name in available_columns:
            table_sql = quote_identifier(table_name)
            column_sql = quote_identifier(column_name)
            result = await conn.execute(
                text(
                    f"""
                    SELECT id, {column_sql} AS file_ref
                    FROM {table_sql}
                    WHERE {column_sql} IS NOT NULL
                      AND btrim(CAST({column_sql} AS text)) <> ''
                    """
                )
            )
            for row in result:
                yield table_name, row.id, column_name, row.file_ref


async def run_check(sample_limit: int) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    upload_root = Path(settings.UPLOAD_DIR)

    minio_client = None
    if settings.MINIO_ENDPOINT and settings.MINIO_ACCESS_KEY and settings.MINIO_SECRET_KEY:
        minio_client = get_minio_client()
    else:
        warnings.append("MinIO is not fully configured; object checks are skipped.")

    print("== 1.7 PVE restore compatibility check ==")
    print(f"upload_root={upload_root}")
    print(f"minio_endpoint={settings.MINIO_ENDPOINT or '(not configured)'}")
    print(f"bucket={settings.MINIO_BUCKET_CONTRACTS}")

    async with engine.begin() as conn:
        existing_tables = await fetch_existing_tables(conn)
        missing_tables = sorted(set(REQUIRED_TABLES) - existing_tables)
        if missing_tables:
            errors.append(f"missing required tables: {', '.join(missing_tables)}")

        versions = await fetch_alembic_versions(conn, existing_tables)
        if not versions:
            warnings.append("alembic_version is missing; 1.7 will treat the DB as an unstamped legacy restore.")
        elif versions != [EXPECTED_HEAD]:
            warnings.append(f"alembic_version={versions}; expected head is {EXPECTED_HEAD}.")

        for table_name, required_columns in REQUIRED_COLUMNS.items():
            if table_name not in existing_tables:
                continue
            existing_columns = await fetch_existing_columns(conn, table_name)
            missing_columns = sorted(set(required_columns) - existing_columns)
            if missing_columns:
                errors.append(f"{table_name} missing columns: {', '.join(missing_columns)}")

        total_refs = 0
        minio_hits = 0
        local_hits = 0
        skipped_refs = 0
        missing_examples: list[str] = []
        invalid_examples: list[str] = []
        seen_refs: set[str] = set()

        async for table_name, row_id, column_name, raw_ref in iter_file_references(conn, existing_tables):
            normalized, skip_reason = normalize_restored_file_reference(raw_ref, upload_root)
            if skip_reason in {"empty", "external"}:
                skipped_refs += 1
                continue
            if skip_reason:
                invalid_examples.append(f"{table_name}[{row_id}].{column_name}: {skip_reason}")
                continue
            if normalized in seen_refs:
                continue
            seen_refs.add(normalized)
            total_refs += 1

            if minio_object_exists(minio_client, settings.MINIO_BUCKET_CONTRACTS, normalized):
                minio_hits += 1
                continue

            try:
                local_path = path_under_upload_root(upload_root, normalized)
            except ValueError as exc:
                invalid_examples.append(f"{table_name}[{row_id}].{column_name}: {exc}")
                continue

            if local_path.is_file():
                local_hits += 1
            elif len(missing_examples) < sample_limit:
                missing_examples.append(
                    f"{table_name}[{row_id}].{column_name}: {raw_ref} -> {local_path}"
                )

        if invalid_examples:
            errors.append("invalid file references found")
        if missing_examples:
            errors.append("file references missing from both MinIO and local uploads")

    if warnings:
        print("\nWarnings:")
        for item in warnings:
            print(f"  - {item}")

    print("\nFile reference summary:")
    print(f"  checked_unique_refs={total_refs}")
    print(f"  minio_hits={minio_hits}")
    print(f"  local_hits={local_hits}")
    print(f"  skipped_refs={skipped_refs}")

    if invalid_examples:
        print("\nInvalid file reference examples:")
        for item in invalid_examples[:sample_limit]:
            print(f"  - {item}")

    if missing_examples:
        print("\nMissing file examples:")
        for item in missing_examples:
            print(f"  - {item}")

    if errors:
        print("\nResult: FAIL")
        for item in errors:
            print(f"  - {item}")
        return 1

    print("\nResult: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=int(os.getenv("RESTORE_CHECK_SAMPLE_LIMIT", "20")),
        help="maximum number of missing/invalid file examples to print",
    )
    args = parser.parse_args()
    return asyncio.run(run_check(sample_limit=args.sample_limit))


if __name__ == "__main__":
    raise SystemExit(main())
