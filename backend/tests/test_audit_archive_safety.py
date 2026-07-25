from unittest.mock import AsyncMock

import pytest

from app.services.audit_archive_service import AuditLogArchiveService


@pytest.mark.asyncio
async def test_archive_verification_failure_prevents_database_deletion(monkeypatch):
    service = object.__new__(AuditLogArchiveService)
    service.db = None
    service.count_logs_before_date = AsyncMock(return_value=3)
    service.export_logs_to_json = AsyncMock(return_value="/tmp/truncated-audit.json")
    service.delete_logs_before_date = AsyncMock()

    def reject_truncated_archive(*_args):
        raise ValueError("archive count mismatch")

    monkeypatch.setattr(service, "verify_archive_file", reject_truncated_archive)

    with pytest.raises(ValueError, match="archive count mismatch"):
        await service.archive_old_logs(days=90, delete_after_export=True)

    service.delete_logs_before_date.assert_not_awaited()
