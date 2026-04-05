#!/usr/bin/env python3
"""
Data Migration Verification Script - V1.5 Upgrade
=================================================
Verifies database/file migration integrity and enforces non-destructive migration rules.

Usage:
    python verify_migration.py --db-only
    python verify_migration.py --files-only
    python verify_migration.py --safety-only
    python verify_migration.py
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None

try:
    from minio import Minio
    from minio.error import S3Error
except ImportError:
    Minio = None

    class S3Error(Exception):
        """Fallback when minio package is not installed."""


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

VERIFICATION_CONFIG: Dict[str, Dict[str, List[str]]] = {
    "contracts_upstream": {"count": True, "sum_fields": ["contract_amount"]},
    "contracts_downstream": {"count": True, "sum_fields": ["contract_amount"]},
    "contracts_management": {"count": True, "sum_fields": ["contract_amount"]},
    "finance_upstream_receivables": {"count": True, "sum_fields": ["amount"]},
    "finance_upstream_collections": {"count": True, "sum_fields": ["amount"]},
    "finance_downstream_payables": {"count": True, "sum_fields": ["amount"]},
    "finance_downstream_payments": {"count": True, "sum_fields": ["amount"]},
    "finance_management_payables": {"count": True, "sum_fields": ["amount"]},
    "finance_management_payments": {"count": True, "sum_fields": ["amount"]},
}

DROP_TABLE_PATTERNS = [
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bop\.drop_table\s*\(", re.IGNORECASE),
]
DROP_COLUMN_PATTERNS = [
    re.compile(r"\bDROP\s+COLUMN\b", re.IGNORECASE),
    re.compile(r"\bop\.drop_column\s*\(", re.IGNORECASE),
]
HARD_DELETE_DICTIONARY_PATTERNS = [
    re.compile(r"\bDELETE\s+FROM\s+sys_dictionaries\b", re.IGNORECASE),
    re.compile(r"\bbulk_delete\s*\([^)]*sys_dictionaries", re.IGNORECASE | re.DOTALL),
]
FILE_PATH_REWRITE_PATTERN = re.compile(r"\bUPDATE\b.+?\bSET\b.+?;", re.IGNORECASE | re.DOTALL)
FILE_FIELD_PATTERN = re.compile(r"\b(file_path|_path|file_key|_key)\b", re.IGNORECASE)
BACKUP_MARKER_PATTERN = re.compile(r"\bbackup_marker\b", re.IGNORECASE)


class MigrationVerifier:
    """Verifies migration integrity and safety rules."""

    def __init__(
        self,
        db_url: Optional[str],
        minio_endpoint: Optional[str] = None,
        minio_access_key: Optional[str] = None,
        minio_secret_key: Optional[str] = None,
        bucket_archive: str = "contracts-archive",
    ) -> None:
        self.db_url = self._convert_db_url(db_url) if db_url else None
        self.minio_endpoint = minio_endpoint
        self.bucket_archive = bucket_archive
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.safety_violations: List[str] = []

        if minio_endpoint and Minio:
            self.minio_client = Minio(
                minio_endpoint,
                access_key=minio_access_key,
                secret_key=minio_secret_key,
                secure=False,
            )
        else:
            self.minio_client = None
            if minio_endpoint and not Minio:
                self.warnings.append("minio package missing; file verification is skipped.")

    @staticmethod
    def _convert_db_url(url: str) -> str:
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return url

    def _require_db(self) -> bool:
        if not self.db_url:
            self.errors.append("DATABASE_URL is required for DB/file verification.")
            return False
        if psycopg2 is None:
            self.errors.append("psycopg2 package not installed; DB verification unavailable.")
            return False
        return True

    def get_db_connection(self):
        return psycopg2.connect(self.db_url)

    def verify_database(self) -> bool:
        logger.info("=" * 60)
        logger.info("Database Verification")
        logger.info("=" * 60)

        if not self._require_db():
            logger.error("Database verification prerequisites not met")
            return False

        conn = self.get_db_connection()
        all_passed = True

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for table_name, config in VERIFICATION_CONFIG.items():
                    cur.execute(
                        """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = %s
                        )
                        """,
                        (table_name,),
                    )
                    if not cur.fetchone()["exists"]:
                        warning = f"Table {table_name} does not exist, skipping"
                        self.warnings.append(warning)
                        logger.warning(warning)
                        continue

                    if config.get("count"):
                        cur.execute(f"SELECT COUNT(*) AS cnt FROM {table_name}")
                        count = cur.fetchone()["cnt"]
                        logger.info("%s: %s rows", table_name, count)

                    for field in config.get("sum_fields", []):
                        cur.execute(f"SELECT COALESCE(SUM({field}), 0) AS total FROM {table_name}")
                        total = cur.fetchone()["total"]
                        logger.info("  └─ %s total: %,.2f", field, total)
        except Exception as exc:
            self.errors.append(f"Database verification failed: {exc}")
            all_passed = False
        finally:
            conn.close()

        return all_passed

    def verify_minio_files(self) -> bool:
        logger.info("=" * 60)
        logger.info("MinIO File Verification")
        logger.info("=" * 60)

        if not self._require_db():
            logger.error("File verification prerequisites not met (DB unavailable)")
            return False

        if not self.minio_client:
            warning = "MinIO client not configured/available, skipping file verification"
            self.warnings.append(warning)
            logger.warning(warning)
            return True

        conn = self.get_db_connection()
        all_passed = True
        total_files = 0
        accessible_files = 0

        tables_config = [
            ("contracts_upstream", "contract_file_key", "contract_file_storage"),
            ("contracts_upstream", "approval_pdf_key", "approval_pdf_storage"),
            ("contracts_downstream", "contract_file_key", "contract_file_storage"),
            ("contracts_downstream", "approval_pdf_key", "approval_pdf_storage"),
            ("contracts_management", "contract_file_key", "contract_file_storage"),
            ("contracts_management", "approval_pdf_key", "approval_pdf_storage"),
            ("project_settlements", "file_key", "storage_provider"),
            ("project_settlements", "audit_report_key", "audit_report_storage"),
            ("project_settlements", "start_report_key", "start_report_storage"),
            ("project_settlements", "completion_report_key", "completion_report_storage"),
            ("expenses_non_contract", "file_key", "storage_provider"),
            ("expenses_non_contract", "approval_pdf_key", "approval_pdf_storage"),
            ("finance_upstream_receivables", "file_key", "storage_provider"),
            ("finance_upstream_invoices", "file_key", "storage_provider"),
            ("finance_upstream_receipts", "file_key", "storage_provider"),
            ("finance_downstream_payables", "file_key", "storage_provider"),
            ("finance_downstream_invoices", "file_key", "storage_provider"),
            ("finance_downstream_payments", "file_key", "storage_provider"),
            ("finance_management_payables", "file_key", "storage_provider"),
            ("finance_management_invoices", "file_key", "storage_provider"),
            ("finance_management_payments", "file_key", "storage_provider"),
            ("downstream_settlements", "file_key", "storage_provider"),
            ("management_settlements", "file_key", "storage_provider"),
        ]

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for table_name, key_col, storage_col in tables_config:
                    cur.execute(
                        """
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = %s
                          AND column_name = %s
                        """,
                        (table_name, key_col),
                    )
                    if not cur.fetchone():
                        logger.warning("Column %s not found in %s, skipping", key_col, table_name)
                        continue

                    cur.execute(
                        f"""
                        SELECT id, {key_col} AS file_key
                        FROM {table_name}
                        WHERE {storage_col} = 'minio'
                          AND {key_col} IS NOT NULL
                        """
                    )
                    for row in cur.fetchall():
                        total_files += 1
                        try:
                            self.minio_client.stat_object(self.bucket_archive, row["file_key"])
                            accessible_files += 1
                        except S3Error:
                            self.errors.append(
                                f"{table_name}[{row['id']}]: file not found in bucket: {row['file_key']}"
                            )
                            all_passed = False
        except Exception as exc:
            self.errors.append(f"MinIO file verification failed: {exc}")
            all_passed = False
        finally:
            conn.close()

        logger.info("Files verified: %s/%s", accessible_files, total_files)
        return all_passed

    def verify_non_destructive_migrations(self, migration_dirs: List[str]) -> bool:
        logger.info("=" * 60)
        logger.info("Non-Destructive Migration Safety Verification")
        logger.info("=" * 60)

        migration_files: List[Path] = []
        for migration_dir in migration_dirs:
            root = Path(migration_dir)
            if not root.exists():
                warning = f"Migration directory not found, skipping: {migration_dir}"
                self.warnings.append(warning)
                logger.warning(warning)
                continue
            migration_files.extend(
                sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in {".py", ".sql"})
            )

        if not migration_files:
            self.warnings.append("No migration files found for safety verification")
            logger.warning("No migration files found for safety verification")
            return True

        for file_path in migration_files:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            safety_text = self._content_for_safety_checks(file_path, text)
            self._check_drop_table(file_path, safety_text)
            self._check_drop_column(file_path, safety_text)
            self._check_file_path_rewrite_without_marker(file_path, safety_text)
            self._check_hard_delete_dictionary(file_path, safety_text)

        if self.safety_violations:
            for violation in self.safety_violations:
                logger.error("SAFETY VIOLATION: %s", violation)
            self.errors.extend(self.safety_violations)
            return False

        logger.info("✓ No destructive migration patterns detected")
        return True

    def _content_for_safety_checks(self, file_path: Path, full_text: str) -> str:
        # For Alembic Python migrations, scan only upgrade() content to avoid
        # flagging expected destructive statements in downgrade() paths.
        if file_path.suffix != ".py":
            return full_text
        match = re.search(
            r"def\s+upgrade\s*\([^)]*\)\s*->\s*None:\s*(.*?)(?:\ndef\s+downgrade\s*\(|\Z)",
            full_text,
            re.DOTALL,
        )
        if match:
            return match.group(1)
        return full_text

    def _check_drop_table(self, file_path: Path, text: str) -> None:
        for pattern in DROP_TABLE_PATTERNS:
            for match in pattern.finditer(text):
                self.safety_violations.append(
                    f"{file_path}: drop-table pattern detected near index {match.start()}"
                )

    def _check_drop_column(self, file_path: Path, text: str) -> None:
        for pattern in DROP_COLUMN_PATTERNS:
            for match in pattern.finditer(text):
                self.safety_violations.append(
                    f"{file_path}: drop-column pattern detected near index {match.start()}"
                )

    def _check_file_path_rewrite_without_marker(self, file_path: Path, text: str) -> None:
        for match in FILE_PATH_REWRITE_PATTERN.finditer(text):
            statement = match.group(0)
            if FILE_FIELD_PATTERN.search(statement) and not BACKUP_MARKER_PATTERN.search(statement):
                snippet = " ".join(statement.split())[:180]
                self.safety_violations.append(
                    f"{file_path}: file-path rewrite without backup_marker: {snippet}"
                )

    def _check_hard_delete_dictionary(self, file_path: Path, text: str) -> None:
        for pattern in HARD_DELETE_DICTIONARY_PATTERNS:
            for match in pattern.finditer(text):
                self.safety_violations.append(
                    f"{file_path}: hard delete on sys_dictionaries detected near index {match.start()}"
                )

    def print_summary(self) -> None:
        logger.info("=" * 60)
        logger.info("Verification Summary")
        logger.info("=" * 60)

        if self.errors:
            logger.error("❌ %s errors found", len(self.errors))
            for err in self.errors:
                logger.error("  - %s", err)
        else:
            logger.info("✓ No errors found")

        if self.warnings:
            logger.warning("⚠️  %s warnings", len(self.warnings))
            for warn in self.warnings:
                logger.warning("  - %s", warn)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify migration integrity and safety.")
    parser.add_argument("--db-only", action="store_true", help="Only verify database.")
    parser.add_argument("--files-only", action="store_true", help="Only verify files.")
    parser.add_argument("--safety-only", action="store_true", help="Only run safety checks.")
    parser.add_argument(
        "--migrations-dir",
        action="append",
        dest="migration_dirs",
        help="Migration directory for safety checks. Can be specified multiple times.",
    )
    args = parser.parse_args()

    selected = [args.db_only, args.files_only, args.safety_only]
    if sum(bool(x) for x in selected) > 1:
        logger.error("Use only one mode flag among --db-only/--files-only/--safety-only")
        return 2

    run_db = False
    run_files = False
    run_safety = False

    if args.db_only:
        run_db = True
    elif args.files_only:
        run_files = True
    elif args.safety_only:
        run_safety = True
    else:
        # Backward-compatible default plus new safety gate.
        run_db = True
        run_files = True
        run_safety = True

    db_url = os.environ.get("DATABASE_URL")
    minio_endpoint = os.environ.get("MINIO_ENDPOINT")
    minio_access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin123")

    verifier = MigrationVerifier(
        db_url=db_url,
        minio_endpoint=minio_endpoint,
        minio_access_key=minio_access_key,
        minio_secret_key=minio_secret_key,
    )
    migration_dirs = args.migration_dirs or ["backend/alembic/versions", "backend/migrations"]

    checks_ok = True
    if run_db:
        checks_ok = verifier.verify_database() and checks_ok
    if run_files:
        checks_ok = verifier.verify_minio_files() and checks_ok
    if run_safety:
        checks_ok = verifier.verify_non_destructive_migrations(migration_dirs) and checks_ok

    verifier.print_summary()
    return 0 if checks_ok and not verifier.errors else 1


if __name__ == "__main__":
    sys.exit(main())
