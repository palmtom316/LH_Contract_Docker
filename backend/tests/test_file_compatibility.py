"""
File compatibility tests for legacy paths and auth transport.
"""
from __future__ import annotations

import os
import re
import io
from types import SimpleNamespace

import pytest
from fastapi import UploadFile
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request
from starlette.responses import FileResponse, StreamingResponse

from app.config import settings
from app.main import app
from app.models.user import UserRole
from app.models.system import SystemConfig
from app.routers import common, system as system_router
from app.database import get_db


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
async def test_upload_accepts_controlled_subdir_and_custom_filename(monkeypatch):
    captured = {}

    class FakeMinioClient:
        def put_object(self, bucket, object_name, data, length, content_type):
            captured["bucket"] = bucket
            captured["object_name"] = object_name
            captured["length"] = length
            captured["content_type"] = content_type

    async def fake_validate_file_upload(file):
        return "contract.pdf"

    monkeypatch.setattr(common, "validate_file_upload", fake_validate_file_upload)
    monkeypatch.setattr("app.core.minio.get_minio_client", lambda: FakeMinioClient())
    monkeypatch.setattr("app.core.minio.ensure_bucket_exists", lambda client, bucket: None)
    monkeypatch.setattr(common.uuid, "uuid4", lambda: "fixed-uuid")
    monkeypatch.setattr(settings, "MINIO_BUCKET_CONTRACTS", "contracts-active")

    upload = UploadFile(
        filename="contract.pdf",
        file=io.BytesIO(b"%PDF-1.4\n%%EOF"),
        headers={"content-type": "application/pdf"},
    )
    response = await common.upload_file(
        file=upload,
        subdir="upstream/contract",
        custom_filename="001_contract.pdf",
        current_user=SimpleNamespace(username="tester"),
    )

    assert captured["bucket"] == "contracts-active"
    assert captured["content_type"] == "application/pdf"
    assert captured["length"] > 0
    assert re.match(r"^contracts/upstream/\d{4}/\d{2}/fixed-uuid_001_contract\.pdf$", captured["object_name"])
    assert response["path"] == captured["object_name"]
    assert response["key"] == captured["object_name"]
    assert response["storage_provider"] == "minio"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("subdir", "expected_prefix"),
    [
        ("downstream/contract", "contracts/downstream"),
        ("management/contract", "contracts/management"),
        ("upstream/invoice", "invoices/upstream"),
        ("upstream/settlement/start", "settlements/upstream/start"),
        ("downstream/payment", "payments/downstream"),
        ("management/settlement", "settlements/management"),
    ],
)
async def test_upload_routes_documents_to_stable_category_prefixes(
    monkeypatch,
    subdir,
    expected_prefix,
):
    captured = {}

    class FakeMinioClient:
        def put_object(self, bucket, object_name, data, length, content_type):
            captured["object_name"] = object_name

    async def fake_validate_file_upload(file):
        return "document.pdf"

    monkeypatch.setattr(common, "validate_file_upload", fake_validate_file_upload)
    monkeypatch.setattr("app.core.minio.get_minio_client", lambda: FakeMinioClient())
    monkeypatch.setattr("app.core.minio.ensure_bucket_exists", lambda client, bucket: None)
    monkeypatch.setattr(common.uuid, "uuid4", lambda: "fixed-uuid")

    upload = UploadFile(
        filename="document.pdf",
        file=io.BytesIO(b"%PDF-1.4\n%%EOF"),
        headers={"content-type": "application/pdf"},
    )
    await common.upload_file(
        file=upload,
        subdir=subdir,
        current_user=SimpleNamespace(username="tester"),
    )

    assert captured["object_name"].startswith(f"{expected_prefix}/")


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

    async def fake_user_can_access_file_path(path, db, current_user):
        return True

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)
    monkeypatch.setattr(common, "user_can_access_file_path", fake_user_can_access_file_path)
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
async def test_admin_can_download_unlinked_legacy_local_upload(monkeypatch, tmp_path):
    original_upload_dir = settings.UPLOAD_DIR
    legacy_relative_path = "legacy/contracts/2025/admin-scan.pdf"
    local_file = tmp_path / legacy_relative_path
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_bytes(b"legacy")

    async def fake_get_user_from_token(token, db):
        return SimpleNamespace(username="admin", is_active=True, is_superuser=False, role=UserRole.ADMIN)

    class MissingMinioClient:
        def stat_object(self, bucket, path):
            raise RuntimeError("not found")

    async def fake_user_can_access_file_path(path, db, current_user):
        return False

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)
    monkeypatch.setattr(common, "user_can_access_file_path", fake_user_can_access_file_path)
    monkeypatch.setattr(common, "get_minio_client", lambda: MissingMinioClient())
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    try:
        response = await common.get_file(
            path=legacy_relative_path,
            request=_build_request({"authorization": "Bearer token-123"}),
            db=object(),
        )
    finally:
        monkeypatch.setattr(settings, "UPLOAD_DIR", original_upload_dir)

    assert isinstance(response, FileResponse)
    assert response.status_code == 200
    assert response.path == str(local_file)


