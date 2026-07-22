import asyncio
from pathlib import Path

from app.routers import health as health_router


REPO_ROOT = Path(__file__).resolve().parents[2]


def _completed(value):
    return asyncio.sleep(0, result=value)


def test_health_detailed_returns_503_when_any_dependency_is_unhealthy(monkeypatch):
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
    monkeypatch.setattr(
        health_router,
        "check_finance_import_jobs",
        lambda _db: _completed({"status": "healthy", "failed_jobs": 0, "stale_leases": 0}),
    )

    response = asyncio.run(health_router.health_check_detailed(db=object()))

    assert response.status_code == 503
    assert response.body
    assert b'"status":"unhealthy"' in response.body


def test_check_minio_uses_factory_client(monkeypatch):
    class DummyClient:
        def list_buckets(self):
            return ["contracts", "archive"]

    monkeypatch.setattr(
        "app.core.minio.get_minio_client",
        lambda: DummyClient(),
    )

    result = asyncio.run(health_router.check_minio())

    assert result == {"status": "healthy", "buckets": 2}


def test_health_ready_returns_503_when_database_is_unhealthy(monkeypatch):
    monkeypatch.setattr(
        health_router,
        "check_database",
        lambda _db: _completed({"status": "unhealthy"}),
    )
    monkeypatch.setattr(
        health_router,
        "check_minio",
        lambda: _completed({"status": "healthy"}),
    )

    response = asyncio.run(health_router.readiness_check(db=object()))

    assert response.status_code == 503
    import json

    payload = json.loads(response.body)
    assert payload["status"] == "not_ready"
    assert payload["checks"]["database"]["status"] == "unhealthy"
    assert payload["checks"]["minio"]["status"] == "healthy"


def test_health_ready_returns_503_when_minio_is_unhealthy(monkeypatch):
    monkeypatch.setattr(
        health_router,
        "check_database",
        lambda _db: _completed({"status": "healthy"}),
    )
    monkeypatch.setattr(
        health_router,
        "check_minio",
        lambda: _completed({"status": "unhealthy"}),
    )

    response = asyncio.run(health_router.readiness_check(db=object()))

    assert response.status_code == 503
    import json

    payload = json.loads(response.body)
    assert payload["status"] == "not_ready"
    assert payload["checks"]["database"]["status"] == "healthy"
    assert payload["checks"]["minio"]["status"] == "unhealthy"


def test_health_ready_returns_ready_when_database_and_minio_are_healthy(monkeypatch):
    monkeypatch.setattr(
        health_router,
        "check_database",
        lambda _db: _completed({"status": "healthy"}),
    )
    monkeypatch.setattr(
        health_router,
        "check_minio",
        lambda: _completed({"status": "healthy"}),
    )

    response = asyncio.run(health_router.readiness_check(db=object()))

    assert response == {"status": "ready"}


def test_production_healthchecks_use_readiness_endpoint():
    compose_files = [
        "docker-compose.production.yml",
        "docker-compose.prod.yml",
        "docker-compose.prod.balanced.yml",
        "docker-compose.prod.lowmem.yml",
        "docker-compose.pve-prod.yml",
    ]
    backend_dockerfile_content = (
        REPO_ROOT / "backend" / "Dockerfile.production"
    ).read_text(encoding="utf-8")
    nginx_content = (REPO_ROOT / "nginx" / "nginx.conf").read_text(encoding="utf-8")

    for compose_file in compose_files:
        compose_content = (REPO_ROOT / compose_file).read_text(encoding="utf-8")
        assert "/health/ready" in compose_content
        assert "http://localhost:8000/health\"" not in compose_content
        assert "http://localhost/health\"" not in compose_content

    assert "http://localhost:8000/health/ready" in backend_dockerfile_content
    assert "proxy_pass http://backend:8000/health/ready;" in nginx_content


def test_frontend_standalone_nginx_does_not_expose_uploads_alias():
    content = (REPO_ROOT / "frontend" / "nginx.conf").read_text(encoding="utf-8")

    assert "alias /usr/share/nginx/html/uploads/" not in content
