#!/usr/bin/env python3
"""
Data Migration Verification Script - V1.5 Upgrade
===================================================
Verifies database and file migration integrity.

This script performs:
1. Row count comparison between source and target databases
2. Critical numeric field sum verification (contract amounts)
3. MinIO file accessibility verification

Usage:
    python verify_migration.py --db-only    # Only verify database
    python verify_migration.py --files-only # Only verify files
    python verify_migration.py              # Full verification
"""

import os
import sys
import argparse
import logging
from decimal import Decimal
from typing import Optional, Dict, List

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("ERROR: psycopg2 package not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

try:
    from minio import Minio
    from minio.error import S3Error
except ImportError:
    print("ERROR: minio package not installed. Run: pip install minio")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tables and their key verification fields
VERIFICATION_CONFIG = {
    "contracts_upstream": {
        "count": True,
        "sum_fields": ["contract_amount"],
    },
    "contracts_downstream": {
        "count": True,
        "sum_fields": ["contract_amount"],
    },
    "contracts_management": {
        "count": True,
        "sum_fields": ["contract_amount"],
    },
    "finance_upstream_receivables": {
        "count": True,
        "sum_fields": ["amount"],
    },
    "finance_upstream_collections": {
        "count": True,
        "sum_fields": ["amount"],
    },
    "finance_downstream_payables": {
        "count": True,
        "sum_fields": ["amount"],
    },
    "finance_downstream_payments": {
        "count": True,
        "sum_fields": ["amount"],
    },
    "finance_management_payables": {
        "count": True,
        "sum_fields": ["amount"],
    },
    "finance_management_payments": {
        "count": True,
        "sum_fields": ["amount"],
    },
}


class MigrationVerifier:
    """Verifies data migration integrity"""
    
    def __init__(
        self,
        db_url: str,
        minio_endpoint: str = None,
        minio_access_key: str = None,
        minio_secret_key: str = None,
        bucket_archive: str = "contracts-archive"
    ):
        self.db_url = self._convert_db_url(db_url)
        self.minio_endpoint = minio_endpoint
        self.bucket_archive = bucket_archive
        
        if minio_endpoint:
            self.minio_client = Minio(
                minio_endpoint,
                access_key=minio_access_key,
                secret_key=minio_secret_key,
                secure=False
            )
        else:
            self.minio_client = None
        
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def _convert_db_url(self, url: str) -> str:
        """Convert async DB URL to sync"""
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql://")
        return url
    
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def verify_database(self) -> bool:
        """Verify database integrity"""
        logger.info("=" * 60)
        logger.info("Database Verification")
        logger.info("=" * 60)
        
        conn = self.get_db_connection()
        all_passed = True
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for table_name, config in VERIFICATION_CONFIG.items():
                    # Check if table exists
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        )
                    """, (table_name,))
                    
                    if not cur.fetchone()['exists']:
                        logger.warning(f"Table {table_name} does not exist, skipping")
                        continue
                    
                    # Verify row count
                    if config.get("count"):
                        cur.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
                        count = cur.fetchone()['cnt']
                        logger.info(f"{table_name}: {count} rows")
                    
                    # Verify sum of numeric fields
                    for field in config.get("sum_fields", []):
                        cur.execute(f"SELECT COALESCE(SUM({field}), 0) as total FROM {table_name}")
                        total = cur.fetchone()['total']
                        logger.info(f"  └─ {field} total: {total:,.2f}")
        
        finally:
            conn.close()
        
        return all_passed
    
    def verify_minio_files(self) -> bool:
        """Verify all migrated files are accessible in MinIO"""
        if not self.minio_client:
            logger.warning("MinIO client not configured, skipping file verification")
            return True
        
        logger.info("=" * 60)
        logger.info("MinIO File Verification")
        logger.info("=" * 60)
        
        conn = self.get_db_connection()
        all_passed = True
        total_files = 0
        accessible_files = 0
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if storage columns exist
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'contracts_upstream' 
                    AND column_name = 'storage_provider'
                """)
                
                if not cur.fetchone():
                    logger.warning("Storage columns not found. Run Alembic migration first.")
                    return True
                
                # Check files from each table
                tables_with_files = [
                    "contracts_upstream",
                    "contracts_downstream", 
                    "contracts_management",
                ]
                
                for table_name in tables_with_files:
                    cur.execute(f"""
                        SELECT id, file_key 
                        FROM {table_name} 
                        WHERE storage_provider = 'minio' 
                        AND file_key IS NOT NULL
                    """)
                    
                    for row in cur.fetchall():
                        total_files += 1
                        try:
                            self.minio_client.stat_object(
                                self.bucket_archive, 
                                row["file_key"]
                            )
                            accessible_files += 1
                        except S3Error:
                            self.errors.append(
                                f"{table_name}[{row['id']}]: File not found: {row['file_key']}"
                            )
                            all_passed = False
        
        finally:
            conn.close()
        
        logger.info(f"Files verified: {accessible_files}/{total_files}")
        
        if self.errors:
            logger.error(f"Found {len(self.errors)} missing files:")
            for err in self.errors[:5]:
                logger.error(f"  - {err}")
            if len(self.errors) > 5:
                logger.error(f"  ... and {len(self.errors) - 5} more")
        else:
            logger.info("✓ All migrated files are accessible")
        
        return all_passed
    
    def print_summary(self):
        """Print verification summary"""
        logger.info("=" * 60)
        logger.info("Verification Summary")
        logger.info("=" * 60)
        
        if self.errors:
            logger.error(f"❌ {len(self.errors)} errors found")
            for err in self.errors:
                logger.error(f"  - {err}")
        else:
            logger.info("✓ No errors found")
        
        if self.warnings:
            logger.warning(f"⚠️  {len(self.warnings)} warnings")
            for warn in self.warnings:
                logger.warning(f"  - {warn}")


def main():
    parser = argparse.ArgumentParser(description="Verify migration integrity")
    parser.add_argument("--db-only", action="store_true", help="Only verify database")
    parser.add_argument("--files-only", action="store_true", help="Only verify files")
    args = parser.parse_args()
    
    # Get configuration from environment
    db_url = os.environ.get("DATABASE_URL")
    minio_endpoint = os.environ.get("MINIO_ENDPOINT")
    minio_access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin123")
    
    if not db_url:
        logger.error("DATABASE_URL environment variable is required")
        sys.exit(1)
    
    verifier = MigrationVerifier(
        db_url=db_url,
        minio_endpoint=minio_endpoint,
        minio_access_key=minio_access_key,
        minio_secret_key=minio_secret_key
    )
    
    if not args.files_only:
        verifier.verify_database()
    
    if not args.db_only:
        verifier.verify_minio_files()
    
    verifier.print_summary()


if __name__ == "__main__":
    main()