@pytest.mark.asyncio
async def test_non_admin_cannot_download_unlinked_legacy_local_upload(monkeypatch, tmp_path):
    original_upload_dir = settings.UPLOAD_DIR
    legacy_relative_path = "legacy/contracts/2025/user-scan.pdf"
    local_file = tmp_path / legacy_relative_path
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_bytes(b"legacy")

    async def fake_get_user_from_token(token, db):
        return SimpleNamespace(username="tester", is_active=True, is_superuser=False, role=UserRole.BIDDING)

    class MissingMinioClient:
        def stat_object(self, bucket, path):
            raise RuntimeError("not found")

    async def fake_user_can_access_file_path(path, db, current_user):
        return False

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)
    monkeypatch.setattr(common, "user_can_access_file_path", fake_user_can_access_file_path)
    monkeypatch.setattr(common, "get_minio_client", lambda: MissingMinioClient())
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    try:
        with pytest.raises(common.PermissionDeniedError):
            await common.get_file(
                path=legacy_relative_path,
                request=_build_request({"authorization": "Bearer token-123"}),
                db=object(),
            )
    finally:
        monkeypatch.setattr(settings, "UPLOAD_DIR", original_upload_dir)


@pytest.mark.asyncio
async def test_legacy_uploads_prefix_is_normalized_for_local_fallback(monkeypatch, tmp_path):
    original_upload_dir = settings.UPLOAD_DIR
    local_relative_path = "contracts/2025/scan.pdf"
    local_file = tmp_path / local_relative_path
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_bytes(b"legacy")

    async def fake_get_user_from_token(token, db):
        return SimpleNamespace(username="tester", is_active=True)

    class MissingMinioClient:
        def stat_object(self, bucket, path):
            raise RuntimeError("not found")

    async def fake_user_can_access_file_path(path, db, current_user):
        assert path == local_relative_path
        return True

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)
    monkeypatch.setattr(common, "user_can_access_file_path", fake_user_can_access_file_path)
    monkeypatch.setattr(common, "get_minio_client", lambda: MissingMinioClient())
    settings.UPLOAD_DIR = str(tmp_path)

    try:
        for legacy_path in (
            f"uploads/{local_relative_path}",
            f"/uploads/{local_relative_path}",
            f"/app/uploads/{local_relative_path}",
        ):
            response = await common.get_file(
                path=legacy_path,
                request=_build_request({"authorization": "Bearer token-123"}),
                db=object(),
            )
            assert isinstance(response, FileResponse)
            assert response.status_code == 200
            assert response.path == str(local_file)
    finally:
        settings.UPLOAD_DIR = original_upload_dir


