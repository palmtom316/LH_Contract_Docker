#!/usr/bin/env python3
"""
MinIO File Migration Script - V1.5 Upgrade
============================================
Non-destructive migration of existing files from local storage to MinIO.

This script follows the "只读不删" (read-only, no delete) principle:
- Files are uploaded to MinIO
- Original files are RENAMED (not deleted) with _migrated suffix
- Database records are updated with new storage_provider field

Usage:
    python migrate_to_minio.py --dry-run     # Preview changes without executing
    python migrate_to_minio.py               # Execute migration
    python migrate_to_minio.py --verify      # Verify migration integrity

Environment Variables Required:
    MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY
    DATABASE_URL
"""

import os
import sys
import hashlib
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from minio import Minio
    from minio.error import S3Error
except ImportError:
    print("ERROR: minio package not installed. Run: pip install minio")
    sys.exit(1)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("ERROR: psycopg2 package not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tables with file_path fields that need migration
TABLES_WITH_FILES = [
    # (table_name, file_path_column)
    ("contracts_upstream", "contract_file_path"),
    ("contracts_downstream", "contract_file_path"),
    ("contracts_management", "contract_file_path"),
    ("contracts_management", "approval_pdf_path"),
    ("contracts_upstream", "approval_pdf_path"),
    ("contracts_downstream", "approval_pdf_path"),
    ("finance_upstream_receivables", "file_path"),
    ("finance_upstream_invoices", "file_path"),
    ("finance_upstream_collections", "file_path"),
    ("finance_downstream_payables", "file_path"),
    ("finance_downstream_invoices", "file_path"),
    ("finance_downstream_payments", "file_path"),
    ("finance_management_payables", "file_path"),
    ("finance_management_invoices", "file_path"),
    ("finance_management_payments", "file_path"),
    ("downstream_settlements", "file_path"),
    ("management_settlements", "file_path"),
]


class MinioMigrator:
    """Handles file migration from local storage to MinIO"""
    
    def __init__(
        self,
        minio_endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_archive: str = "contracts-archive",
        db_url: str = None,
        upload_dir: str = "/app/uploads",
        dry_run: bool = False
    ):
        self.minio_endpoint = minio_endpoint
        self.bucket_archive = bucket_archive
        self.upload_dir = Path(upload_dir)
        self.dry_run = dry_run
        self.db_url = db_url
        
        # Initialize MinIO client
        self.client = Minio(
            minio_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False  # Use True for production with HTTPS
        )
        
        # Statistics
        self.stats = {
            "files_found": 0,
            "files_migrated": 0,
            "files_skipped": 0,
            "files_error": 0,
            "bytes_transferred": 0,
        }
    
    def ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        if not self.client.bucket_exists(self.bucket_archive):
            logger.info(f"Creating bucket: {self.bucket_archive}")
            if not self.dry_run:
                self.client.make_bucket(self.bucket_archive)
    
    def calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_db_connection(self):
        """Get database connection"""
        # Parse DATABASE_URL
        if self.db_url.startswith("postgresql+asyncpg://"):
            # Convert async URL to sync
            db_url = self.db_url.replace("postgresql+asyncpg://", "postgresql://")
        else:
            db_url = self.db_url
        return psycopg2.connect(db_url)
    
    def check_storage_columns_exist(self) -> bool:
        """Check if storage migration columns exist in database"""
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'contracts_upstream' 
                    AND column_name = 'storage_provider'
                """)
                return cur.fetchone() is not None
        finally:
            conn.close()
    
    def get_files_to_migrate(self) -> List[Dict]:
        """Get list of files that need migration from database"""
        files = []
        conn = self.get_db_connection()
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for table_name, column_name in TABLES_WITH_FILES:
                    # Check if table and column exist
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = %s
                    """, (table_name, column_name))
                    
                    if not cur.fetchone():
                        logger.debug(f"Column {column_name} not found in {table_name}, skipping")
                        continue
                    
                    # Get files that haven't been migrated yet
                    # If storage_provider column exists, filter by it
                    if self.check_storage_columns_exist():
                        query = f"""
                            SELECT id, {column_name} as file_path 
                            FROM {table_name} 
                            WHERE {column_name} IS NOT NULL 
                            AND {column_name} != ''
                            AND (storage_provider IS NULL OR storage_provider = 'local')
                        """
                    else:
                        query = f"""
                            SELECT id, {column_name} as file_path 
                            FROM {table_name} 
                            WHERE {column_name} IS NOT NULL 
                            AND {column_name} != ''
                        """
                    
                    cur.execute(query)
                    
                    for row in cur.fetchall():
                        files.append({
                            "table": table_name,
                            "column": column_name,
                            "id": row["id"],
                            "file_path": row["file_path"]
                        })
        finally:
            conn.close()
        
        return files
    
    def migrate_file(self, file_info: Dict) -> Tuple[bool, str]:
        """
        Migrate a single file to MinIO.
        Returns (success, message)
        """
        file_path_str = file_info["file_path"]
        
        # Handle relative and absolute paths
        if file_path_str.startswith("/"):
            local_path = Path(file_path_str)
        else:
            local_path = self.upload_dir / file_path_str
        
        if not local_path.exists():
            return False, f"File not found: {local_path}"
        
        # Generate MinIO object key
        # Format: archive/YYYY/MM/original_filename
        timestamp = datetime.now()
        minio_key = f"archive/{timestamp.year}/{timestamp.month:02d}/{local_path.name}"
        
        # Check if already exists in MinIO (idempotency)
        try:
            self.client.stat_object(self.bucket_archive, minio_key)
            return True, f"Already exists in MinIO: {minio_key}"
        except S3Error:
            pass  # Object doesn't exist, proceed with upload
        
        # Calculate MD5 before upload
        md5_before = self.calculate_md5(local_path)
        file_size = local_path.stat().st_size
        
        if self.dry_run:
            return True, f"[DRY-RUN] Would upload {local_path} -> {minio_key}"
        
        # Upload to MinIO
        try:
            self.client.fput_object(
                self.bucket_archive,
                minio_key,
                str(local_path),
                content_type=self._get_content_type(local_path)
            )
        except S3Error as e:
            return False, f"MinIO upload failed: {e}"
        
        # Verify upload by checking MD5
        try:
            stat = self.client.stat_object(self.bucket_archive, minio_key)
            # MinIO returns etag which is MD5 for single-part uploads
            minio_etag = stat.etag.strip('"')
            if minio_etag != md5_before:
                return False, f"MD5 mismatch after upload! Local: {md5_before}, MinIO: {minio_etag}"
        except S3Error as e:
            return False, f"Verification failed: {e}"
        
        # Rename original file (non-destructive)
        migrated_path = local_path.with_name(f"_migrated_{local_path.name}")
        try:
            local_path.rename(migrated_path)
        except OSError as e:
            logger.warning(f"Could not rename original file: {e}")
        
        # Update database record
        self._update_db_record(file_info, minio_key)
        
        self.stats["bytes_transferred"] += file_size
        return True, f"Migrated: {local_path} -> {minio_key}"
    
    def _get_content_type(self, path: Path) -> str:
        """Get content type based on file extension"""
        ext = path.suffix.lower()
        content_types = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        return content_types.get(ext, "application/octet-stream")
    
    def _update_db_record(self, file_info: Dict, minio_key: str):
        """Update database record with MinIO key"""
        if self.dry_run:
            return
        
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cur:
                # Check if new columns exist
                if self.check_storage_columns_exist():
                    # Update with new storage info
                    cur.execute(f"""
                        UPDATE {file_info['table']} 
                        SET file_key = %s, storage_provider = 'minio'
                        WHERE id = %s
                    """, (minio_key, file_info['id']))
                conn.commit()
        finally:
            conn.close()
    
    def run_migration(self):
        """Execute the full migration"""
        logger.info("=" * 60)
        logger.info("MinIO File Migration - V1.5 Upgrade")
        logger.info("=" * 60)
        
        if self.dry_run:
            logger.info("🔍 DRY RUN MODE - No changes will be made")
        
        # Ensure bucket exists
        self.ensure_bucket_exists()
        
        # Get files to migrate
        logger.info("Scanning database for files to migrate...")
        files = self.get_files_to_migrate()
        self.stats["files_found"] = len(files)
        
        logger.info(f"Found {len(files)} files to migrate")
        
        # Migrate each file
        for i, file_info in enumerate(files, 1):
            logger.info(f"[{i}/{len(files)}] Processing: {file_info['file_path']}")
            
            success, message = self.migrate_file(file_info)
            
            if success:
                self.stats["files_migrated"] += 1
                logger.info(f"  ✓ {message}")
            else:
                self.stats["files_error"] += 1
                logger.error(f"  ✗ {message}")
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print migration summary"""
        logger.info("=" * 60)
        logger.info("Migration Summary")
        logger.info("=" * 60)
        logger.info(f"Files found:      {self.stats['files_found']}")
        logger.info(f"Files migrated:   {self.stats['files_migrated']}")
        logger.info(f"Files skipped:    {self.stats['files_skipped']}")
        logger.info(f"Files with error: {self.stats['files_error']}")
        logger.info(f"Bytes transferred: {self.stats['bytes_transferred'] / (1024*1024):.2f} MB")
    
    def verify_migration(self):
        """Verify all migrated files are accessible in MinIO"""
        logger.info("Verifying migration integrity...")
        
        conn = self.get_db_connection()
        errors = []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for table_name, _ in TABLES_WITH_FILES:
                    if not self.check_storage_columns_exist():
                        continue
                    
                    cur.execute(f"""
                        SELECT id, file_key 
                        FROM {table_name} 
                        WHERE storage_provider = 'minio' 
                        AND file_key IS NOT NULL
                    """)
                    
                    for row in cur.fetchall():
                        try:
                            self.client.stat_object(self.bucket_archive, row["file_key"])
                        except S3Error:
                            errors.append(f"{table_name}[{row['id']}]: {row['file_key']}")
        finally:
            conn.close()
        
        if errors:
            logger.error(f"Found {len(errors)} missing files in MinIO:")
            for err in errors[:10]:
                logger.error(f"  - {err}")
        else:
            logger.info("✓ All migrated files verified successfully")


def main():
    parser = argparse.ArgumentParser(description="Migrate files from local storage to MinIO")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    parser.add_argument("--verify", action="store_true", help="Verify migration integrity")
    args = parser.parse_args()
    
    # Get configuration from environment
    minio_endpoint = os.environ.get("MINIO_ENDPOINT", "minio:9000")
    access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin123")
    db_url = os.environ.get("DATABASE_URL")
    upload_dir = os.environ.get("UPLOAD_DIR", "/app/uploads")
    
    if not db_url:
        logger.error("DATABASE_URL environment variable is required")
        sys.exit(1)
    
    migrator = MinioMigrator(
        minio_endpoint=minio_endpoint,
        access_key=access_key,
        secret_key=secret_key,
        db_url=db_url,
        upload_dir=upload_dir,
        dry_run=args.dry_run
    )
    
    if args.verify:
        migrator.verify_migration()
    else:
        migrator.run_migration()


if __name__ == "__main__":
    main()
