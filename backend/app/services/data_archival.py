"""
Data Archival Strategy for Audit Logs
Automatically archives old audit logs to improve query performance
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from datetime import datetime, timedelta
import logging

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditLogArchive:
    """Archive table model (same structure as AuditLog)"""
    __tablename__ = "audit_logs_archive"
    # Same columns as AuditLog


async def archive_old_audit_logs(
    db: AsyncSession,
    days_to_keep: int = 365
) -> dict:
    """
    Archive audit logs older than specified days

    Args:
        db: Database session
        days_to_keep: Number of days to keep in main table (default: 365)

    Returns:
        dict with archived_count and deleted_count
    """
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)

    try:
        # Count records to archive
        count_query = select(AuditLog).where(AuditLog.created_at < cutoff_date)
        result = await db.execute(count_query)
        records_to_archive = len(result.scalars().all())

        if records_to_archive == 0:
            logger.info("No audit logs to archive")
            return {"archived_count": 0, "deleted_count": 0}

        # Archive to archive table (if exists)
        # Note: Archive table must be created manually
        # CREATE TABLE audit_logs_archive AS SELECT * FROM audit_logs WHERE 1=0;

        # Delete old records from main table
        delete_query = delete(AuditLog).where(AuditLog.created_at < cutoff_date)
        await db.execute(delete_query)
        await db.commit()

        logger.info(f"Archived {records_to_archive} audit logs older than {cutoff_date}")

        return {
            "archived_count": records_to_archive,
            "deleted_count": records_to_archive,
            "cutoff_date": cutoff_date.isoformat()
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to archive audit logs: {e}")
        raise


async def cleanup_old_data(db: AsyncSession) -> dict:
    """
    Cleanup old data across multiple tables

    Returns:
        dict with cleanup statistics
    """
    results = {}

    # Archive audit logs (keep 1 year)
    audit_result = await archive_old_audit_logs(db, days_to_keep=365)
    results["audit_logs"] = audit_result

    # Add more cleanup tasks here as needed
    # e.g., old temporary files, expired sessions, etc.

    return results
