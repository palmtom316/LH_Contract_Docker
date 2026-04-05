"""
File compatibility tests for legacy paths and auth transport.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from starlette.requests import Request
from starlette.responses import FileResponse, StreamingResponse

from app.config import settings
from app.routers import common


def _build_request(headers: dict[str, str] | None = None) -> Request:
    raw_headers = []
    for key, value in (headers or {}).items():
        raw_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/common/files/test",
        "headers": raw_headers,
        "query_string": b"",
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_legacy_uploads_path_still_downloads_with_auth_header(monkeypatch, tmp_path):
    original_upload_dir = settings.UPLOAD_DIR
    legacy_relative_path = "legacy/contracts/2025/scan.pdf"
    local_file = tmp_path / legacy_relative_path
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_bytes(b"legacy")

    async def fake_get_user_from_token(token, db):
        return SimpleNamespace(username="tester", is_active=True)

    class MissingMinioClient:
        def stat_object(self, bucket, path):
            raise RuntimeError("not found")

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)
    monkeypatch.setattr(common, "get_minio_client", lambda: MissingMinioClient())
    settings.UPLOAD_DIR = str(tmp_path)

    try:
        response = await common.get_file(
            path=legacy_relative_path,
            request=_build_request({"authorization": "Bearer token-123"}),
            db=object(),
        )
    finally:
        settings.UPLOAD_DIR = original_upload_dir

    assert isinstance(response, FileResponse)
    assert response.status_code == 200
    assert response.path == str(local_file)


@pytest.mark.asyncio
async def test_minio_key_download_works_without_query_token(monkeypatch):
    expected = b"minio-payload"

    async def fake_get_user_from_token(token, db):
        assert token == "cookie-token"
        return SimpleNamespace(username="tester", is_active=True)

    class FakeObjectResponse:
        def stream(self, chunk_size):
            yield expected

        def close(self):
            return None

        def release_conn(self):
            return None

    class FakeMinioClient:
        def stat_object(self, bucket, path):
            assert path == "contracts/2026/04/demo.pdf"
            return SimpleNamespace(size=len(expected))

        def get_object(self, bucket, path):
            assert path == "contracts/2026/04/demo.pdf"
            return FakeObjectResponse()

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)
    monkeypatch.setattr(common, "get_minio_client", lambda: FakeMinioClient())
    monkeypatch.setattr(settings, "ALLOW_QUERY_TOKEN", False)

    response = await common.get_file(
        path="contracts/2026/04/demo.pdf",
        request=_build_request({"cookie": "lh_access_token=cookie-token"}),
        db=object(),
    )

    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    assert isinstance(response, StreamingResponse)
    assert response.status_code == 200
    assert body == expected
