"""
Permission hardening regressions for route parity.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upstream_import_requires_same_permission_as_manual_create(
    client: AsyncClient,
    user_token: str,
):
    response = await client.post(
        "/api/v1/contracts/upstream/import/excel",
        headers={"Authorization": f"Bearer {user_token}"},
        files={
            "file": (
                "demo.xlsx",
                b"fake",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_period_trend_requires_view_dashboard(
    client: AsyncClient,
    user_token: str,
):
    response = await client.get(
        "/api/v1/dashboard/stats/trend/period",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403
