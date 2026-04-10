import os

import pytest

from app.config import Settings, settings


@pytest.mark.asyncio
async def test_database_backup_uses_non_public_temp_dir(client, admin_token, monkeypatch, tmp_path):
    import app.routers.system as system_router

    captured = {}
    upload_root = tmp_path / "uploads"
    backup_root = tmp_path / "backup_tmp"
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_root))
    monkeypatch.setattr(settings, "BACKUP_TMP_DIR", str(backup_root))

    def fake_run_db_dump(output_file: str):
        captured["output_file"] = output_file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "wb") as fh:
            fh.write(b"sql")

    monkeypatch.setattr(system_router, "run_db_dump", fake_run_db_dump)

    response = await client.get(
        "/api/v1/system/backup/db",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert captured["output_file"].startswith(str(backup_root))
    assert not captured["output_file"].startswith(str(upload_root))


def test_backup_tmp_dir_cannot_be_nested_under_upload_dir(tmp_path):
    upload_root = tmp_path / "uploads"
    backup_root = upload_root / "backup_tmp"

    with pytest.raises(ValueError, match="BACKUP_TMP_DIR"):
        Settings(
            DEBUG=True,
            SECRET_KEY="test-secret",
            UPLOAD_DIR=str(upload_root),
            BACKUP_TMP_DIR=str(backup_root),
        )


@pytest.mark.asyncio
async def test_full_backup_does_not_create_upload_temp_subdir(client, admin_token, monkeypatch, tmp_path):
    import app.routers.system as system_router

    captured = {}
    upload_root = tmp_path / "uploads"
    backup_root = tmp_path / "backup_tmp"
    expected_temp_dir = backup_root / "full_backup_test"
    upload_root.mkdir(parents=True, exist_ok=True)
    (upload_root / "contracts").mkdir(parents=True, exist_ok=True)
    (upload_root / "contracts" / "demo.txt").write_text("demo", encoding="utf-8")

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_root))
    monkeypatch.setattr(settings, "BACKUP_TMP_DIR", str(backup_root))

    def fake_run_db_dump(output_file: str):
        captured["db_dump_output"] = output_file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "wb") as fh:
            fh.write(b"sql")

    def fake_mkdtemp(prefix: str, dir: str):
        captured["temp_dir"] = str(expected_temp_dir)
        os.makedirs(expected_temp_dir, exist_ok=True)
        return str(expected_temp_dir)

    def fake_make_archive(base_name: str, format: str, root_dir: str):
        captured["base_name"] = base_name
        captured["root_dir"] = root_dir
        archive_path = f"{base_name}.zip"
        with open(archive_path, "wb") as fh:
            fh.write(b"zip")
        return archive_path

    monkeypatch.setattr(system_router, "run_db_dump", fake_run_db_dump)
    monkeypatch.setattr(system_router.tempfile, "mkdtemp", fake_mkdtemp)
    monkeypatch.setattr(system_router.shutil, "make_archive", fake_make_archive)

    await client.get("/api/v1/system/backup/full", headers={"Authorization": f"Bearer {admin_token}"})
    assert captured["temp_dir"].startswith(str(backup_root))
    assert captured["db_dump_output"].startswith(str(expected_temp_dir))
    assert captured["base_name"].startswith(str(backup_root))
    assert not os.path.exists(os.path.join(settings.UPLOAD_DIR, "temp"))