@pytest.mark.asyncio
async def test_minio_key_download_works_without_query_token(monkeypatch):
    expected = b"minio-payload"

    async def fake_get_user_from_token(token, db):
        assert token == "header-token"
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

    async def fake_user_can_access_file_path(path, db, current_user):
        return True

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)
    monkeypatch.setattr(common, "user_can_access_file_path", fake_user_can_access_file_path)
    monkeypatch.setattr(common, "get_minio_client", lambda: FakeMinioClient())
    response = await common.get_file(
        path="contracts/2026/04/demo.pdf",
        request=_build_request({"authorization": "Bearer header-token"}),
        db=object(),
    )

    assert isinstance(response, StreamingResponse)
    assert response.status_code == 200
    assert response.headers["content-length"] == str(len(expected))
    assert response.media_type == "application/pdf"


@pytest.mark.asyncio
async def test_minio_download_supports_chinese_inline_filename(monkeypatch):
    expected = b"pdf"
    path = "contracts/upstream/2026/07/fixed-id_中文合同文件.pdf"

    async def fake_get_user_from_token(token, db):
        return SimpleNamespace(username="tester", is_active=True)

    class FakeObjectResponse:
        def stream(self, chunk_size):
            yield expected

        def close(self):
            return None

        def release_conn(self):
            return None

    class FakeMinioClient:
        def stat_object(self, bucket, object_name):
            assert object_name == path
            return SimpleNamespace(size=len(expected))

        def get_object(self, bucket, object_name):
            assert object_name == path
            return FakeObjectResponse()

    async def fake_user_can_access_file_path(object_name, db, current_user):
        return True

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)
    monkeypatch.setattr(common, "user_can_access_file_path", fake_user_can_access_file_path)
    monkeypatch.setattr(common, "get_minio_client", lambda: FakeMinioClient())

    response = await common.get_file(
        path=path,
        request=_build_request({"authorization": "Bearer header-token"}),
        db=object(),
    )

    disposition = response.headers["content-disposition"]
    assert disposition.startswith('inline; filename="fixed-id_.pdf";')
    assert "filename*=UTF-8''fixed-id_%E4%B8%AD%E6%96%87" in disposition
    disposition.encode("latin-1")


@pytest.mark.asyncio
async def test_file_endpoint_rejects_query_token_even_with_valid_header(monkeypatch):
    async def fake_get_user_from_token(token, db):
        return SimpleNamespace(username="tester", is_active=True)

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)

    with pytest.raises(common.ValidationError) as exc:
        await common.get_file(
            path="contracts/2026/04/demo.pdf",
            token="query-token",
            request=_build_request({"authorization": "Bearer header-token"}),
            db=object(),
        )

    assert exc.value.message == "不允许使用查询参数令牌"


@pytest.mark.asyncio
async def test_file_endpoint_rejects_cookie_only_auth(monkeypatch):
    async def fake_get_user_from_token(token, db):
        return SimpleNamespace(username="tester", is_active=True)

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)

    with pytest.raises(common.AuthenticationError) as exc:
        await common.get_file(
            path="contracts/2026/04/demo.pdf",
            request=_build_request({"cookie": "lh_access_token=cookie-token"}),
            db=object(),
        )

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_local_file_fallback_rejects_symlink_escape(monkeypatch, tmp_path):
    original_upload_dir = settings.UPLOAD_DIR
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    contracts_dir = uploads_dir / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    outside_secret = tmp_path / "outside-secret.txt"
    outside_secret.write_text("secret")
    symlink_path = contracts_dir / "jump.txt"
    symlink_path.symlink_to(outside_secret)

    async def fake_get_user_from_token(token, db):
        return SimpleNamespace(username="tester", is_active=True)

    class MissingMinioClient:
        def stat_object(self, bucket, path):
            raise RuntimeError("not found")

    async def fake_user_can_access_file_path(path, db, current_user):
        return True

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)
    monkeypatch.setattr(common, "user_can_access_file_path", fake_user_can_access_file_path)
    monkeypatch.setattr(common, "get_minio_client", lambda: MissingMinioClient())
    settings.UPLOAD_DIR = str(uploads_dir)

    try:
        with pytest.raises(common.ValidationError) as exc:
            await common.get_file(
                path="contracts/jump.txt",
                request=_build_request({"authorization": "Bearer token-123"}),
                db=object(),
            )
    finally:
        settings.UPLOAD_DIR = original_upload_dir

    assert exc.value.message == "非法的文件路径"


