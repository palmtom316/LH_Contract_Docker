"""
Auth hardening regression tests.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import PermissionDeniedError
from app.main import internal_server_error_handler
from app.routers.auth import register
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import UserCreate


@pytest.mark.asyncio
class TestRegistrationHardening:
    async def test_register_handler_rejects_public_registration_without_touching_db(self):
        with pytest.raises(PermissionDeniedError) as exc_info:
            await register(
                user_data=UserCreate(
                    username="blocked",
                    email="blocked@example.com",
                    password="ValidPass123",
                    full_name="Blocked User",
                    role="BIDDING",
                ),
                db=None,
            )

        assert exc_info.value.message == "公开注册已关闭"

    async def test_public_register_cannot_create_admin_role(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "evil",
                "email": "evil@example.com",
                "password": "ValidPass123",
                "full_name": "Evil User",
                "role": "ADMIN",
            },
        )

        assert response.status_code in (400, 403)
        payload = response.json()
        assert payload["message"] == "公开注册已关闭"


@pytest.mark.asyncio
class TestRefreshTokenHardening:
    async def test_old_refresh_token_is_revoked_after_rotation(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        test_user: User,
    ):
        login_response = await client.post(
            "/api/v1/auth/login/json",
            json={"username": "testuser", "password": "testpass123"},
        )
        assert login_response.status_code == 200
        original_refresh_token = login_response.json()["refresh_token"]

        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": original_refresh_token},
        )
        assert refresh_response.status_code == 200
        rotated_refresh_token = refresh_response.json()["refresh_token"]
        assert rotated_refresh_token != original_refresh_token

        retry_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": original_refresh_token},
        )
        assert retry_response.status_code == 401

        tokens = (
            await test_db.execute(
                select(RefreshToken).where(RefreshToken.user_id == test_user.id).order_by(RefreshToken.id)
            )
        ).scalars().all()

        assert len(tokens) == 2
        assert tokens[0].revoked is True
        assert tokens[1].revoked is False

    async def test_logout_revokes_all_refresh_tokens(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        test_user: User,
    ):
        first_login = await client.post(
            "/api/v1/auth/login/json",
            json={"username": "testuser", "password": "testpass123"},
        )
        second_login = await client.post(
            "/api/v1/auth/login/json",
            json={"username": "testuser", "password": "testpass123"},
        )
        assert first_login.status_code == 200
        assert second_login.status_code == 200

        access_token = second_login.json()["access_token"]
        logout_response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert logout_response.status_code == 200

        tokens = (
            await test_db.execute(select(RefreshToken).where(RefreshToken.user_id == test_user.id))
        ).scalars().all()

        assert len(tokens) == 2
        assert all(token.revoked is True for token in tokens)

    async def test_change_password_revokes_existing_refresh_tokens(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        test_user: User,
    ):
        login_response = await client.post(
            "/api/v1/auth/login/json",
            json={"username": "testuser", "password": "testpass123"},
        )
        assert login_response.status_code == 200
        payload = login_response.json()

        change_response = await client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {payload['access_token']}"},
            json={"old_password": "testpass123", "new_password": "ValidPass456"},
        )
        assert change_response.status_code == 200

        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": payload["refresh_token"]},
        )
        assert refresh_response.status_code == 401

        tokens = (
            await test_db.execute(select(RefreshToken).where(RefreshToken.user_id == test_user.id))
        ).scalars().all()

        assert tokens
        assert all(token.revoked is True for token in tokens)


@pytest.mark.asyncio
async def test_global_exception_handler_hides_internal_error_details():
    class Boom(Exception):
        pass

    response = await internal_server_error_handler(request=None, exc=Boom("db password leaked"))

    assert response.status_code == 500
    assert b"db password leaked" not in response.body
    assert b"Server Error" not in response.body
    assert b"9001" in response.body
