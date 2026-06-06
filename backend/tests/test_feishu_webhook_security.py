"""
Feishu webhook verification regressions.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.routers import feishu


@pytest.mark.asyncio
async def test_feishu_webhook_rejects_unsigned_event_callback(
    client: AsyncClient,
    monkeypatch,
):
    monkeypatch.setattr(feishu, "FEISHU_WEBHOOK_VERIFICATION_TOKEN", "expected-token")

    response = await client.post(
        "/api/feishu/webhook",
        json={
            "header": {"event_type": "approval.instance.status_changed"},
            "event": {"instance_code": "fake", "status": "APPROVED"},
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_feishu_webhook_accepts_signed_event_callback(
    client: AsyncClient,
    monkeypatch,
):
    monkeypatch.setattr(feishu, "FEISHU_WEBHOOK_VERIFICATION_TOKEN", "expected-token")

    response = await client.post(
        "/api/feishu/webhook",
        json={
            "token": "expected-token",
            "header": {"event_type": "approval.instance.status_changed"},
            "event": {"instance_code": "fake", "status": "PENDING"},
        },
    )

    assert response.status_code == 200
    assert response.json()["msg"] == "success"


@pytest.mark.asyncio
async def test_feishu_webhook_fails_closed_when_verification_token_is_missing(
    client: AsyncClient,
    monkeypatch,
):
    monkeypatch.setattr(feishu, "FEISHU_WEBHOOK_VERIFICATION_TOKEN", "")
    monkeypatch.setattr(feishu.settings, "DEBUG", False)

    response = await client.post(
        "/api/feishu/webhook",
        json={
            "header": {"event_type": "approval.instance.status_changed"},
            "event": {"instance_code": "fake", "status": "APPROVED"},
        },
    )

    assert response.status_code == 503
