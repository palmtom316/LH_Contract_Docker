"""
Refresh Token Tests
Tests for the new refresh token mechanism
"""
import pytest
from datetime import timedelta
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.auth import (
    create_access_token,
    create_refresh_token_sync,
    verify_refresh_token
)


class TestRefreshTokenCreation:
    """Test refresh token creation"""
    
    def test_create_refresh_token(self):
        """Test creating a refresh token"""
        token_data = {
            "sub": "1",
            "username": "testuser",
            "role": "VIEWER"
        }
        token, _ = create_refresh_token_sync(data=token_data, jti="test-jti-1")
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically long
    
    def test_refresh_token_has_type(self):
        """Test that refresh token has type 'refresh'"""
        token_data = {"sub": "1", "username": "testuser"}
        token, _ = create_refresh_token_sync(data=token_data, jti="test-jti-2")
        
        # Verify the token
        payload = verify_refresh_token(token)
        
        assert payload is not None
        assert payload.get("type") == "refresh"
    
    def test_access_token_has_type(self):
        """Test that access token has type 'access'"""
        token_data = {"sub": "1", "username": "testuser"}
        token = create_access_token(data=token_data)
        
        # Access token should NOT pass refresh token verification
        payload = verify_refresh_token(token)
        assert payload is None  # Should fail because type is 'access'


class TestRefreshTokenVerification:
    """Test refresh token verification"""
    
    def test_verify_valid_refresh_token(self):
        """Test verifying a valid refresh token"""
        token_data = {
            "sub": "1",
            "username": "testuser",
            "role": "VIEWER"
        }
        token, _ = create_refresh_token_sync(data=token_data, jti="test-jti-3")
        
        payload = verify_refresh_token(token)
        
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["username"] == "testuser"
        assert payload["type"] == "refresh"
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token"""
        payload = verify_refresh_token("invalid.token.here")
        
        assert payload is None
    
    def test_verify_expired_token(self):
        """Test verifying an expired refresh token"""
        token_data = {"sub": "1", "username": "testuser"}
        # Create token with negative expiration (already expired)
        token, _ = create_refresh_token_sync(
            data=token_data,
            jti="test-jti-4",
            expires_delta=timedelta(seconds=-1)
        )
        
        payload = verify_refresh_token(token)
        
        assert payload is None  # Should be expired


@pytest.mark.asyncio
class TestRefreshTokenEndpoint:
    """Test the /auth/refresh endpoint"""
    
    async def test_refresh_token_success(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test successful token refresh"""
        # First, login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login/json",
            json={"username": "testuser", "password": "testpass123"}
        )
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        refresh_token = login_data.get("refresh_token")
        original_access_token = login_data.get("access_token")
        
        assert refresh_token is not None
        
        # Now use the refresh token to get a new access token
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        
        assert "access_token" in refresh_data
        assert "refresh_token" in refresh_data
        assert refresh_data["token_type"] == "bearer"
        assert refresh_data["user"]["username"] == "testuser"
        
        # The new access token should be different (has new expiration)
        # Note: Due to timing, they might be the same, so we just check it exists
        assert refresh_data["access_token"] is not None
        assert refresh_data["refresh_token"] != refresh_token

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token"""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        
        assert response.status_code == 401
    
    async def test_login_returns_refresh_token(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test that login returns both access and refresh tokens"""
        response = await client.post(
            "/api/v1/auth/login/json",
            json={"username": "testuser", "password": "testpass123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
        
        # expires_in should be in seconds (2 hours = 7200 seconds)
        assert data["expires_in"] == 7200  # 2 hours * 60 minutes * 60 seconds

    async def test_refresh_token_rotation_revokes_old_token_record(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        test_user: User
    ):
        login_response = await client.post(
            "/api/v1/auth/login/json",
            json={"username": "testuser", "password": "testpass123"}
        )
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]

        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200

        token_rows = (
            await test_db.execute(
                select(RefreshToken).where(RefreshToken.user_id == test_user.id).order_by(RefreshToken.id)
            )
        ).scalars().all()
        assert len(token_rows) == 2
        assert token_rows[0].revoked is True
        assert token_rows[1].revoked is False
