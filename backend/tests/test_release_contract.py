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


def test_main_does_not_run_schema_mutation_as_part_of_normal_boot_contract():
    content = (REPO_ROOT / "backend/app/main.py").read_text(encoding="utf-8")
    assert "run_startup_check" not in content


def test_database_init_contract_does_not_create_schema_objects():
    content = (REPO_ROOT / "backend/app/database.py").read_text(encoding="utf-8")
    assert "create_all" not in content


def test_deployment_checklist_references_existing_compose_services():
    content = (REPO_ROOT / "docs/release/deployment-checklist-hardening.md").read_text(encoding="utf-8")
    assert "frontend nginx" not in content
