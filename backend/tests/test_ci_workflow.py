from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ci_workflow_tracks_release_19_branch_pushes_and_prs():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-cd.yml").read_text(encoding="utf-8")

    assert "branches: [ main, develop, 1.6, release/1.8, release/1.9 ]" in workflow


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


def test_ci_workflow_does_not_swallow_frontend_lint_failures():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-cd.yml").read_text(encoding="utf-8")

    assert "npm run lint || true" not in workflow
    assert "npm run lint" in workflow


def test_ci_workflow_builds_release_19_branch_and_checks_readiness():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-cd.yml").read_text(encoding="utf-8")

    assert "refs/heads/release/1.9" in workflow
    assert "IMAGE_VERSION: 1.9.0" in workflow
    assert "${{ secrets.DEPLOY_URL }}/health/ready" in workflow


def test_ci_workflow_publishes_release_images_to_ghcr_without_dockerhub_secrets():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-cd.yml").read_text(encoding="utf-8")

    assert "permissions:" in workflow
    assert "packages: write" in workflow
    assert "registry: ${{ env.REGISTRY }}" in workflow
    assert "password: ${{ secrets.GITHUB_TOKEN }}" in workflow
    assert "ghcr.io" in workflow
    assert "lh-contract-backend:${{ env.IMAGE_VERSION }}" in workflow
    assert "lh-contract-frontend:${{ env.IMAGE_VERSION }}" in workflow
    assert "DOCKER_USERNAME" not in workflow
    assert "DOCKER_PASSWORD" not in workflow


def test_ci_workflow_skips_deploy_steps_when_server_secrets_are_missing():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-cd.yml").read_text(encoding="utf-8")

    assert "DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}" in workflow
    assert "DEPLOY_USER: ${{ secrets.DEPLOY_USER }}" in workflow
    assert "DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}" in workflow
    assert "DEPLOY_URL: ${{ secrets.DEPLOY_URL }}" in workflow
    assert "if: ${{ env.DEPLOY_HOST != '' && env.DEPLOY_USER != '' && env.DEPLOY_KEY != '' && env.DEPLOY_URL != '' }}" in workflow
