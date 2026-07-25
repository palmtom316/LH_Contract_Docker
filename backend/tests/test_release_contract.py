"""
Release contract tests for production startup and deployment docs.
"""

from __future__ import annotations

from pathlib import Path

from app.main import app


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_main_mounts_detailed_health_route():
    routes = {route.path for route in app.routes}
    assert "/health/detailed" in routes


def test_main_keeps_api_docs_closed_by_default():
    routes = {route.path for route in app.routes}
    assert "/docs" not in routes
    assert "/openapi.json" not in routes


def test_main_does_not_run_schema_mutation_as_part_of_normal_boot_contract():
    content = (REPO_ROOT / "backend/app/main.py").read_text(encoding="utf-8")
    assert "run_startup_check" not in content


def test_database_init_contract_does_not_create_schema_objects():
    content = (REPO_ROOT / "backend/app/database.py").read_text(encoding="utf-8")
    assert "create_all" not in content


def test_deployment_checklist_references_existing_compose_services():
    content = (REPO_ROOT / "DEPLOYMENT.md").read_text(encoding="utf-8")
    legacy_admin_phrase = "默认" + "管理员" + "账号"
    legacy_admin_password = "admin" + "123"
    assert legacy_admin_phrase not in content
    assert legacy_admin_password not in content


def test_production_images_and_startup_match_release_18_contract():
    backend_dockerfile = (REPO_ROOT / "backend" / "Dockerfile.production").read_text(
        encoding="utf-8"
    )
    frontend_dockerfile = (REPO_ROOT / "frontend" / "Dockerfile.production").read_text(
        encoding="utf-8"
    )
    frontend_package = (REPO_ROOT / "frontend" / "package.json").read_text(
        encoding="utf-8"
    )

    assert 'LABEL version="1.9.0"' in backend_dockerfile
    assert 'LABEL version="1.9.0"' in frontend_dockerfile
    assert '"version": "1.9.0"' in frontend_package
    assert "alembic upgrade head && uvicorn" in backend_dockerfile


def test_pve_compose_defaults_to_release_191_ghcr_images():
    content = (REPO_ROOT / "docker-compose.pve-prod.yml").read_text(encoding="utf-8")

    assert "ghcr.io/palmtom316/lh-contract-backend:1.9.1" in content
    assert "ghcr.io/palmtom316/lh-contract-frontend:1.9.1" in content
    assert "BACKEND_IMAGE" in content
    assert "FRONTEND_IMAGE" in content


def test_pve_minio_ports_are_loopback_only():
    content = (REPO_ROOT / "docker-compose.pve-prod.yml").read_text(encoding="utf-8")

    assert '"127.0.0.1:9000:9000"' in content
    assert '"127.0.0.1:9001:9001"' in content


def test_release_18_preflight_checks_schema_and_required_environment():
    content = (REPO_ROOT / "scripts/preflight_1.8.sh").read_text(encoding="utf-8")

    assert "20260527_add_zero_hour_tax_description" in content
    assert "version_width" in content
    assert "COMPANY_TAX_NO" in content


def test_release_19_upgrade_is_guarded_by_backup_and_schema_preflights():
    preflight = (REPO_ROOT / "scripts/preflight_1.9.sh").read_text(encoding="utf-8")
    upgrade = (REPO_ROOT / "scripts/upgrade_to_v1.9.sh").read_text(encoding="utf-8")
    assert "20260527_add_zero_hour_tax_description" in preflight
    assert "20260717_invoice_project_matching" in preflight
    assert "20260722_durable_import_jobs" in preflight
    assert "20260723_zero_hour_finance_fields" in preflight
    assert "20260723_expand_system_config" in preflight
    assert "20260725_remove_bank_receipts" in preflight
    assert "./scripts/preflight_1.9.sh before" in upgrade
    assert "./scripts/backup.sh" in upgrade
    assert "alembic upgrade head" in upgrade
    assert "./scripts/preflight_1.9.sh after" in upgrade


def test_upgrade_backup_requires_minio_object_backup():
    content = (REPO_ROOT / "scripts/backup.sh").read_text(encoding="utf-8")

    assert "无法创建升级所需的 MinIO 对象备份" in content
    assert "CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))" in content


def test_production_compose_variants_configure_minio_for_backend():
    compose_files = [
        "docker-compose.production.yml",
        "docker-compose.prod.yml",
        "docker-compose.prod.balanced.yml",
        "docker-compose.prod.lowmem.yml",
        "docker-compose.pve-prod.yml",
    ]

    for compose_file in compose_files:
        content = (REPO_ROOT / compose_file).read_text(encoding="utf-8")
        assert "\n  minio:" in content
        assert "MINIO_ENDPOINT: minio:9000" in content
        assert "MINIO_ACCESS_KEY:" in content
        assert "MINIO_SECRET_KEY:" in content
        assert "MINIO_BUCKET_CONTRACTS:" in content
        assert "minio_data:" in content


def test_compose_files_use_current_contract_bucket_env_name():
    compose_files = [
        "docker-compose.yml",
        "docker-compose.production.yml",
        "docker-compose.prod.yml",
        "docker-compose.prod.balanced.yml",
        "docker-compose.prod.lowmem.yml",
        "docker-compose.pve-prod.yml",
    ]

    for compose_file in compose_files:
        content = (REPO_ROOT / compose_file).read_text(encoding="utf-8")
        assert "MINIO_BUCKET_CONTRACTS" in content
        assert "MINIO_BUCKET_ACTIVE" not in content
