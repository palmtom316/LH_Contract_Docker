from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ci_workflow_tracks_main_and_16_branch_pushes():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-cd.yml").read_text(encoding="utf-8")

    assert "branches: [ main, develop, 1.6 ]" in workflow


def test_ci_workflow_uses_supported_node_version_for_vite_7():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-cd.yml").read_text(encoding="utf-8")

    assert "node-version: '20'" in workflow


def test_ci_workflow_provides_test_database_url_for_backend_suite():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-cd.yml").read_text(encoding="utf-8")

    assert "TEST_DATABASE_URL: postgresql+asyncpg://test_user:test_password@localhost:5432/test_db" in workflow


def test_ci_workflow_does_not_swallow_frontend_test_failures():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-cd.yml").read_text(encoding="utf-8")

    assert "npm run test || true" not in workflow
    assert "npm run test" in workflow