@pytest.mark.asyncio
async def test_file_endpoint_rejects_authenticated_user_without_resource_access(monkeypatch):
    async def fake_get_user_from_token(token, db):
        return SimpleNamespace(id=2002, username="outsider", is_active=True)

    async def fake_user_can_access_file_path(path, db, current_user):
        return False

    monkeypatch.setattr(common, "get_user_from_token", fake_get_user_from_token)
    monkeypatch.setattr(common, "user_can_access_file_path", fake_user_can_access_file_path)

    with pytest.raises(common.PermissionDeniedError) as exc:
        await common.get_file(
            path="contracts/2026/04/private.pdf",
            request=_build_request({"authorization": "Bearer token-123"}),
            db=object(),
        )

    assert exc.value.message == "无权访问该文件"


@pytest.mark.asyncio
async def test_uploads_static_mount_is_removed():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/uploads/system/site_logo.png")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_public_logo_endpoint_serves_only_current_logo(monkeypatch, tmp_path):
    original_upload_dir = settings.UPLOAD_DIR
    system_dir = tmp_path / "system"
    system_dir.mkdir(parents=True, exist_ok=True)
    png_logo = system_dir / "site_logo.png"
    jpg_logo = system_dir / "site_logo.jpg"
    png_logo.write_bytes(b"older-logo")
    jpg_logo.write_bytes(b"newer-logo")
    old_ns = 1_710_000_000_000_000_000
    new_ns = old_ns + 10_000
    os.utime(png_logo, ns=(old_ns, old_ns))
    os.utime(jpg_logo, ns=(new_ns, new_ns))
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    try:
        response = await system_router.get_logo_file()
    finally:
        monkeypatch.setattr(settings, "UPLOAD_DIR", original_upload_dir)

    assert isinstance(response, FileResponse)
    assert response.status_code == 200
    assert response.path == str(jpg_logo)
    assert response.headers["cache-control"] == "public, max-age=300"


@pytest.mark.asyncio
async def test_public_logo_metadata_endpoint_returns_new_logo_path(monkeypatch, tmp_path):
    original_upload_dir = settings.UPLOAD_DIR
    system_dir = tmp_path / "system"
    system_dir.mkdir(parents=True, exist_ok=True)
    (system_dir / "site_logo.png").write_bytes(b"logo-bytes")
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/system/logo")
    finally:
        monkeypatch.setattr(settings, "UPLOAD_DIR", original_upload_dir)

    assert response.status_code == 200
    assert re.match(r"^/api/v1/system/logo/file\?v=\d+$", response.json()["path"])


@pytest.mark.asyncio
async def test_system_config_normalizes_logo_path_and_ignores_legacy_uploads_value(monkeypatch, tmp_path):
    class FakeScalarResult:
        def __init__(self, rows):
            self._rows = rows

        def all(self):
            return self._rows

    class FakeResult:
        def __init__(self, rows):
            self._rows = rows

        def scalars(self):
            return FakeScalarResult(self._rows)

    class FakeDBSession:
        async def execute(self, _statement):
            return FakeResult([
                SystemConfig(key="system_name", value="新系统名"),
                SystemConfig(key="system_logo", value="/uploads/system/site_logo.png"),
            ])

    async def override_get_db():
        yield FakeDBSession()

    original_upload_dir = settings.UPLOAD_DIR
    system_dir = tmp_path / "system"
    system_dir.mkdir(parents=True, exist_ok=True)
    (system_dir / "site_logo.png").write_bytes(b"logo-bytes")

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/system/config")
    finally:
        app.dependency_overrides.pop(get_db, None)
        monkeypatch.setattr(settings, "UPLOAD_DIR", original_upload_dir)

    payload = response.json()
    assert response.status_code == 200
    assert payload["system_name"] == "新系统名"
    assert re.match(r"^/api/v1/system/logo/file\?v=\d+$", payload["system_logo"])
