"""
Audit Log Archive Service
Provides functionality to archive old audit logs to improve database performance.

Features:
- Archive logs older than specified days
- Export to JSON/CSV files before deletion
- Scheduled cleanup capability
- Retention policy enforcement
"""
import logging
import json
import csv
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, and_
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.config import settings

logger = logging.getLogger(__name__)

# Archive directory
ARCHIVE_DIR = Path(settings.UPLOAD_DIR).parent / "archives" / "audit_logs"


class AuditLogArchiveService:
    """
    Service for archiving and managing audit logs.
    
    Usage:
        service = AuditLogArchiveService(db)
        result = await service.archive_old_logs(days=90)
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._ensure_archive_dir()
    
    def _ensure_archive_dir(self):
        """Ensure archive directory exists"""
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    async def get_log_statistics(self) -> Dict[str, Any]:
        """
        Get audit log statistics.
        
        Returns:
            Dictionary with log counts and date ranges
        """
        try:
            # Total count
            total_result = await self.db.execute(
                select(func.count(AuditLog.id))
            )
            total_count = total_result.scalar() or 0
            
            # Date range
            date_result = await self.db.execute(
                select(
                    func.min(AuditLog.created_at),
                    func.max(AuditLog.created_at)
                )
            )
            date_row = date_result.first()
            oldest_date = date_row[0] if date_row else None
            newest_date = date_row[1] if date_row else None
            
            # Count by action
            action_result = await self.db.execute(
                select(
                    AuditLog.action,
                    func.count(AuditLog.id)
                ).group_by(AuditLog.action)
            )
            action_counts = {row[0]: row[1] for row in action_result.all()}
            
            # Size estimate (rough: 1KB per log)
            estimated_size_mb = total_count * 1024 / (1024 * 1024)
            
            return {
                "total_count": total_count,
                "oldest_log": oldest_date.isoformat() if oldest_date else None,
                "newest_log": newest_date.isoformat() if newest_date else None,
                "action_breakdown": action_counts,
                "estimated_size_mb": round(estimated_size_mb, 2)
            }
        except Exception as e:
            logger.error(f"Failed to get log statistics: {e}")
            raise
    
    async def count_logs_before_date(self, before_date: datetime) -> int:
        """
        Count logs before a specific date.
        
        Args:
            before_date: Cutoff date
            
        Returns:
            Number of logs before the date
        """
        result = await self.db.execute(
            select(func.count(AuditLog.id)).where(
                AuditLog.created_at < before_date
            )
        )
        return result.scalar() or 0
    
    async def export_logs_to_json(
        self, 
        before_date: datetime,
        batch_size: int = 1000
    ) -> str:
        """
        Export audit logs to JSON file.
        
        Args:
            before_date: Export logs before this date
            batch_size: Number of records per batch
            
        Returns:
            Path to the exported file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_logs_archive_{timestamp}.json"
        filepath = ARCHIVE_DIR / filename
        
        logs_data = []
        offset = 0
        
        while True:
            result = await self.db.execute(
                select(AuditLog)
                .where(AuditLog.created_at < before_date)
                .order_by(AuditLog.created_at)
                .offset(offset)
                .limit(batch_size)
            )
            batch = result.scalars().all()
            
            if not batch:
                break
            
            for log in batch:
                logs_data.append({
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.username,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "description": log.description,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "old_values": log.old_values,
                    "new_values": log.new_values,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                })
            
            offset += batch_size
            logger.info(f"Exported {offset} audit logs...")
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "export_date": datetime.now().isoformat(),
                "before_date": before_date.isoformat(),
                "total_records": len(logs_data),
                "logs": logs_data
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(logs_data)} logs to {filepath}")
        return str(filepath)
    
    async def export_logs_to_csv(
        self,
        before_date: datetime,
        batch_size: int = 1000
    ) -> str:
        """
        Export audit logs to CSV file.
        
        Args:
            before_date: Export logs before this date
            batch_size: Number of records per batch
            
        Returns:
            Path to the exported file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_logs_archive_{timestamp}.csv"
        filepath = ARCHIVE_DIR / filename
        
        fieldnames = [
            "id", "user_id", "username", "action", "resource_type",
            "resource_id", "description", "ip_address", "user_agent",
            "old_values", "new_values", "created_at"
        ]
        
        offset = 0
        total_exported = 0
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            while True:
                result = await self.db.execute(
                    select(AuditLog)
                    .where(AuditLog.created_at < before_date)
                    .order_by(AuditLog.created_at)
                    .offset(offset)
                    .limit(batch_size)
                )
                batch = result.scalars().all()
                
                if not batch:
                    break
                
                for log in batch:
                    writer.writerow({
                        "id": log.id,
                        "user_id": log.user_id,
                        "username": log.username,
                        "action": log.action,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "description": log.description,
                        "ip_address": log.ip_address,
                        "user_agent": log.user_agent,
                        "old_values": json.dumps(log.old_values) if log.old_values else "",
                        "new_values": json.dumps(log.new_values) if log.new_values else "",
                        "created_at": log.created_at.isoformat() if log.created_at else ""
                    })
                    total_exported += 1
                
                offset += batch_size
                logger.info(f"Exported {offset} audit logs to CSV...")
        
        logger.info(f"Exported {total_exported} logs to {filepath}")
        return str(filepath)
    
    async def delete_logs_before_date(self, before_date: datetime) -> int:
        """
        Delete audit logs before a specific date.
        
        Args:
            before_date: Delete logs before this date
            
        Returns:
            Number of deleted logs
        """
        result = await self.db.execute(
            delete(AuditLog).where(AuditLog.created_at < before_date)
        )
        await self.db.commit()
        
        deleted_count = result.rowcount
        logger.info(f"Deleted {deleted_count} audit logs before {before_date}")
        return deleted_count
    
    async def archive_old_logs(
        self,
        days: int = 90,
        export_format: str = "json",
        delete_after_export: bool = True
    ) -> Dict[str, Any]:
        """
        Archive and optionally delete old audit logs.
        
        Args:
            days: Archive logs older than this many days
            export_format: "json" or "csv"
            delete_after_export: Whether to delete logs after exporting
            
        Returns:
            Dictionary with archive results
        """
        before_date = datetime.now() - timedelta(days=days)
        
        # Count logs to archive
        count = await self.count_logs_before_date(before_date)
        
        if count == 0:
            return {
                "success": True,
                "message": f"没有超过 {days} 天的审计日志需要归档",
                "archived_count": 0,
                "deleted_count": 0,
                "archive_file": None
            }
        
        # Export logs
        if export_format.lower() == "csv":
            archive_file = await self.export_logs_to_csv(before_date)
        else:
            archive_file = await self.export_logs_to_json(before_date)
        
        # Delete logs if requested
        deleted_count = 0
        if delete_after_export:
            deleted_count = await self.delete_logs_before_date(before_date)
        
        return {
            "success": True,
            "message": f"成功归档 {count} 条审计日志",
            "archived_count": count,
            "deleted_count": deleted_count,
            "archive_file": archive_file,
            "before_date": before_date.isoformat()
        }
    
    async def cleanup_old_archives(self, keep_days: int = 365) -> int:
        """
        Clean up old archive files.
        
        Args:
            keep_days: Keep archives newer than this many days
            
        Returns:
            Number of deleted archive files
        """
        if not ARCHIVE_DIR.exists():
            return 0
        
        cutoff = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0
        
        for filepath in ARCHIVE_DIR.glob("audit_logs_archive_*"):
            if filepath.is_file():
                file_mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if file_mtime < cutoff:
                    filepath.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old archive: {filepath}")
        
        return deleted_count
    
    def list_archives(self) -> List[Dict[str, Any]]:
        """
        List all archive files.
        
        Returns:
            List of archive file information
        """
        if not ARCHIVE_DIR.exists():
            return []
        
        archives = []
        for filepath in sorted(ARCHIVE_DIR.glob("audit_logs_archive_*"), reverse=True):
            if filepath.is_file():
                stat = filepath.stat()
                archives.append({
                    "filename": filepath.name,
                    "path": str(filepath),
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return archives


# Convenience function for scheduling
async def run_scheduled_archive(db: AsyncSession, days: int = 90):
    """
    Run scheduled audit log archive.
    Can be called from a scheduler/cron job.
    """
    try:
        service = AuditLogArchiveService(db)
        result = await service.archive_old_logs(days=days)
        logger.info(f"Scheduled archive completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Scheduled archive failed: {e}")
        raise
