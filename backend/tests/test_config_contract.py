import os

from app.config import Settings


def _base_env(tmp_path):
    return {
        "DEBUG": True,
        "DATABASE_URL": "postgresql+asyncpg://test_user:test-db-password@localhost:5432/test_db",
        "SECRET_KEY": "test_secret_key_for_release_contracts",
        "UPLOAD_DIR": str(tmp_path / "uploads"),
        "BACKUP_TMP_DIR": str(tmp_path / "backup_tmp"),
        "MINIO_ENDPOINT": "minio:9000",
        "MINIO_ACCESS_KEY": "test-minio-access",
        "MINIO_SECRET_KEY": "test-minio-secret",
    }


def test_minio_bucket_contracts_prefers_current_env_name(monkeypatch, tmp_path):
    monkeypatch.setattr(os, "environ", _base_env(tmp_path) | {
        "MINIO_BUCKET_CONTRACTS": "current-bucket",
        "MINIO_BUCKET_ACTIVE": "legacy-bucket",
    })

    settings = Settings()

    assert settings.MINIO_BUCKET_CONTRACTS == "current-bucket"


def test_minio_bucket_contracts_accepts_legacy_env_name(monkeypatch, tmp_path):
    monkeypatch.setattr(os, "environ", _base_env(tmp_path) | {
        "MINIO_BUCKET_ACTIVE": "legacy-bucket",
    })

    settings = Settings()

    assert settings.MINIO_BUCKET_CONTRACTS == "legacy-bucket"
