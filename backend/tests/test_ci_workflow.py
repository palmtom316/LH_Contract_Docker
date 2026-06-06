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


def test_ci_workflow_skips_docker_publish_when_registry_secrets_are_missing():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-cd.yml").read_text(encoding="utf-8")

    assert "DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}" in workflow
    assert "DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}" in workflow
    assert "if: ${{ env.DOCKER_USERNAME != '' && env.DOCKER_PASSWORD != '' }}" in workflow


def test_ci_workflow_skips_deploy_steps_when_server_secrets_are_missing():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-cd.yml").read_text(encoding="utf-8")

    assert "DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}" in workflow
    assert "DEPLOY_USER: ${{ secrets.DEPLOY_USER }}" in workflow
    assert "DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}" in workflow
    assert "DEPLOY_URL: ${{ secrets.DEPLOY_URL }}" in workflow
    assert "if: ${{ env.DEPLOY_HOST != '' && env.DEPLOY_USER != '' && env.DEPLOY_KEY != '' && env.DEPLOY_URL != '' }}" in workflow
