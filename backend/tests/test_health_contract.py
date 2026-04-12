import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.routers import health as health_router


REPO_ROOT = Path(__file__).resolve().parents[2]


def _completed(value):
    return asyncio.sleep(0, result=value)


def test_health_detailed_returns_503_when_any_dependency_is_unhealthy(monkeypatch):
    async def override_get_db():
        yield object()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(
        health_router,
        "check_database",
        lambda _db: _completed({"status": "unhealthy"}),
    )
    monkeypatch.setattr(
        health_router,
        "check_redis",
        lambda: _completed({"status": "healthy"}),
    )
    monkeypatch.setattr(
        health_router,
        "check_minio",
        lambda: _completed({"status": "healthy"}),
    )

    try:
        client = TestClient(app)
        response = client.get("/health/detailed")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"


def test_health_ready_returns_503_when_database_is_unhealthy(monkeypatch):
    async def override_get_db():
        yield object()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(
        health_router,
        "check_database",
        lambda _db: _completed({"status": "unhealthy"}),
    )

    try:
        client = TestClient(app)
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_production_healthchecks_use_readiness_endpoint():
    compose_content = (REPO_ROOT / "docker-compose.production.yml").read_text(encoding="utf-8")
    backend_dockerfile_content = (
        REPO_ROOT / "backend" / "Dockerfile.production"
    ).read_text(encoding="utf-8")
    nginx_content = (REPO_ROOT / "nginx" / "nginx.conf").read_text(encoding="utf-8")

    assert "http://localhost:8000/health/ready" in compose_content
    assert "http://localhost/health/ready" in compose_content
    assert "http://localhost:8000/health/ready" in backend_dockerfile_content
    assert "proxy_pass http://backend:8000/health/ready;" in nginx_content


def test_frontend_standalone_nginx_does_not_expose_uploads_alias():
    content = (REPO_ROOT / "frontend" / "nginx.conf").read_text(encoding="utf-8")

    assert "alias /usr/share/nginx/html/uploads/" not in content
