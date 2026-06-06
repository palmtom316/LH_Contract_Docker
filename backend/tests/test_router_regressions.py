from pathlib import Path

import pytest
from fastapi.responses import FileResponse

from app.routers.audit import list_archives
from app.routers.contracts_upstream import download_import_template
from app.services import audit_archive_service
from app.config import settings


@pytest.mark.asyncio
async def test_list_archives_formats_created_at_without_name_error(tmp_path, monkeypatch):
    archive_file = tmp_path / "audit_logs_archive_20260408.json"
    archive_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(audit_archive_service, "ARCHIVE_DIR", tmp_path)

    response = await list_archives(current_user=None)

    assert response["total"] == 1
    assert response["archives"][0]["filename"] == archive_file.name
    assert "created_at" in response["archives"][0]


@pytest.mark.asyncio
async def test_download_import_template_creates_excel_file_without_name_error(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    response = await download_import_template()

    assert isinstance(response, FileResponse)
    assert Path(response.path).exists()
    assert Path(response.path).name == "upstream_contracts_import_template.xlsx"
