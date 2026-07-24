from sqlalchemy import select

from app.core.secure_config import protect_config_secret, reveal_config_secret
from app.models.system import SystemConfig


async def test_mineru_test_reports_unsaved_config_and_keeps_disabled(
    client, admin_token, test_db
):
    response = await client.post(
        "/api/v1/system/config/mineru/test",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "ok": False,
        "result": "not_configured",
        "message": "请先保存 MinerU API 地址和 API Key",
    }
    enabled = await test_db.scalar(
        select(SystemConfig).where(SystemConfig.key == "mineru_enabled")
    )
    assert enabled.value == "false"


async def test_system_config_cannot_enable_mineru_without_connection_test(
    client, admin_token
):
    response = await client.post(
        "/api/v1/system/config",
        json={"mineru_enabled": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 422


async def test_system_config_saves_long_encrypted_mineru_key(
    client, admin_token, test_db, monkeypatch
):
    api_key = "mineru-" + "a" * 700
    monkeypatch.setattr(
        "app.routers.system.validate_external_api_url", lambda value: value
    )

    response = await client.post(
        "/api/v1/system/config",
        json={
            "mineru_api_url": "https://mineru.net/api/v4/extract/task",
            "mineru_api_key": api_key,
            "mineru_enabled": False,
            "mineru_timeout_seconds": 60,
            "company_bank_accounts": "7421610182600142192",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    stored_key = await test_db.scalar(
        select(SystemConfig.value).where(SystemConfig.key == "mineru_api_key")
    )
    assert len(stored_key) > 500
    assert reveal_config_secret(stored_key) == api_key


async def test_successful_mineru_test_enables_recognition(
    client, admin_token, test_db, monkeypatch
):
    test_db.add_all(
        [
            SystemConfig(key="mineru_api_url", value="https://mineru.example.test/api"),
            SystemConfig(
                key="mineru_api_key", value=protect_config_secret("test-token")
            ),
            SystemConfig(key="mineru_timeout_seconds", value="30"),
            SystemConfig(key="mineru_enabled", value="false"),
        ]
    )
    await test_db.commit()

    class FakeResponse:
        status_code = 422

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            assert kwargs["timeout"] == 30

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, url, headers):
            assert url == "https://mineru.example.test/api"
            assert headers["Authorization"] == "Bearer test-token"
            return FakeResponse()

    monkeypatch.setattr(
        "app.routers.system.create_pinned_http_transport", lambda _url: object()
    )
    monkeypatch.setattr("app.routers.system.httpx.AsyncClient", FakeAsyncClient)

    response = await client.post(
        "/api/v1/system/config/mineru/test",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["message"] == "连接成功，MinerU 识别已启用"
    enabled = await test_db.scalar(
        select(SystemConfig).where(SystemConfig.key == "mineru_enabled")
    )
    assert enabled.value == "true"
